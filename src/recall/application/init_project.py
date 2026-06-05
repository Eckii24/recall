from __future__ import annotations

from pathlib import Path

from recall.infrastructure.config_store import Config, load_config, write_config


def initialize_project(
    *, base_path: Path | None = None, decks_dir: str | None = None
) -> Config:
    project_root = base_path or Path.cwd()
    existing = load_config(project_root)
    config = Config(**existing.to_dict())
    if decks_dir is not None:
        config.decks_dir = decks_dir

    (project_root / config.decks_dir).mkdir(parents=True, exist_ok=True)
    write_config(config, project_root)
    return config
