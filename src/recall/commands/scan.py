from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from recall.repository import load_all_decks, load_deck, sidecar_path
from recall.scheduler.sm2 import SM2Scheduler
from recall.sidecar import create_empty_sidecar, load_sidecar, save_sidecar


def run(repo_root: Path, deck: str | None = None, output_format: str = "text", today: date | None = None) -> str:
    today = today or date.today()
    scheduler = SM2Scheduler()
    decks = [load_deck(repo_root, deck)] if deck else load_all_decks(repo_root)
    errors: list[str] = []
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
    payload = {
        "decks_scanned": len(decks),
        "cards_total": cards_total,
        "cards_due": cards_due,
        "errors": errors,
    }
    if output_format == "json":
        return json.dumps(payload, sort_keys=True)
    return f"Scanned {payload['decks_scanned']} decks, {cards_total} cards, {cards_due} due."
