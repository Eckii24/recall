from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ParseIssue:
    code: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Flashcard:
    card_id: str
    question: str
    answer: str
    heading_level: int
    line: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParsedDeck:
    deck_name: str
    cards: list[Flashcard] = field(default_factory=list)
    issues: list[ParseIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "deck_name": self.deck_name,
            "cards": [card.to_dict() for card in self.cards],
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(slots=True)
class NormalizeResult:
    deck_name: str
    content: str
    changed: bool
    missing_ids: list[str] = field(default_factory=list)
    written: bool = False

    @property
    def added_ids(self) -> list[str]:
        return self.missing_ids


@dataclass(slots=True)
class DeckValidationResult:
    name: str
    path: str
    cards: list[Flashcard] = field(default_factory=list)
    issues: list[ParseIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "cards": [card.to_dict() for card in self.cards],
            "issues": [issue.to_dict() for issue in self.issues],
            "warnings": list(self.warnings),
            "ok": self.ok,
        }


@dataclass(slots=True)
class ValidationSummary:
    decks: list[DeckValidationResult]

    @property
    def ok(self) -> bool:
        return all(deck.ok for deck in self.decks)

    @property
    def summary(self) -> dict[str, int]:
        return {
            "decks": len(self.decks),
            "cards": sum(len(deck.cards) for deck in self.decks),
            "errors": sum(len(deck.issues) for deck in self.decks),
            "warnings": sum(len(deck.warnings) for deck in self.decks),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": self.summary,
            "decks": [deck.to_dict() for deck in self.decks],
        }
