from __future__ import annotations

import json
from pathlib import Path

from recall.domain.entities import (
    DeckValidationResult,
    NormalizeResult,
    ValidationSummary,
)
from recall.domain.markdown import normalize_deck_markdown, parse_markdown_deck
from recall.infrastructure.config_store import load_config


def _decks_dir(root: Path) -> Path:
    return root / load_config(root).decks_dir


def _discover_decks(root: Path, deck: str | None) -> list[Path]:
    decks_dir = _decks_dir(root)
    if deck:
        return [decks_dir / f"{deck}.md"]
    return sorted(decks_dir.glob("*.md"))


def validate_decks(root: str | Path, deck: str | None = None) -> ValidationSummary:
    root_path = Path(root)
    config = load_config(root_path)
    results: list[DeckValidationResult] = []
    for deck_path in _discover_decks(root_path, deck):
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
                result.warnings.append(
                    f"sidecar contains orphaned card state: {orphan_id}"
                )
        results.append(result)
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
