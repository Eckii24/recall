from __future__ import annotations

from pathlib import Path

from recall.domain.entities import CollectionDetails, CollectionListItem
from recall.infrastructure.collection_store import get_collection_details, list_collections


def list_collection_items(base_path: Path) -> list[CollectionListItem]:
    return list_collections(base_path)


def show_collection(base_path: Path, name: str) -> CollectionDetails:
    return get_collection_details(base_path, name)
