from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from recall.application.learning import stats


def run(
    repo_root: Path,
    deck: str | None = None,
    output_format: str = "text",
    today: date | None = None,
) -> str:
    result = stats(repo_root=repo_root, deck=deck, today=today)
    if output_format == "json":
        return json.dumps(result.to_dict(), sort_keys=True)
    return "\n".join(f"{key}: {value}" for key, value in result.to_dict().items())
