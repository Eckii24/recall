from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from recall.errors import CardNotFoundError
from recall.repository import load_deck, sidecar_path
from recall.scheduler.sm2 import SM2Scheduler
from recall.sidecar import load_sidecar, save_sidecar


def run(
    repo_root: Path,
    deck: str,
    card_id: str,
    rating: str,
    output_format: str = "text",
    today: date | None = None,
) -> str:
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

    payload = {
        "deck": deck,
        "card_id": card_id,
        "rating": rating,
        "old_state": old_state.to_dict(),
        "new_state": new_state.to_dict(),
    }
    if output_format == "json":
        return json.dumps(payload, sort_keys=True)
    return f"Reviewed {card_id}: {rating}"
