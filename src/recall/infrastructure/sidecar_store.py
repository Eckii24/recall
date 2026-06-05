from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import SupportsFloat, SupportsInt, TypedDict, cast

from recall.domain.scheduler.base import CardState

SCHEMA_VERSION = 1


class SidecarData(TypedDict):
    version: int
    deck: str
    cards: dict[str, CardState]


def create_empty_sidecar(deck_name: str) -> SidecarData:
    return {"version": SCHEMA_VERSION, "deck": deck_name, "cards": {}}


def _card_state_from_dict(payload: dict[str, object]) -> CardState:
    return CardState(
        due=date.fromisoformat(str(payload["due"])),
        ease=float(cast(SupportsFloat, payload["ease"])),
        interval=int(cast(SupportsInt, payload["interval"])),
        reps=int(cast(SupportsInt, payload["reps"])),
    )


def _serialize(sidecar: SidecarData) -> dict[str, object]:
    return {
        "version": sidecar["version"],
        "deck": sidecar["deck"],
        "cards": {
            card_id: state.to_dict() for card_id, state in sidecar["cards"].items()
        },
    }


def load_sidecar(path: Path, deck_name: str | None = None) -> SidecarData:
    if not path.exists():
        if deck_name is None:
            raise FileNotFoundError(path)
        return create_empty_sidecar(deck_name)

    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_cards = payload.get("cards", {})
    if not isinstance(raw_cards, dict):
        raw_cards = {}
    cards = {
        card_id: _card_state_from_dict(state)
        for card_id, state in raw_cards.items()
        if isinstance(state, dict)
    }
    return {
        "version": int(payload["version"]),
        "deck": str(payload["deck"]),
        "cards": cards,
    }


def save_sidecar(path: Path, sidecar: SidecarData) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(_serialize(sidecar), indent=2, sort_keys=True) + "\n"
    with tmp_path.open("w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, path)
