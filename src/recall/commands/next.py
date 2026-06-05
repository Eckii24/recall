from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from recall.application.learning import next_cards


def run(
    repo_root: Path,
    deck: str,
    limit: int = 1,
    show_answer: bool = False,
    output_format: str = "text",
    shuffle: bool = False,
    today: date | None = None,
) -> str:
    result = next_cards(
        repo_root=repo_root,
        deck=deck,
        limit=limit,
        show_answer=show_answer,
        shuffle=shuffle,
        today=today,
    )
    if output_format == "json":
        return json.dumps(result.to_dict(), sort_keys=True)

    lines: list[str] = []
    for item in result.cards:
        lines.append(f"[{item.card_id}]")
        lines.append(item.question)
        if show_answer and item.answer is not None:
            lines.append(item.answer)
    return "\n".join(lines)
