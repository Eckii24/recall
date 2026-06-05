from __future__ import annotations

from pathlib import Path

from recall.domain.entities import DeckCreationResult, DeckListItem
from recall.infrastructure.deck_store import create_deck_files, list_deck_items


def create_deck(base_path: Path, name: str) -> DeckCreationResult:
    return create_deck_files(base_path, name)


def list_decks(base_path: Path) -> list[DeckListItem]:
    return list_deck_items(base_path)
