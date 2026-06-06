from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from recall.domain.entities import (
    CollectionValidationResult,
    DeckValidationResult,
    NormalizeResult,
    ParseIssue,
    ValidationSummary,
)
from recall.domain.markdown import normalize_deck_markdown, parse_markdown_deck
from recall.infrastructure.collection_store import get_collection_details
from recall.infrastructure.config_store import load_config
from recall.infrastructure.sidecar_store import load_collection_sidecar


def _decks_dir(root: Path) -> Path:
    return root / load_config(root).decks_dir


def _discover_decks(root: Path, deck: str | None) -> list[Path]:
    decks_dir = _decks_dir(root)
    if deck:
        return [decks_dir / f"{deck}.md"]
    return sorted(decks_dir.glob("*.md"))


def _validate_deck_path(root_path: Path, deck_path: Path) -> DeckValidationResult:
    config = load_config(root_path)
    deck_name = deck_path.stem
    markdown = deck_path.read_text(encoding="utf-8")
    parsed = parse_markdown_deck(
        markdown,
        deck_name=deck_name,
        auto_mode=config.default_auto_mode,
        min_heading_level=config.default_min_heading_level,
    )
    result = DeckValidationResult(
        name=deck_name,
        path=str(deck_path),
        cards=parsed.cards,
        issues=parsed.issues,
    )
    sidecar_path = deck_path.parent / f"{deck_name}{config.sidecar_suffix}"
    if sidecar_path.exists():
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
        cards = payload.get("cards", {})
        sidecar_cards = set(cards.keys()) if isinstance(cards, dict) else set()
        markdown_cards = {card.card_id for card in parsed.cards}
        for orphan_id in sorted(sidecar_cards - markdown_cards):
            result.warnings.append(f"sidecar contains orphaned card state: {orphan_id}")
    return result


def validate_decks(
    root: str | Path, deck: str | None = None, collection: str | None = None
) -> ValidationSummary:
    root_path = Path(root)
    if collection is not None:
        details = get_collection_details(root_path, collection)
        results = [_validate_deck_path(root_path, deck_path) for deck_path in details.files]
        duplicates = Counter(
            card.card_id for result in results for card in result.cards if card.card_id
        )
        for result in results:
            for card in result.cards:
                if duplicates[card.card_id] > 1:
                    result.issues.append(
                        ParseIssue(
                            code="duplicate_id",
                            message=f"Duplicate card id across collection: {card.card_id}",
                            line=card.line,
                        )
                    )
        sidecar = load_collection_sidecar(
            root_path / ".recall" / "collections" / f"{collection}.flashcards.json",
            collection_name=collection,
        )
        markdown_cards = {card.card_id for result in results for card in result.cards}
        orphan_ids = sorted(set(sidecar["cards"].keys()) - markdown_cards)
        if orphan_ids and results:
            for orphan_id in orphan_ids:
                results[0].warnings.append(
                    f"sidecar contains orphaned card state: {orphan_id}"
                )
        return ValidationSummary(
            decks=[],
            collection=CollectionValidationResult(
                name=collection,
                include=details.include,
                exclude=details.exclude,
                files=results,
            ),
        )

    results = []
    for deck_path in _discover_decks(root_path, deck):
        results.append(_validate_deck_path(root_path, deck_path))
    return ValidationSummary(results)


def validate_decks_as_json(root: str | Path, deck: str | None = None) -> str:
    return json.dumps(validate_decks(root, deck).to_dict())


def normalize_deck(root: str | Path, deck: str, write: bool = False) -> NormalizeResult:
    root_path = Path(root)
    config = load_config(root_path)
    deck_path = root_path / config.decks_dir / f"{deck}.md"
    markdown = deck_path.read_text(encoding="utf-8")
    return normalize_deck_markdown(
        markdown,
        deck_name=deck,
        write=write,
        path=deck_path,
        auto_mode=config.default_auto_mode,
        min_heading_level=config.default_min_heading_level,
    )
