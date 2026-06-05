from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from recall.cli import app
from recall.exit_codes import ExitCode

runner = CliRunner()


TAGGED_DECK = """# Architecture

## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt Commands und Queries.
"""


def test_validate_and_normalize_commands_are_available_and_fix_missing_ids(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    (decks_dir / "architecture.md").write_text(
        "## Was ist CQRS? #flashcard\n\nCQRS trennt Commands und Queries.\n",
        encoding="utf-8",
    )

    invalid = runner.invoke(app, ["validate", "--deck", "architecture"])
    assert invalid.exit_code == ExitCode.INVALID_CARD_FORMAT
    assert "missing_id" in invalid.stdout.lower() or "missing explicit recall:id" in invalid.stdout.lower()

    normalized = runner.invoke(app, ["normalize", "--deck", "architecture", "--write"])
    assert normalized.exit_code == ExitCode.OK
    assert "architecture-was-ist-cqrs" in (decks_dir / "architecture.md").read_text(encoding="utf-8")

    valid = runner.invoke(app, ["validate", "--deck", "architecture"])
    assert valid.exit_code == ExitCode.OK
    assert "valid" in valid.stdout.lower()


def test_scan_next_review_stats_work_end_to_end_via_cli_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    (decks_dir / "architecture.md").write_text(TAGGED_DECK, encoding="utf-8")

    scan_result = runner.invoke(app, ["scan", "--deck", "architecture", "--format", "json"])
    assert scan_result.exit_code == ExitCode.OK
    assert json.loads(scan_result.stdout) == {
        "cards_due": 1,
        "cards_total": 1,
        "decks_scanned": 1,
        "errors": [],
    }

    next_result = runner.invoke(app, ["next", "--deck", "architecture", "--show-answer", "--format", "json"])
    assert next_result.exit_code == ExitCode.OK
    next_payload = json.loads(next_result.stdout)
    assert next_payload["deck"] == "architecture"
    assert next_payload["cards"][0]["card_id"] == "architecture-cqrs"
    assert next_payload["cards"][0]["answer"] == "CQRS trennt Commands und Queries."

    review_result = runner.invoke(
        app,
        ["review", "--deck", "architecture", "--card-id", "architecture-cqrs", "--rating", "good", "--format", "json"],
    )
    assert review_result.exit_code == ExitCode.OK
    review_payload = json.loads(review_result.stdout)
    assert review_payload["new_state"]["ease"] == 2.36
    assert review_payload["new_state"]["interval"] == 1
    assert review_payload["new_state"]["reps"] == 1

    stats_result = runner.invoke(app, ["stats", "--deck", "architecture", "--format", "json"])
    assert stats_result.exit_code == ExitCode.OK
    assert json.loads(stats_result.stdout) == {
        "cards_total": 1,
        "deck": "architecture",
        "due_today": 0,
        "mature": 0,
        "new": 0,
        "young": 1,
    }


def test_next_returns_no_due_cards_exit_code_when_all_cards_are_in_future(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    (decks_dir / "architecture.md").write_text(TAGGED_DECK, encoding="utf-8")

    runner.invoke(app, ["scan", "--deck", "architecture"])
    runner.invoke(app, ["review", "--deck", "architecture", "--card-id", "architecture-cqrs", "--rating", "good"])

    result = runner.invoke(app, ["next", "--deck", "architecture", "--format", "json"])
    assert result.exit_code == ExitCode.NO_DUE_CARDS
