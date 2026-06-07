from __future__ import annotations

import random
from datetime import date
from pathlib import Path

from recall.domain.entities import (
    Card,
    CardSource,
    DueCard,
    NextCardsResult,
    ReviewResult,
    ScanResult,
    StatsResult,
)
from recall.domain.errors import CardNotFoundError, NoDueCardsError
from recall.domain.scheduler.base import CardState, Rating
from recall.domain.scheduler.sm2 import SM2Scheduler
from recall.infrastructure.collection_store import (
    collection_sidecar_path,
    load_collection,
)
from recall.infrastructure.deck_store import load_all_decks, load_deck, sidecar_path
from recall.infrastructure.sidecar_store import (
    create_empty_collection_sidecar,
    create_empty_sidecar,
    load_collection_sidecar,
    load_sidecar,
    save_collection_sidecar,
    save_sidecar,
)

MATURE_INTERVAL_DAYS = 21


def _is_new(state: CardState) -> bool:
    return state.reps == 0 and state.interval == 0


def _collection_card_state(
    repo_root: Path,
    collection_name: str,
    card: Card,
    scheduler: SM2Scheduler,
    today: date,
) -> tuple[CardState, str]:
    sidecar = load_collection_sidecar(
        collection_sidecar_path(repo_root, collection_name),
        collection_name=collection_name,
    )
    entry = sidecar["cards"].get(card.card_id)
    if entry is None:
        return scheduler.new_card(today), str(card.source_path.relative_to(repo_root))
    return entry["state"], entry["source_path"]


def scan(
    repo_root: Path,
    deck: str | None = None,
    collection: str | None = None,
    today: date | None = None,
) -> ScanResult:
    today = today or date.today()
    scheduler = SM2Scheduler()
    if collection is not None:
        loaded = load_collection(repo_root, collection)
        path = collection_sidecar_path(repo_root, collection)
        if not path.exists():
            save_collection_sidecar(path, create_empty_collection_sidecar(collection))
        sidecar = load_collection_sidecar(path, collection_name=collection)
        cards_due = 0
        for card in loaded.cards:
            entry = sidecar["cards"].get(card.card_id)
            state = entry["state"] if entry is not None else scheduler.new_card(today)
            if scheduler.is_due(state, today):
                cards_due += 1
        return ScanResult(
            decks_scanned=len(loaded.files),
            cards_total=len(loaded.cards),
            cards_due=cards_due,
            errors=[],
            collection=collection,
        )

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
    deck: str | None = None,
    collection: str | None = None,
    limit: int = 1,
    show_answer: bool = False,
    shuffle: bool = False,
    new_only: bool = False,
    today: date | None = None,
) -> NextCardsResult:
    today = today or date.today()
    scheduler = SM2Scheduler()

    due_cards: list[DueCard] = []
    if collection is not None:
        loaded = load_collection(repo_root, collection)
        sidecar = load_collection_sidecar(
            collection_sidecar_path(repo_root, collection),
            collection_name=collection,
        )
        for card in loaded.cards:
            entry = sidecar["cards"].get(card.card_id)
            state = entry["state"] if entry is not None else scheduler.new_card(today)
            if new_only and not _is_new(state):
                continue
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
            raise NoDueCardsError(collection)
        return NextCardsResult(cards=due_cards, collection=collection)

    assert deck is not None
    deck_data = load_deck(repo_root, deck)
    sidecar = load_sidecar(sidecar_path(repo_root, deck), deck_name=deck)

    for card in deck_data.cards:
        state = sidecar["cards"].get(card.card_id, scheduler.new_card(today))
        if new_only and not _is_new(state):
            continue
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
    return NextCardsResult(cards=due_cards, deck=deck)


def review_card(
    repo_root: Path,
    deck: str | None = None,
    collection: str | None = None,
    card_id: str = "",
    rating: Rating = "good",
    today: date | None = None,
) -> ReviewResult:
    today = today or date.today()
    scheduler = SM2Scheduler()
    if collection is not None:
        loaded = load_collection(repo_root, collection)
        card_by_id = {card.card_id: card for card in loaded.cards}
        if card_id not in card_by_id:
            raise CardNotFoundError(collection, card_id)
        card = card_by_id[card_id]
        path = collection_sidecar_path(repo_root, collection)
        sidecar = load_collection_sidecar(path, collection_name=collection)
        entry = sidecar["cards"].get(card_id)
        old_state = entry["state"] if entry is not None else scheduler.new_card(today)
        new_state = scheduler.review(old_state, rating, today)
        sidecar["cards"][card_id] = {
            "state": new_state,
            "source_path": str(card.source_path.relative_to(repo_root)),
        }
        save_collection_sidecar(path, sidecar)
        return ReviewResult(
            card_id=card_id,
            rating=rating,
            old_state=old_state,
            new_state=new_state,
            collection=collection,
        )

    assert deck is not None
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
        card_id=card_id,
        rating=rating,
        old_state=old_state,
        new_state=new_state,
        deck=deck,
    )


def _category(state: CardState) -> str:
    if state.reps == 0 and state.interval == 0:
        return "new"
    if state.interval >= MATURE_INTERVAL_DAYS:
        return "mature"
    return "young"


def stats(
    repo_root: Path,
    deck: str | None = None,
    collection: str | None = None,
    today: date | None = None,
) -> StatsResult:
    today = today or date.today()
    scheduler = SM2Scheduler()
    if collection is not None:
        loaded = load_collection(repo_root, collection)
        sidecar = load_collection_sidecar(
            collection_sidecar_path(repo_root, collection),
            collection_name=collection,
        )
        totals = {
            "cards_total": len(loaded.cards),
            "due_today": 0,
            "new": 0,
            "young": 0,
            "mature": 0,
        }
        for card in loaded.cards:
            entry = sidecar["cards"].get(card.card_id)
            state = entry["state"] if entry is not None else scheduler.new_card(today)
            if scheduler.is_due(state, today):
                totals["due_today"] += 1
            totals[_category(state)] += 1
        return StatsResult(
            cards_total=totals["cards_total"],
            due_today=totals["due_today"],
            new=totals["new"],
            young=totals["young"],
            mature=totals["mature"],
            collection=collection,
        )

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
