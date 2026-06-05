from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

from recall.domain.errors import InvalidConfigError

CONFIG_FILE_NAME = "recall.config.json"


@dataclass(slots=True)
class Config:
    version: int = 1
    decks_dir: str = "decks"
    default_auto_mode: bool = False
    default_min_heading_level: int = 2
    sidecar_suffix: str = ".flashcards.json"
    scheduler: str = "sm2"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def config_path(base_path: Path | None = None) -> Path:
    return (base_path or Path.cwd()) / CONFIG_FILE_NAME


def validate_config(raw: object) -> Config:
    if not isinstance(raw, dict):
        raise InvalidConfigError()

    config = Config()
    merged = config.to_dict()
    merged.update(cast(dict[str, Any], raw))

    if merged.get("version") != 1:
        raise InvalidConfigError()
    if not isinstance(merged.get("decks_dir"), str) or not merged["decks_dir"]:
        raise InvalidConfigError()
    if not isinstance(merged.get("default_auto_mode"), bool):
        raise InvalidConfigError()
    if not isinstance(merged.get("default_min_heading_level"), int):
        raise InvalidConfigError()
    if (
        not isinstance(merged.get("sidecar_suffix"), str)
        or not merged["sidecar_suffix"]
    ):
        raise InvalidConfigError()
    if not isinstance(merged.get("scheduler"), str) or not merged["scheduler"]:
        raise InvalidConfigError()

    return Config(**merged)


def load_config(base_path: Path | None = None) -> Config:
    path = config_path(base_path)
    if not path.exists():
        return Config()

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise InvalidConfigError() from exc

    return validate_config(raw)


def write_config(config: Config, base_path: Path | None = None) -> Path:
    path = config_path(base_path)
    path.write_text(json.dumps(config.to_dict(), indent=2) + "\n")
    return path
