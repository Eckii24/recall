from __future__ import annotations

import json
from pathlib import Path

from recall.application.validation import validate_decks as validate_decks_use_case


def validate_decks(
    root: str | Path, deck: str | None = None, output_format: str = "object"
):
    summary = validate_decks_use_case(root=root, deck=deck)
    if output_format == "json":
        return json.dumps(summary.to_dict())
    return summary
