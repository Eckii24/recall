from __future__ import annotations

import random
from datetime import date
from pathlib import Path

from recall.domain.entities import (
    CardSource,
    DueCard,
    NextCardsResult,
    ReviewResult,
    ScanResult,
    StatsResult,
)
from recall.errors import CardNotFoundError, NoDueCardsError
from recall.infrastructure.deck_store import load_all_decks, load_deck, sidecar_path
from recall.infrastructure.sidecar_store import (
    create_empty_sidecar,
    load_sidecar,
    save_sidecar,
)
from recall.scheduler.base import CardState, Rating
from recall.scheduler.sm2 import SM2Scheduler

MATURE_INTERVAL_DAYS = 21


def scan(
    repo_root: Path, deck: str | None = None, today: date | None = None
) -> ScanResult:
    today = today or date.today()
    scheduler = SM2Scheduler()
    decks = [load_deck(repo_root, deck)] if deck else load_all_decks(repo_root)
    cards_total = 0
    cards_due = 0
    for item in decks:
        path = sidecar_path(repo_root, item.name)
        if not path.exists():
            save_sidecar(path, create_empty_sidecar(item.name))
        sidecar = load_sidecar(path, deck_name=item.name)
        cards_total += len(item.cards)
        for card in item.cards:
            state = sidecar["cards"].get(card.card_id, scheduler.new_card(today))
            if scheduler.is_due(state, today):
                cards_due += 1
    return ScanResult(
        decks_scanned=len(decks),
        cards_total=cards_total,
        cards_due=cards_due,
        errors=[],
    )


def next_cards(
    repo_root: Path,
    deck: str,
    limit: int = 1,
    show_answer: bool = False,
    shuffle: bool = False,
    today: date | None = None,
) -> NextCardsResult:
    today = today or date.today()
    scheduler = SM2Scheduler()
    deck_data = load_deck(repo_root, deck)
    sidecar = load_sidecar(sidecar_path(repo_root, deck), deck_name=deck)

    due_cards: list[DueCard] = []
    for card in deck_data.cards:
        state = sidecar["cards"].get(card.card_id, scheduler.new_card(today))
        if scheduler.is_due(state, today):
            due_cards.append(
                DueCard(
                    card_id=card.card_id,
                    question=card.question,
                    source=CardSource(
                        path=str(card.source_path.relative_to(repo_root)),
                        line=card.source_line,
                    ),
                    state=state,
                    answer=card.answer if show_answer else None,
                )
            )

    if shuffle:
        random.Random().shuffle(due_cards)
    due_cards = due_cards[:limit]

    if not due_cards:
        raise NoDueCardsError(deck)
    return NextCardsResult(deck=deck, cards=due_cards)


def review_card(
    repo_root: Path,
    deck: str,
    card_id: str,
    rating: Rating,
    today: date | None = None,
) -> ReviewResult:
    today = today or date.today()
    scheduler = SM2Scheduler()
    deck_data = load_deck(repo_root, deck)
    if card_id not in {card.card_id for card in deck_data.cards}:
        raise CardNotFoundError(deck, card_id)

    path = sidecar_path(repo_root, deck)
    sidecar = load_sidecar(path, deck_name=deck)
    old_state = sidecar["cards"].get(card_id, scheduler.new_card(today))
    new_state = scheduler.review(old_state, rating, today)
    sidecar["cards"][card_id] = new_state
    save_sidecar(path, sidecar)
    return ReviewResult(
        deck=deck,
        card_id=card_id,
        rating=rating,
        old_state=old_state,
        new_state=new_state,
    )


def _category(state: CardState) -> str:
    if state.reps == 0 and state.interval == 0:
        return "new"
    if state.interval >= MATURE_INTERVAL_DAYS:
        return "mature"
    return "young"


def stats(
    repo_root: Path, deck: str | None = None, today: date | None = None
) -> StatsResult:
    today = today or date.today()
    scheduler = SM2Scheduler()
    decks = [load_deck(repo_root, deck)] if deck else load_all_decks(repo_root)

    totals = {"cards_total": 0, "due_today": 0, "new": 0, "young": 0, "mature": 0}
    for deck_data in decks:
        sidecar = load_sidecar(
            sidecar_path(repo_root, deck_data.name), deck_name=deck_data.name
        )
        totals["cards_total"] += len(deck_data.cards)
        for card in deck_data.cards:
            state = sidecar["cards"].get(card.card_id, scheduler.new_card(today))
            if scheduler.is_due(state, today):
                totals["due_today"] += 1
            totals[_category(state)] += 1

    return StatsResult(
        cards_total=totals["cards_total"],
        due_today=totals["due_today"],
        new=totals["new"],
        young=totals["young"],
        mature=totals["mature"],
        deck=deck,
        decks=None if deck else len(decks),
    )
