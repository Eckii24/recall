from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from recall.config import Config, load_config
from recall.errors import DeckNotFoundError, InvalidCardFormatError
from recall.parser import parse_markdown_deck


@dataclass(frozen=True)
class Card:
    card_id: str
    question: str
    answer: str
    source_path: Path
    source_line: int


@dataclass(frozen=True)
class Deck:
    name: str
    path: Path
    cards: list[Card]


def _config(repo_root: Path) -> Config:
    return load_config(repo_root)


def decks_dir(repo_root: Path) -> Path:
    return repo_root / _config(repo_root).decks_dir


def deck_path(repo_root: Path, deck_name: str) -> Path:
    return decks_dir(repo_root) / f"{deck_name}.md"


def sidecar_path(repo_root: Path, deck_name: str) -> Path:
    config = _config(repo_root)
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
            f"{issue.code} at line {issue.line}: {issue.message}" if issue.line is not None else f"{issue.code}: {issue.message}"
            for issue in parsed.issues
        )
        raise InvalidCardFormatError(f"Invalid card format in deck {deck_name}: {details}")

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
    config = _config(repo_root)
    path = deck_path(repo_root, deck_name)
    if not path.exists():
        raise DeckNotFoundError(deck_name)
    return _parse_loaded_deck(path, deck_name, config)


def load_all_decks(repo_root: Path) -> list[Deck]:
    config = _config(repo_root)
    results: list[Deck] = []
    for deck_name in list_deck_names(repo_root):
        path = deck_path(repo_root, deck_name)
        results.append(_parse_loaded_deck(path, deck_name, config))
    return results
