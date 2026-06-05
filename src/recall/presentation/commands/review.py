from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import cast

from recall.application.learning import review_card
from recall.domain.scheduler.base import Rating


def run(
    repo_root: Path,
    deck: str,
    card_id: str,
    rating: str,
    output_format: str = "text",
    today: date | None = None,
) -> str:
    result = review_card(
        repo_root=repo_root,
        deck=deck,
        card_id=card_id,
        rating=cast(Rating, rating),
        today=today,
    )
    if output_format == "json":
        return json.dumps(result.to_dict(), sort_keys=True)
    return f"Reviewed {result.card_id}: {result.rating}"
