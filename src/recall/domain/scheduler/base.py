from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, Protocol

Rating = Literal["again", "hard", "good", "easy"]


@dataclass(frozen=True)
class CardState:
    due: date
    ease: float
    interval: int
    reps: int

    def to_dict(self) -> dict[str, object]:
        return {
            "due": self.due.isoformat(),
            "ease": self.ease,
            "interval": self.interval,
            "reps": self.reps,
        }


class Scheduler(Protocol):
    def new_card(self, today: date) -> CardState: ...

    def is_due(self, state: CardState, today: date) -> bool: ...

    def review(self, state: CardState, rating: Rating, today: date) -> CardState: ...
