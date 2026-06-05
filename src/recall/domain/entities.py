from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from recall.domain.scheduler.base import CardState, Rating


@dataclass(slots=True, frozen=True)
class ParseIssue:
    code: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, frozen=True)
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


@dataclass(slots=True, frozen=True)
class Card:
    card_id: str
    question: str
    answer: str
    source_path: Path
    source_line: int


@dataclass(slots=True, frozen=True)
class Deck:
    name: str
    path: Path
    cards: list[Card]


@dataclass(slots=True, frozen=True)
class DeckCreationResult:
    deck_name: str
    markdown_path: Path
    sidecar_path: Path


@dataclass(slots=True, frozen=True)
class DeckListItem:
    name: str
    path: Path
    card_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path.as_posix(),
            "card_count": self.card_count,
        }


@dataclass(slots=True, frozen=True)
class ScanResult:
    decks_scanned: int
    cards_total: int
    cards_due: int
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decks_scanned": self.decks_scanned,
            "cards_total": self.cards_total,
            "cards_due": self.cards_due,
            "errors": list(self.errors),
        }


@dataclass(slots=True, frozen=True)
class CardSource:
    path: str
    line: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, frozen=True)
class DueCard:
    card_id: str
    question: str
    source: CardSource
    state: CardState
    answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "card_id": self.card_id,
            "question": self.question,
            "source": self.source.to_dict(),
            "state": self.state.to_dict(),
        }
        if self.answer is not None:
            payload["answer"] = self.answer
        return payload


@dataclass(slots=True, frozen=True)
class NextCardsResult:
    deck: str
    cards: list[DueCard]

    def to_dict(self) -> dict[str, Any]:
        return {"deck": self.deck, "cards": [card.to_dict() for card in self.cards]}


@dataclass(slots=True, frozen=True)
class ReviewResult:
    deck: str
    card_id: str
    rating: Rating
    old_state: CardState
    new_state: CardState

    def to_dict(self) -> dict[str, Any]:
        return {
            "deck": self.deck,
            "card_id": self.card_id,
            "rating": self.rating,
            "old_state": self.old_state.to_dict(),
            "new_state": self.new_state.to_dict(),
        }


@dataclass(slots=True, frozen=True)
class StatsResult:
    cards_total: int
    due_today: int
    new: int
    young: int
    mature: int
    deck: str | None = None
    decks: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "cards_total": self.cards_total,
            "due_today": self.due_today,
            "new": self.new,
            "young": self.young,
            "mature": self.mature,
        }
        if self.deck is not None:
            payload["deck"] = self.deck
        if self.decks is not None:
            payload["decks"] = self.decks
        return payload
