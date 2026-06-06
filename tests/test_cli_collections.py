from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from recall.presentation.cli import app
from recall.presentation.exit_codes import ExitCode

runner = CliRunner()


def _write_collection_repo(tmp_path: Path) -> None:
    (tmp_path / "recall.config.json").write_text(
        json.dumps(
            {
                "version": 2,
                "collections": {
                    "chess": {
                        "include": ["chess/**/*.md"],
                        "exclude": ["**/templates/**"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "chess" / "openings").mkdir(parents=True)
    (tmp_path / "chess" / "templates").mkdir(parents=True)
    (tmp_path / "chess" / "game1.md").write_text(
        "# Game 1\n\n"
        "## White plan? #flashcard\n"
        "<!-- recall:id=chess-plan -->\n\n"
        "Attack the center.\n",
        encoding="utf-8",
    )
    (tmp_path / "chess" / "openings" / "game2.md").write_text(
        "# Game 2\n\n"
        "## Best move? #flashcard\n"
        "<!-- recall:id=chess-move -->\n\n"
        "Play Nf3.\n",
        encoding="utf-8",
    )
    (tmp_path / "chess" / "templates" / "ignored.md").write_text(
        "# Template\n\n"
        "## Ignored? #flashcard\n"
        "<!-- recall:id=ignored-card -->\n\n"
        "Ignore me.\n",
        encoding="utf-8",
    )


def test_collection_list_and_show_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_collection_repo(tmp_path)

    list_result = runner.invoke(app, ["collection", "list", "--format", "json"])
    show_result = runner.invoke(
        app, ["collection", "show", "chess", "--format", "json"]
    )

    assert list_result.exit_code == ExitCode.OK
    assert json.loads(list_result.stdout) == {
        "collections": [
            {
                "exclude": ["**/templates/**"],
                "file_count": 2,
                "include": ["chess/**/*.md"],
                "name": "chess",
            }
        ]
    }
    assert show_result.exit_code == ExitCode.OK
    assert json.loads(show_result.stdout) == {
        "collection": {
            "exclude": ["**/templates/**"],
            "files": ["chess/game1.md", "chess/openings/game2.md"],
            "include": ["chess/**/*.md"],
            "name": "chess",
        }
    }


def test_collection_commands_end_to_end_and_ambiguous_scope_errors(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_collection_repo(tmp_path)

    validate_result = runner.invoke(
        app, ["validate", "--collection", "chess", "--format", "json"]
    )
    scan_result = runner.invoke(
        app, ["scan", "--collection", "chess", "--format", "json"]
    )
    next_result = runner.invoke(
        app,
        [
            "next",
            "--collection",
            "chess",
            "--show-answer",
            "--limit",
            "5",
            "--format",
            "json",
        ],
    )

    assert validate_result.exit_code == ExitCode.OK
    validate_payload = json.loads(validate_result.stdout)
    assert validate_payload["collection"]["name"] == "chess"
    assert [item["path"] for item in validate_payload["collection"]["files"]] == [
        str(tmp_path / "chess" / "game1.md"),
        str(tmp_path / "chess" / "openings" / "game2.md"),
    ]
    assert scan_result.exit_code == ExitCode.OK
    assert json.loads(scan_result.stdout) == {
        "cards_due": 2,
        "cards_total": 2,
        "collection": "chess",
        "decks_scanned": 2,
        "errors": [],
    }

    assert next_result.exit_code == ExitCode.OK
    next_payload = json.loads(next_result.stdout)
    assert next_payload["collection"] == "chess"
    assert [card["card_id"] for card in next_payload["cards"]] == [
        "chess-plan",
        "chess-move",
    ]
    assert next_payload["cards"][0]["source"] == {"line": 3, "path": "chess/game1.md"}
    assert next_payload["cards"][1]["source"] == {
        "line": 3,
        "path": "chess/openings/game2.md",
    }

    review_result = runner.invoke(
        app,
        [
            "review",
            "--collection",
            "chess",
            "--card-id",
            "chess-plan",
            "--rating",
            "good",
            "--format",
            "json",
        ],
    )
    assert review_result.exit_code == ExitCode.OK
    review_payload = json.loads(review_result.stdout)
    assert review_payload["collection"] == "chess"
    assert review_payload["card_id"] == "chess-plan"
    assert review_payload["new_state"]["interval"] == 1

    sidecar_payload = json.loads(
        (tmp_path / ".recall" / "collections" / "chess.flashcards.json").read_text(
            encoding="utf-8"
        )
    )
    assert sidecar_payload["collection"] == "chess"
    assert (
        sidecar_payload["cards"]["chess-plan"]["state"] == review_payload["new_state"]
    )
    assert sidecar_payload["cards"]["chess-plan"]["source_path"] == "chess/game1.md"

    stats_result = runner.invoke(
        app, ["stats", "--collection", "chess", "--format", "json"]
    )
    assert stats_result.exit_code == ExitCode.OK
    assert json.loads(stats_result.stdout) == {
        "cards_total": 2,
        "collection": "chess",
        "due_today": 1,
        "mature": 0,
        "new": 1,
        "young": 1,
    }

    ambiguous = runner.invoke(app, ["scan", "--deck", "x", "--collection", "chess"])
    assert ambiguous.exit_code == ExitCode.INVALID_ARGUMENTS
    assert (
        "exactly one" in ambiguous.stderr.lower()
        or "cannot use both" in ambiguous.stderr.lower()
    )

    missing_scope = runner.invoke(app, ["next", "--format", "json"])
    assert missing_scope.exit_code == ExitCode.INVALID_ARGUMENTS
    assert "exactly one" in missing_scope.stderr.lower()


def test_validate_collection_rejects_duplicate_ids_across_files(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _write_collection_repo(tmp_path)
    (tmp_path / "chess" / "openings" / "game2.md").write_text(
        "# Game 2\n\n"
        "## Duplicate? #flashcard\n"
        "<!-- recall:id=chess-plan -->\n\n"
        "Still duplicate.\n",
        encoding="utf-8",
    )
    (tmp_path / ".recall" / "collections").mkdir(parents=True)
    (tmp_path / ".recall" / "collections" / "chess.flashcards.json").write_text(
        json.dumps(
            {
                "version": 1,
                "collection": "chess",
                "cards": {
                    "orphan-card": {
                        "source_path": "chess/missing.md",
                        "state": {
                            "due": "2026-06-05",
                            "ease": 2.5,
                            "interval": 0,
                            "reps": 0,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["validate", "--collection", "chess", "--format", "json"]
    )

    assert result.exit_code == ExitCode.INVALID_CARD_FORMAT
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["collection"]["name"] == "chess"
    issues = [
        issue for file in payload["collection"]["files"] for issue in file["issues"]
    ]
    assert any(issue["code"] == "duplicate_id" for issue in issues)
    warnings = [
        warning
        for file in payload["collection"]["files"]
        for warning in file["warnings"]
    ]
    assert warnings == ["sidecar contains orphaned card state: orphan-card"]
