from __future__ import annotations

import json
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar, cast

import typer

from recall.application.collections import list_collection_items, show_collection
from recall.application.decks import create_deck, list_decks
from recall.application.init_project import initialize_project
from recall.application.learning import next_cards, review_card, scan, stats
from recall.application.validation import normalize_deck, validate_decks
from recall.domain.entities import (
    NextCardsResult,
    ReviewResult,
    ScanResult,
    StatsResult,
    ValidationSummary,
)
from recall.domain.errors import (
    InvalidArgumentsError,
    InvalidCardFormatError,
    RecallError,
)
from recall.domain.scheduler.base import Rating
from recall.presentation.exit_codes import ExitCode
from recall.presentation.output import emit, emit_error

app = typer.Typer(name="recall", help="Headless markdown spaced repetition CLI")
deck_app = typer.Typer(help="Deck management commands")
collection_app = typer.Typer(help="Collection management commands")
app.add_typer(deck_app, name="deck")
app.add_typer(collection_app, name="collection")

P = ParamSpec("P")
T = TypeVar("T")


class OutputFormat(str):
    TEXT = "text"
    JSON = "json"


def _exit_code_for_error(error: RecallError) -> ExitCode:
    if isinstance(error, InvalidArgumentsError):
        return ExitCode.INVALID_ARGUMENTS
    if isinstance(error, InvalidCardFormatError):
        return ExitCode.INVALID_CARD_FORMAT
    from recall.domain.errors import (
        CardNotFoundError,
        DeckNotFoundError,
        InvalidConfigError,
        InvalidSidecarStateError,
        NoDueCardsError,
        WriteError,
    )

    if isinstance(error, InvalidConfigError):
        return ExitCode.INVALID_CONFIG
    if isinstance(error, DeckNotFoundError):
        return ExitCode.DECK_NOT_FOUND
    if isinstance(error, CardNotFoundError):
        return ExitCode.CARD_NOT_FOUND
    if isinstance(error, InvalidSidecarStateError):
        return ExitCode.INVALID_SIDECAR_STATE
    if isinstance(error, NoDueCardsError):
        return ExitCode.NO_DUE_CARDS
    if isinstance(error, WriteError):
        return ExitCode.WRITE_ERROR
    return ExitCode.ERROR


