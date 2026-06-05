from __future__ import annotations

import json
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar, cast

import typer

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
from recall.errors import InvalidArgumentsError, InvalidCardFormatError, RecallError
from recall.exit_codes import ExitCode
from recall.output import emit, emit_error
from recall.scheduler.base import Rating

app = typer.Typer(help="Headless markdown spaced repetition CLI")
deck_app = typer.Typer(help="Deck management commands")
app.add_typer(deck_app, name="deck")

P = ParamSpec("P")
T = TypeVar("T")


class OutputFormat(str):
    TEXT = "text"
    JSON = "json"


def command_handler(func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except RecallError as exc:
            emit_error(str(exc))
            raise typer.Exit(code=int(exc.exit_code)) from exc

    return wrapper


def _emit_json(payload: object) -> None:
    typer.echo(json.dumps(payload, sort_keys=True))


def _emit_validation(summary: ValidationSummary, output_format: str) -> None:
    if output_format == OutputFormat.JSON:
        _emit_json(summary.to_dict())
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
        emit(
            f"Scanned {result.decks_scanned} decks, "
            f"{result.cards_total} cards, {result.cards_due} due."
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


@app.command("validate")
@command_handler
def validate_command(
    deck: str | None = typer.Option(None, "--deck"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    summary = validate_decks(root=Path.cwd(), deck=deck)
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
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    result = scan(repo_root=Path.cwd(), deck=deck)
    _emit_scan_result(result, output_format)


@app.command("next")
@command_handler
def next_command(
    deck: str = typer.Option(..., "--deck"),
    limit: int = typer.Option(1, "--limit"),
    show_answer: bool = typer.Option(False, "--show-answer"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
    shuffle: bool = typer.Option(False, "--shuffle"),
) -> None:
    result = next_cards(
        repo_root=Path.cwd(),
        deck=deck,
        limit=limit,
        show_answer=show_answer,
        shuffle=shuffle,
    )
    _emit_next_result(result, output_format, show_answer)


@app.command("review")
@command_handler
def review_command(
    deck: str = typer.Option(..., "--deck"),
    card_id: str = typer.Option(..., "--card-id"),
    rating: str = typer.Option(..., "--rating"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    valid_ratings = {"again", "hard", "good", "easy"}
    if rating not in valid_ratings:
        raise InvalidArgumentsError(f"Invalid rating: {rating}")
    result = review_card(
        repo_root=Path.cwd(),
        deck=deck,
        card_id=card_id,
        rating=cast(Rating, rating),
        today=None,
    )
    _emit_review_result(result, output_format)


@app.command("stats")
@command_handler
def stats_command(
    deck: str | None = typer.Option(None, "--deck"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    result = stats(repo_root=Path.cwd(), deck=deck)
    _emit_stats_result(result, output_format)


def main() -> int:
    app()
    return int(ExitCode.OK)


if __name__ == "__main__":
    raise SystemExit(main())
