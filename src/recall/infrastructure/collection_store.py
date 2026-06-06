from __future__ import annotations

from pathlib import Path, PurePosixPath

from recall.domain.entities import (
    Card,
    Collection,
    CollectionDetails,
    CollectionListItem,
)
from recall.domain.errors import InvalidArgumentsError
from recall.infrastructure.config_store import CollectionConfig, load_config
from recall.infrastructure.deck_store import _parse_loaded_deck


class CollectionNotFoundError(InvalidArgumentsError):
    def __init__(self, collection: str) -> None:
        super().__init__(f"Collection not found: {collection}")


def collection_sidecar_path(repo_root: Path, collection_name: str) -> Path:
    return repo_root / ".recall" / "collections" / f"{collection_name}.flashcards.json"


def _resolve_collection_files(
    repo_root: Path, include: list[str], exclude: list[str]
) -> list[Path]:
    matched: dict[str, Path] = {}
    for pattern in include:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file():
                relative = path.relative_to(repo_root).as_posix()
                matched[relative] = path

    if exclude:
        matched = {
            relative: path
            for relative, path in matched.items()
            if not any(PurePosixPath(relative).match(pattern) for pattern in exclude)
        }

    return [matched[key] for key in sorted(matched)]


def _collection_config(repo_root: Path, collection_name: str) -> CollectionConfig:
    config = load_config(repo_root)
    collection = config.collections.get(collection_name)
    if collection is None:
        raise CollectionNotFoundError(collection_name)
    return collection


def load_collection(repo_root: Path, collection_name: str) -> Collection:
    config = load_config(repo_root)
    collection_config = _collection_config(repo_root, collection_name)
    files = _resolve_collection_files(
        repo_root, collection_config.include, collection_config.exclude
    )
    cards: list[Card] = []
    for path in files:
        parsed = _parse_loaded_deck(path, path.stem, config)
        cards.extend(parsed.cards)
    return Collection(
        name=collection_name,
        include=list(collection_config.include),
        exclude=list(collection_config.exclude),
        files=files,
        cards=cards,
    )


def list_collections(repo_root: Path) -> list[CollectionListItem]:
    config = load_config(repo_root)
    results: list[CollectionListItem] = []
    for name in sorted(config.collections):
        collection = config.collections[name]
        files = _resolve_collection_files(repo_root, collection.include, collection.exclude)
        results.append(
            CollectionListItem(
                name=name,
                include=list(collection.include),
                exclude=list(collection.exclude),
                file_count=len(files),
            )
        )
    return results


def get_collection_details(repo_root: Path, collection_name: str) -> CollectionDetails:
    collection = _collection_config(repo_root, collection_name)
    files = _resolve_collection_files(repo_root, collection.include, collection.exclude)
    return CollectionDetails(
        name=collection_name,
        include=list(collection.include),
        exclude=list(collection.exclude),
        files=files,
    )
