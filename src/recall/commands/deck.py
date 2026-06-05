from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from recall.config import load_config
from recall.errors import InvalidArgumentsError, WriteError

DECK_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")


def titleize_deck_name(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def validate_deck_name(name: str) -> None:
    if not DECK_NAME_PATTERN.fullmatch(name):
        raise InvalidArgumentsError(f"Invalid deck name: {name}")


def create_deck(name: str, *, base_path: Path | None = None) -> dict[str, Path]:
    validate_deck_name(name)
    project_root = base_path or Path.cwd()
    config = load_config(project_root)
    decks_dir = project_root / config.decks_dir
    decks_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = decks_dir / f"{name}.md"
    sidecar_path = decks_dir / f"{name}{config.sidecar_suffix}"
    if markdown_path.exists() or sidecar_path.exists():
        raise WriteError(f"Deck already exists: {name}")

    markdown_path.write_text(f"# {titleize_deck_name(name)}\n")
    sidecar_path.write_text(
        json.dumps({"version": 1, "deck": name, "cards": {}}, indent=2) + "\n"
    )
    return {"markdown_path": markdown_path, "sidecar_path": sidecar_path}


def list_decks(*, base_path: Path | None = None) -> list[dict[str, Any]]:
    project_root = base_path or Path.cwd()
    config = load_config(project_root)
    decks_dir = project_root / config.decks_dir
    if not decks_dir.exists():
        return []

    decks: list[dict[str, Any]] = []
    for markdown_path in sorted(decks_dir.glob("*.md")):
        name = markdown_path.stem
        sidecar_path = decks_dir / f"{name}{config.sidecar_suffix}"
        card_count = 0
        if sidecar_path.exists():
            payload = json.loads(sidecar_path.read_text())
            cards = payload.get("cards", {})
            if isinstance(cards, dict):
                card_count = len(cards)
        decks.append(
            {
                "name": name,
                "path": str(markdown_path.relative_to(project_root)),
                "card_count": card_count,
            }
        )

    return decks