def command_handler(func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except RecallError as exc:
            emit_error(str(exc))
            raise typer.Exit(code=int(_exit_code_for_error(exc))) from exc

    return wrapper


def _emit_json(payload: object) -> None:
    typer.echo(json.dumps(payload, sort_keys=True))


def _resolve_scope(
    deck: str | None,
    collection: str | None,
    *,
    require_one: bool,
) -> None:
    if deck is not None and collection is not None:
        raise InvalidArgumentsError("Cannot use both --deck and --collection; choose exactly one")
    if require_one and deck is None and collection is None:
        raise InvalidArgumentsError("Exactly one of --deck or --collection is required")


def _emit_validation(summary: ValidationSummary, output_format: str) -> None:
    if output_format == OutputFormat.JSON:
        _emit_json(summary.to_dict())
        return
    if summary.collection is not None:
        result = summary.collection
        emit(
            "\n".join(
                [
                    f"Collection {result.name} {'valid' if result.ok else 'invalid'}.",
                    f"Files: {len(result.files)}",
                    f"Cards: {sum(len(item.cards) for item in result.files)}",
                    f"Errors: {sum(len(item.issues) for item in result.files)}",
                    f"Warnings: {sum(len(item.warnings) for item in result.files)}",
                ]
            )
        )
        return
    for result in summary.decks:
        if result.ok:
            emit(
                "\n".join(
                    [
                        f"Deck {result.name} valid.",
                        f"Cards: {len(result.cards)}",
                        f"Errors: {len(result.issues)}",
                        f"Warnings: {len(result.warnings)}",
                    ]
                )
            )
        else:
            issues = "\n".join(
                f"- {issue.code}: {issue.message}" for issue in result.issues
            )
            warnings = "\n".join(f"- {warning}" for warning in result.warnings)
            message = [
                f"Deck {result.name} invalid.",
                f"Cards: {len(result.cards)}",
                f"Errors: {len(result.issues)}",
                f"Warnings: {len(result.warnings)}",
            ]
            if issues:
                message.append(issues)
            if warnings:
                message.append(warnings)
            emit("\n".join(message))


def _emit_scan_result(result: ScanResult, output_format: str) -> None:
    if output_format == OutputFormat.JSON:
        _emit_json(result.to_dict())
    else:
        scope = f"collection {result.collection}" if result.collection else f"{result.decks_scanned} decks"
        emit(
            f"Scanned {scope}, {result.cards_total} cards, {result.cards_due} due."
        )


def _emit_next_result(
    result: NextCardsResult, output_format: str, show_answer: bool
) -> None:
    if output_format == OutputFormat.JSON:
        _emit_json(result.to_dict())
        return
    lines: list[str] = []
    for item in result.cards:
        lines.append(f"[{item.card_id}]")
        lines.append(item.question)
        if show_answer and item.answer is not None:
            lines.append(item.answer)
    emit("\n".join(lines))


def _emit_review_result(result: ReviewResult, output_format: str) -> None:
    if output_format == OutputFormat.JSON:
        _emit_json(result.to_dict())
    else:
        emit(f"Reviewed {result.card_id}: {result.rating}")


def _emit_stats_result(result: StatsResult, output_format: str) -> None:
    if output_format == OutputFormat.JSON:
        _emit_json(result.to_dict())
    else:
        emit("\n".join(f"{key}: {value}" for key, value in result.to_dict().items()))


@app.command("init")
@command_handler
def init_command(decks_dir: str = typer.Option(None, "--decks-dir")) -> None:
    config = initialize_project(base_path=Path.cwd(), decks_dir=decks_dir)
    emit(f"Initialized recall project in ./{config.decks_dir}")


@deck_app.command("create")
@command_handler
def deck_create_command(name: str) -> None:
    create_deck(Path.cwd(), name)
    emit(f"Created deck {name}")


@deck_app.command("list")
@command_handler
def deck_list_command(
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    decks = list_decks(Path.cwd())
    if output_format == OutputFormat.JSON:
        _emit_json({"decks": [deck.to_dict() for deck in decks]})
        return
    emit("\n".join(f"{deck.name} ({deck.card_count} cards)" for deck in decks))


@collection_app.command("list")
@command_handler
def collection_list_command(
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    collections = list_collection_items(Path.cwd())
    if output_format == OutputFormat.JSON:
        _emit_json({"collections": [item.to_dict() for item in collections]})
        return
    emit("\n".join(f"{item.name} ({item.file_count} files)" for item in collections))


@collection_app.command("show")
@command_handler
def collection_show_command(
    name: str,
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    details = show_collection(Path.cwd(), name)
    if output_format == OutputFormat.JSON:
        _emit_json({"collection": details.to_dict(Path.cwd())})
        return
    emit(
        "\n".join(
            [
                f"Collection {details.name}",
                *(path.relative_to(Path.cwd()).as_posix() for path in details.files),
            ]
        )
    )


@app.command("validate")
@command_handler
def validate_command(
    deck: str | None = typer.Option(None, "--deck"),
    collection: str | None = typer.Option(None, "--collection"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    _resolve_scope(deck, collection, require_one=False)
    summary = validate_decks(root=Path.cwd(), deck=deck, collection=collection)
    _emit_validation(summary, output_format)
    if not summary.ok:
        raise InvalidCardFormatError("Validation failed")


@app.command("normalize")
@command_handler
def normalize_command(
    deck: str = typer.Option(..., "--deck"),
    write: bool = typer.Option(False, "--write"),
) -> None:
    result = normalize_deck(root=Path.cwd(), deck=deck, write=write)
    if result.changed:
        action = "Wrote" if result.written else "Would write"
        emit(
            f"{action} {len(result.added_ids)} ids for deck {deck}: "
            f"{', '.join(result.added_ids)}"
        )
    else:
        emit(f"No changes needed for deck {deck}")


@app.command("scan")
@command_handler
def scan_command(
    deck: str | None = typer.Option(None, "--deck"),
    collection: str | None = typer.Option(None, "--collection"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    _resolve_scope(deck, collection, require_one=False)
    result = scan(repo_root=Path.cwd(), deck=deck, collection=collection)
    _emit_scan_result(result, output_format)


@app.command("next")
@command_handler
def next_command(
    deck: str | None = typer.Option(None, "--deck"),
    collection: str | None = typer.Option(None, "--collection"),
    limit: int = typer.Option(1, "--limit"),
    show_answer: bool = typer.Option(False, "--show-answer"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
    shuffle: bool = typer.Option(False, "--shuffle"),
) -> None:
    _resolve_scope(deck, collection, require_one=True)
    result = next_cards(
        repo_root=Path.cwd(),
        deck=deck,
        collection=collection,
        limit=limit,
        show_answer=show_answer,
        shuffle=shuffle,
    )
    _emit_next_result(result, output_format, show_answer)


@app.command("review")
@command_handler
def review_command(
    deck: str | None = typer.Option(None, "--deck"),
    collection: str | None = typer.Option(None, "--collection"),
    card_id: str = typer.Option(..., "--card-id"),
    rating: str = typer.Option(..., "--rating"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    _resolve_scope(deck, collection, require_one=True)
    valid_ratings = {"again", "hard", "good", "easy"}
    if rating not in valid_ratings:
        raise InvalidArgumentsError(f"Invalid rating: {rating}")
    result = review_card(
        repo_root=Path.cwd(),
        deck=deck,
        collection=collection,
        card_id=card_id,
        rating=cast(Rating, rating),
    )
    _emit_review_result(result, output_format)


@app.command("stats")
@command_handler
def stats_command(
    deck: str | None = typer.Option(None, "--deck"),
    collection: str | None = typer.Option(None, "--collection"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    _resolve_scope(deck, collection, require_one=False)
    result = stats(repo_root=Path.cwd(), deck=deck, collection=collection)
    _emit_stats_result(result, output_format)


def main() -> int:
    app()
    return int(ExitCode.OK)


if __name__ == "__main__":
    raise SystemExit(main())
