from __future__ import annotations

import json
import re
from pathlib import Path

from recall.domain.entities import Card, Deck, DeckCreationResult, DeckListItem
from recall.domain.markdown import parse_markdown_deck
from recall.errors import (
    DeckNotFoundError,
    InvalidArgumentsError,
    InvalidCardFormatError,
    WriteError,
)
from recall.infrastructure.config_store import Config, load_config

DECK_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")


def titleize_deck_name(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def validate_deck_name(name: str) -> None:
    if not DECK_NAME_PATTERN.fullmatch(name):
        raise InvalidArgumentsError(f"Invalid deck name: {name}")


def decks_dir(repo_root: Path) -> Path:
    return repo_root / load_config(repo_root).decks_dir


def deck_path(repo_root: Path, deck_name: str) -> Path:
    return decks_dir(repo_root) / f"{deck_name}.md"


def sidecar_path(repo_root: Path, deck_name: str) -> Path:
    config = load_config(repo_root)
    return decks_dir(repo_root) / f"{deck_name}{config.sidecar_suffix}"


def list_deck_names(repo_root: Path) -> list[str]:
    root = decks_dir(repo_root)
    if not root.exists():
        return []
    return sorted(path.stem for path in root.glob("*.md"))


def _parse_loaded_deck(path: Path, deck_name: str, config: Config) -> Deck:
    markdown = path.read_text(encoding="utf-8")
    parsed = parse_markdown_deck(
        markdown,
        deck_name=deck_name,
        auto_mode=config.default_auto_mode,
        min_heading_level=config.default_min_heading_level,
    )
    if parsed.issues:
        details = "; ".join(
            f"{issue.code} at line {issue.line}: {issue.message}"
            if issue.line is not None
            else f"{issue.code}: {issue.message}"
            for issue in parsed.issues
        )
        raise InvalidCardFormatError(
            f"Invalid card format in deck {deck_name}: {details}"
        )

    return Deck(
        name=deck_name,
        path=path,
        cards=[
            Card(
                card_id=card.card_id,
                question=card.question,
                answer=card.answer,
                source_path=path,
                source_line=card.line,
            )
            for card in parsed.cards
        ],
    )


def load_deck(repo_root: Path, deck_name: str) -> Deck:
    config = load_config(repo_root)
    path = deck_path(repo_root, deck_name)
    if not path.exists():
        raise DeckNotFoundError(deck_name)
    return _parse_loaded_deck(path, deck_name, config)


def load_all_decks(repo_root: Path) -> list[Deck]:
    config = load_config(repo_root)
    results: list[Deck] = []
    for deck_name in list_deck_names(repo_root):
        path = deck_path(repo_root, deck_name)
        results.append(_parse_loaded_deck(path, deck_name, config))
    return results


def create_deck_files(project_root: Path, name: str) -> DeckCreationResult:
    validate_deck_name(name)
    config = load_config(project_root)
    root = project_root / config.decks_dir
    root.mkdir(parents=True, exist_ok=True)

    markdown_path = root / f"{name}.md"
    sidecar_file_path = root / f"{name}{config.sidecar_suffix}"
    if markdown_path.exists() or sidecar_file_path.exists():
        raise WriteError(f"Deck already exists: {name}")

    markdown_path.write_text(f"# {titleize_deck_name(name)}\n", encoding="utf-8")
    sidecar_file_path.write_text(
        json.dumps({"version": 1, "deck": name, "cards": {}}, indent=2) + "\n",
        encoding="utf-8",
    )
    return DeckCreationResult(
        deck_name=name, markdown_path=markdown_path, sidecar_path=sidecar_file_path
    )


def list_deck_items(project_root: Path) -> list[DeckListItem]:
    config = load_config(project_root)
    root = project_root / config.decks_dir
    if not root.exists():
        return []

    decks: list[DeckListItem] = []
    for markdown_path in sorted(root.glob("*.md")):
        name = markdown_path.stem
        parsed_deck = _parse_loaded_deck(markdown_path, name, config)
        decks.append(
            DeckListItem(
                name=name,
                path=markdown_path.relative_to(project_root),
                card_count=len(parsed_deck.cards),
            )
        )

    return decks
