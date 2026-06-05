from __future__ import annotations

from pathlib import Path
from typing import Any

from recall.application.decks import create_deck as create_deck_use_case
from recall.application.decks import list_decks as list_decks_use_case


def create_deck(name: str, *, base_path: Path | None = None) -> dict[str, Path]:
    result = create_deck_use_case(base_path or Path.cwd(), name)
    return {"markdown_path": result.markdown_path, "sidecar_path": result.sidecar_path}


def list_decks(*, base_path: Path | None = None) -> list[dict[str, Any]]:
    return [deck.to_dict() for deck in list_decks_use_case(base_path or Path.cwd())]
