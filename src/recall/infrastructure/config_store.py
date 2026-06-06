from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from recall.domain.errors import InvalidConfigError

CONFIG_FILE_NAME = "recall.config.json"


@dataclass(slots=True)
class CollectionConfig:
    include: list[str]
    exclude: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Config:
    version: int = 1
    decks_dir: str = "decks"
    default_auto_mode: bool = False
    default_min_heading_level: int = 2
    sidecar_suffix: str = ".flashcards.json"
    scheduler: str = "sm2"
    collections: dict[str, CollectionConfig] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        collections = {
            name: collection.to_dict()
            for name, collection in sorted(self.collections.items())
        }
        if collections:
            payload["collections"] = collections
        else:
            payload.pop("collections", None)
        return payload


def config_path(base_path: Path | None = None) -> Path:
    return (base_path or Path.cwd()) / CONFIG_FILE_NAME


def _validate_string_list(values: object, field_name: str) -> list[str]:
    if not isinstance(values, list) or not values or not all(
        isinstance(value, str) and value for value in values
    ):
        raise InvalidConfigError(f"Invalid configuration: {field_name} must be a non-empty list of strings")
    return list(values)


def _validate_optional_string_list(values: object, field_name: str) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value for value in values
    ):
        raise InvalidConfigError(f"Invalid configuration: {field_name} must be a list of strings")
    return list(values)


def _validate_collections(raw: object) -> dict[str, CollectionConfig]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise InvalidConfigError("Invalid configuration: collections must be an object")

    collections: dict[str, CollectionConfig] = {}
    for name, payload in raw.items():
        if not isinstance(name, str) or not name:
            raise InvalidConfigError("Invalid configuration: collection names must be non-empty strings")
        if not isinstance(payload, dict):
            raise InvalidConfigError(
                f"Invalid configuration: collection {name} must be an object"
            )
        include = _validate_string_list(payload.get("include"), "include")
        exclude = _validate_optional_string_list(payload.get("exclude"), "exclude")
        collections[name] = CollectionConfig(include=include, exclude=exclude)
    return collections


def validate_config(raw: object) -> Config:
    if not isinstance(raw, dict):
        raise InvalidConfigError()

    config = Config()
    merged = config.to_dict()
    merged.update(cast(dict[str, Any], raw))

    version = merged.get("version")
    if version not in {1, 2}:
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

    collections = _validate_collections(merged.get("collections"))
    if collections and version != 2:
        raise InvalidConfigError(
            "Invalid configuration: collections require version 2"
        )

    return Config(
        version=version,
        decks_dir=str(merged["decks_dir"]),
        default_auto_mode=bool(merged["default_auto_mode"]),
        default_min_heading_level=int(merged["default_min_heading_level"]),
        sidecar_suffix=str(merged["sidecar_suffix"]),
        scheduler=str(merged["scheduler"]),
        collections=collections,
    )


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
