import json
from pathlib import Path

from recall.commands.normalize import normalize_deck
from recall.commands.validate import validate_decks


def test_validate_single_deck_reports_errors_and_sidecar_orphans(tmp_path: Path):
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    deck_path = decks_dir / "architecture.md"
    sidecar_path = decks_dir / "architecture.flashcards.json"

    deck_path.write_text(
        "## What is CQRS? #flashcard\n"
        "<!-- recall:id=architecture-cqrs -->\n\n"
        "Answer.\n\n"
        "## Empty #flashcard\n"
        "<!-- recall:id=architecture-empty -->\n",
        encoding="utf-8",
    )
    sidecar_path.write_text(
        json.dumps(
            {
                "version": 1,
                "deck": "architecture",
                "cards": {
                    "architecture-cqrs": {"rating": "good"},
                    "architecture-old-card": {"rating": "again"},
                },
            }
        ),
        encoding="utf-8",
    )

    result = validate_decks(root=tmp_path, deck="architecture")

    assert result.ok is False
    assert result.summary["decks"] == 1
    assert result.summary["cards"] == 2
    assert any(issue.code == "empty_answer" for issue in result.decks[0].issues)
    assert result.decks[0].warnings == [
        "sidecar contains orphaned card state: architecture-old-card"
    ]


def test_validate_all_decks_and_json_output(tmp_path: Path):
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    (decks_dir / "one.md").write_text(
        "## One #flashcard\n<!-- recall:id=one-card -->\n\nAnswer.\n",
        encoding="utf-8",
    )
    (decks_dir / "two.md").write_text(
        "## Two #flashcard\n<!-- recall:id=two-card -->\n\nAnswer.\n",
        encoding="utf-8",
    )

    result = validate_decks(root=tmp_path)
    payload = json.loads(validate_decks(root=tmp_path, output_format="json"))

    assert result.ok is True
    assert sorted(deck.name for deck in result.decks) == ["one", "two"]
    assert payload["ok"] is True
    assert payload["summary"] == {"decks": 2, "cards": 2, "errors": 0, "warnings": 0}


def test_normalize_deck_dry_run_and_write(tmp_path: Path):
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    deck_path = decks_dir / "architecture.md"
    deck_path.write_text(
        "## What is CQRS? #flashcard\n\nAnswer.\n",
        encoding="utf-8",
    )

    preview = normalize_deck(root=tmp_path, deck="architecture", write=False)

    assert preview.changed is True
    assert preview.written is False
    assert preview.added_ids == ["architecture-what-is-cqrs"]
    assert "<!-- recall:id=architecture-what-is-cqrs -->" in preview.content

    written = normalize_deck(root=tmp_path, deck="architecture", write=True)

    assert written.changed is True
    assert written.written is True
    assert "<!-- recall:id=architecture-what-is-cqrs -->" in deck_path.read_text(
        encoding="utf-8"
    )
