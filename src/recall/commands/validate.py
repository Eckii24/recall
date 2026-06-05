from __future__ import annotations

import json
from pathlib import Path

from ..config import load_config
from ..models import DeckValidationResult, ValidationSummary
from ..parser import parse_markdown_deck


def _decks_dir(root: Path) -> Path:
    return root / load_config(root).decks_dir


def _discover_decks(root: Path, deck: str | None) -> list[Path]:
    decks_dir = _decks_dir(root)
    if deck:
        return [decks_dir / f"{deck}.md"]
    return sorted(decks_dir.glob("*.md"))


def validate_decks(root: str | Path, deck: str | None = None, output_format: str = "object"):
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
        result = DeckValidationResult(name=deck_name, path=str(deck_path), cards=parsed.cards, issues=parsed.issues)
        sidecar_path = deck_path.parent / f"{deck_name}{config.sidecar_suffix}"
        if sidecar_path.exists():
            payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
            sidecar_cards = set(payload.get("cards", {}).keys())
            markdown_cards = {card.card_id for card in parsed.cards}
            for orphan_id in sorted(sidecar_cards - markdown_cards):
                result.warnings.append(f"sidecar contains orphaned card state: {orphan_id}")
        results.append(result)
    summary = ValidationSummary(results)
    if output_format == "json":
        return json.dumps(summary.to_dict())
    return summary
