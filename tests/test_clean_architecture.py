from __future__ import annotations

from datetime import date
from pathlib import Path

from recall.application import decks as deck_use_cases
from recall.application import learning as learning_use_cases
from recall.application import validation as validation_use_cases
from recall.cli import app as legacy_app
from recall.interfaces.cli import app as cli_app
from recall.sidecar import load_sidecar

TAGGED_DECK = """# Architecture

## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt Commands und Queries.
"""


def test_cli_module_is_compatibility_wrapper() -> None:
    assert legacy_app is cli_app


def test_application_deck_use_cases_return_typed_results(tmp_path: Path) -> None:
    created = deck_use_cases.create_deck(tmp_path, "architecture")
    listed = deck_use_cases.list_decks(tmp_path)

    assert created.deck_name == "architecture"
    assert created.markdown_path == tmp_path / "decks" / "architecture.md"
    assert created.sidecar_path == tmp_path / "decks" / "architecture.flashcards.json"
    assert listed == [
        deck_use_cases.DeckListItem(
            name="architecture",
            path=Path("decks/architecture.md"),
            card_count=0,
        )
    ]


def test_validation_and_normalization_use_cases_return_objects(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    (decks_dir / "architecture.md").write_text(
        "## Was ist CQRS? #flashcard\n\nCQRS trennt Commands und Queries.\n",
        encoding="utf-8",
    )

    preview = validation_use_cases.normalize_deck(tmp_path, "architecture", write=False)
    summary = validation_use_cases.validate_decks(tmp_path, deck="architecture")

    assert preview.changed is True
    assert preview.written is False
    assert preview.added_ids == ["architecture-was-ist-cqrs"]
    assert summary.ok is False
    assert summary.decks[0].issues[0].code == "missing_id"


def test_learning_use_cases_are_filesystem_backed_but_cli_agnostic(
    tmp_path: Path,
) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    (decks_dir / "architecture.md").write_text(TAGGED_DECK, encoding="utf-8")

    scan_result = learning_use_cases.scan(
        tmp_path, deck="architecture", today=date(2026, 6, 5)
    )
    next_result = learning_use_cases.next_cards(
        tmp_path,
        deck="architecture",
        limit=1,
        show_answer=True,
        shuffle=False,
        today=date(2026, 6, 5),
    )
    review_result = learning_use_cases.review_card(
        tmp_path,
        deck="architecture",
        card_id="architecture-cqrs",
        rating="good",
        today=date(2026, 6, 5),
    )
    stats_result = learning_use_cases.stats(
        tmp_path, deck="architecture", today=date(2026, 6, 5)
    )

    assert scan_result.cards_due == 1
    assert next_result.deck == "architecture"
    assert next_result.cards[0].answer == "CQRS trennt Commands und Queries."
    assert review_result.new_state.interval == 1
    assert stats_result.deck == "architecture"
    assert stats_result.due_today == 0

    sidecar = load_sidecar(tmp_path / "decks" / "architecture.flashcards.json")
    assert sidecar["cards"]["architecture-cqrs"].interval == 1
