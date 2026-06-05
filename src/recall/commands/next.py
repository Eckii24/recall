from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

from recall.errors import NoDueCardsError
from recall.repository import load_deck, sidecar_path
from recall.scheduler.sm2 import SM2Scheduler
from recall.sidecar import load_sidecar


def run(
    repo_root: Path,
    deck: str,
    limit: int = 1,
    show_answer: bool = False,
    output_format: str = "text",
    shuffle: bool = False,
    today: date | None = None,
) -> str:
    today = today or date.today()
    scheduler = SM2Scheduler()
    deck_data = load_deck(repo_root, deck)
    sidecar = load_sidecar(sidecar_path(repo_root, deck), deck_name=deck)

    due_cards: list[dict[str, object]] = []
    for card in deck_data.cards:
        state = sidecar["cards"].get(card.card_id, scheduler.new_card(today))
        if scheduler.is_due(state, today):
            item = {
                "card_id": card.card_id,
                "question": card.question,
                "source": {"path": str(card.source_path.relative_to(repo_root)), "line": card.source_line},
                "state": state.to_dict(),
            }
            if show_answer:
                item["answer"] = card.answer
            due_cards.append(item)

    if shuffle:
        random.Random().shuffle(due_cards)
    due_cards = due_cards[:limit]

    if not due_cards:
        raise NoDueCardsError(deck)

    if output_format == "json":
        return json.dumps({"deck": deck, "cards": due_cards}, sort_keys=True)

    lines: list[str] = []
    for item in due_cards:
        lines.append(f"[{item['card_id']}]")
        lines.append(str(item["question"]))
        if show_answer:
            lines.append(str(item["answer"]))
    return "\n".join(lines)
