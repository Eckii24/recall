from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from recall.repository import load_all_decks, load_deck, sidecar_path
from recall.scheduler.base import CardState
from recall.scheduler.sm2 import SM2Scheduler
from recall.sidecar import load_sidecar

MATURE_INTERVAL_DAYS = 21


def _category(state: CardState) -> str:
    if state.reps == 0 and state.interval == 0:
        return "new"
    if state.interval >= MATURE_INTERVAL_DAYS:
        return "mature"
    return "young"


def _stats_for_decks(repo_root: Path, deck_names: list[str], today: date) -> dict[str, int]:
    scheduler = SM2Scheduler()
    totals = {"cards_total": 0, "due_today": 0, "new": 0, "young": 0, "mature": 0}
    for deck_name in deck_names:
        deck = load_deck(repo_root, deck_name)
        sidecar = load_sidecar(sidecar_path(repo_root, deck_name), deck_name=deck_name)
        totals["cards_total"] += len(deck.cards)
        for card in deck.cards:
            state = sidecar["cards"].get(card.card_id, scheduler.new_card(today))
            if scheduler.is_due(state, today):
                totals["due_today"] += 1
            totals[_category(state)] += 1
    return totals


def run(repo_root: Path, deck: str | None = None, output_format: str = "text", today: date | None = None) -> str:
    today = today or date.today()
    deck_names = [deck] if deck else [item.name for item in load_all_decks(repo_root)]
    payload = _stats_for_decks(repo_root, deck_names, today)
    if deck:
        payload = {"deck": deck, **payload}
    else:
        payload = {"decks": len(deck_names), **payload}
    if output_format == "json":
        return json.dumps(payload, sort_keys=True)
    return "\n".join(f"{key}: {value}" for key, value in payload.items())
