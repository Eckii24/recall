from __future__ import annotations

from pathlib import Path

from ..config import load_config
from ..parser import normalize_deck_markdown


def normalize_deck(root: str | Path, deck: str, write: bool = False):
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
