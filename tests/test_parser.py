from pathlib import Path

import pytest

from recall.domain.markdown import (
    generate_card_id,
    normalize_deck_markdown,
    parse_markdown_deck,
)


def test_parse_tagged_mode_extracts_heading_based_cards_with_explicit_ids():
    markdown = """---
title: Architecture
---

# Architecture

## What is CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS separates reads and writes.

### Details

More detail.

## Ignored heading
<!-- recall:id=architecture-ignored -->

This is not tagged.
"""

    deck = parse_markdown_deck(markdown, deck_name="architecture", auto_mode=False)

    assert [card.card_id for card in deck.cards] == ["architecture-cqrs"]
    assert deck.cards[0].question == "What is CQRS?"
    assert "CQRS separates reads and writes." in deck.cards[0].answer
    assert "### Details" in deck.cards[0].answer
    assert deck.issues == []


def test_parse_auto_mode_uses_min_heading_level_and_ignores_frontmatter_and_code():
    markdown = """---
title: Demo
---

# Deck title

```markdown
## Not a card #flashcard
<!-- recall:id=ignored -->
```

## First question
<!-- recall:id=demo-first-question -->

Answer one.

### Still part of answer

Yes.

## Second question
<!-- recall:id=demo-second-question -->

Answer two.
"""

    deck = parse_markdown_deck(
        markdown, deck_name="demo", auto_mode=True, min_heading_level=2
    )

    assert [card.card_id for card in deck.cards] == [
        "demo-first-question",
        "demo-second-question",
    ]
    assert "## Not a card" not in deck.cards[0].question
    assert "### Still part of answer" in deck.cards[0].answer


@pytest.mark.parametrize(
    "card_id",
    ["ok", "deck.topic:1", "A_B-c:d"],
)
def test_valid_id_syntax_is_accepted(card_id):
    markdown = f"## Q? #flashcard\n<!-- recall:id={card_id} -->\n\nA\n"

    deck = parse_markdown_deck(markdown, deck_name="deck", auto_mode=False)

    assert deck.issues == []
    assert deck.cards[0].card_id == card_id


@pytest.mark.parametrize(
    "card_id",
    ["bad id", "bad/id", "äöü", ""],
)
def test_invalid_id_syntax_is_reported(card_id):
    markdown = f"## Q? #flashcard\n<!-- recall:id={card_id} -->\n\nA\n"

    deck = parse_markdown_deck(markdown, deck_name="deck", auto_mode=False)

    assert any(issue.code == "invalid_id" for issue in deck.issues)


def test_duplicate_ids_and_empty_answers_are_reported():
    markdown = """## One #flashcard
<!-- recall:id=dup -->

Answer.

## Two #flashcard
<!-- recall:id=dup -->

   
"""

    deck = parse_markdown_deck(markdown, deck_name="deck", auto_mode=False)

    assert [issue.code for issue in deck.issues] == ["duplicate_id", "empty_answer"]


def test_missing_id_directly_under_heading_is_reported():
    markdown = """## Question #flashcard

Answer before id.
<!-- recall:id=late-id -->
"""

    deck = parse_markdown_deck(markdown, deck_name="deck", auto_mode=False)

    assert any(issue.code == "missing_id" for issue in deck.issues)


def test_normalize_dry_run_reports_missing_ids_and_write_inserts_deterministic_ids(
    tmp_path: Path,
):
    deck_path = tmp_path / "architecture.md"
    deck_path.write_text(
        "# Architecture\n\n"
        "## What is CQRS? #flashcard\n\n"
        "Answer.\n\n"
        "## What is CQRS? #flashcard\n\n"
        "Another answer.\n",
        encoding="utf-8",
    )

    preview = normalize_deck_markdown(
        deck_path.read_text(encoding="utf-8"), deck_name="architecture", write=False
    )

    assert preview.changed is True
    assert preview.missing_ids == [
        "architecture-what-is-cqrs",
        "architecture-what-is-cqrs-2",
    ]
    assert "recall:id=architecture-what-is-cqrs" in preview.content
    assert (
        deck_path.read_text(encoding="utf-8") == "# Architecture\n\n"
        "## What is CQRS? #flashcard\n\n"
        "Answer.\n\n"
        "## What is CQRS? #flashcard\n\n"
        "Another answer.\n"
    )

    written = normalize_deck_markdown(
        deck_path.read_text(encoding="utf-8"),
        deck_name="architecture",
        write=True,
        path=deck_path,
    )

    assert written.changed is True
    text = deck_path.read_text(encoding="utf-8")
    assert "<!-- recall:id=architecture-what-is-cqrs -->" in text
    assert "<!-- recall:id=architecture-what-is-cqrs-2 -->" in text


def test_generate_card_id_slugifies_and_deduplicates():
    used_ids = {"architecture-what-is-cqrs"}

    generated = generate_card_id("architecture", "What is CQRS?", used_ids)

    assert generated == "architecture-what-is-cqrs-2"
