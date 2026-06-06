from __future__ import annotations

import pytest

from recall.domain.errors import InvalidConfigError
from recall.infrastructure.config_store import CollectionConfig, Config, validate_config


def test_validate_config_accepts_version_1_without_collections() -> None:
    config = validate_config({"version": 1, "decks_dir": "decks"})

    assert config == Config(version=1, decks_dir="decks")
    assert config.collections == {}


def test_validate_config_accepts_version_2_with_collections() -> None:
    config = validate_config(
        {
            "version": 2,
            "collections": {
                "chess": {
                    "include": ["chess/**/*.md"],
                    "exclude": ["**/templates/**"],
                }
            },
        }
    )

    assert config.version == 2
    assert config.collections == {
        "chess": CollectionConfig(
            include=["chess/**/*.md"], exclude=["**/templates/**"]
        )
    }


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (
            {"version": 1, "collections": {"chess": {"include": ["chess/**/*.md"]}}},
            "version 2",
        ),
        ({"version": 2, "collections": {"chess": {}}}, "include"),
        ({"version": 2, "collections": {"chess": {"include": []}}}, "include"),
        ({"version": 2, "collections": {"chess": {"include": [1]}}}, "include"),
        (
            {
                "version": 2,
                "collections": {
                    "chess": {"include": ["chess/**/*.md"], "exclude": [1]}
                },
            },
            "exclude",
        ),
    ],
)
def test_validate_config_rejects_invalid_collection_shapes(
    raw: dict, message: str
) -> None:
    with pytest.raises(InvalidConfigError, match=message):
        validate_config(raw)
