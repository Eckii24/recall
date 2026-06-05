from __future__ import annotations

from math import ceil
from datetime import date, timedelta

from recall.scheduler.base import CardState, Rating, Scheduler

RATING_TO_QUALITY: dict[Rating, int] = {
    "again": 0,
    "hard": 2,
    "good": 3,
    "easy": 5,
}


def rating_to_quality(rating: Rating) -> int:
    return RATING_TO_QUALITY[rating]


class SM2Scheduler(Scheduler):
    def new_card(self, today: date) -> CardState:
        return CardState(due=today, ease=2.5, interval=0, reps=0)

    def is_due(self, state: CardState, today: date) -> bool:
        return state.due <= today

    def review(self, state: CardState, rating: Rating, today: date) -> CardState:
        quality = rating_to_quality(rating)

        if quality < 3:
            interval = 1
            reps = 0
        else:
            if state.reps == 0:
                interval = 1
            elif state.reps == 1:
                interval = 6
            else:
                interval = ceil(state.interval * state.ease)
            reps = state.reps + 1

        ease = state.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ease = round(max(1.3, ease), 2)
        due = today + timedelta(days=interval)
        return CardState(due=due, ease=ease, interval=interval, reps=reps)
