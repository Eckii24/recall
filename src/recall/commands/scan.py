from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from recall.application.learning import scan


def run(
    repo_root: Path,
    deck: str | None = None,
    output_format: str = "text",
    today: date | None = None,
) -> str:
    result = scan(repo_root=repo_root, deck=deck, today=today)
    if output_format == "json":
        return json.dumps(result.to_dict(), sort_keys=True)
    return (
        f"Scanned {result.decks_scanned} decks, "
        f"{result.cards_total} cards, {result.cards_due} due."
    )
