from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import Any, Callable, ParamSpec, TypeVar

import typer

from recall.commands.deck import create_deck, list_decks
from recall.commands.init import initialize_project
from recall.commands.next import run as next_run
from recall.commands.normalize import normalize_deck
from recall.commands.review import run as review_run
from recall.commands.scan import run as scan_run
from recall.commands.stats import run as stats_run
from recall.commands.validate import validate_decks
from recall.errors import InvalidCardFormatError, RecallError
from recall.exit_codes import ExitCode
from recall.output import emit, emit_error

app = typer.Typer(help="Headless markdown spaced repetition CLI")
deck_app = typer.Typer(help="Deck management commands")
app.add_typer(deck_app, name="deck")

P = ParamSpec("P")
T = TypeVar("T")


class OutputFormat(str):
    TEXT = "text"
    JSON = "json"


class Rating(str):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


def command_handler(func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except RecallError as exc:
            emit_error(str(exc))
            raise typer.Exit(code=int(exc.exit_code)) from exc

    return wrapper


def _emit_serialized(result: str, output_format: str) -> None:
    if output_format == OutputFormat.JSON:
        typer.echo(result)
    else:
        emit(result)


@app.command("init")
@command_handler
def init_command(decks_dir: str = typer.Option(None, "--decks-dir")) -> None:
    config = initialize_project(decks_dir=decks_dir)
    emit(f"Initialized recall project in ./{config.decks_dir}")


@deck_app.command("create")
@command_handler
def deck_create_command(name: str) -> None:
    create_deck(name)
    emit(f"Created deck {name}")


@deck_app.command("list")
@command_handler
def deck_list_command(output_format: str = typer.Option(OutputFormat.TEXT, "--format")) -> None:
    decks = list_decks()
    if output_format == OutputFormat.JSON:
        emit({"decks": decks}, output_format="json")
        return

    lines = [f"{deck['name']} ({deck['card_count']} cards)" for deck in decks]
    emit("\n".join(lines))


@app.command("validate")
@command_handler
def validate_command(
    deck: str | None = typer.Option(None, "--deck"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    root = Path.cwd()
    summary = validate_decks(root=root, deck=deck)
    assert not isinstance(summary, str)

    if output_format == OutputFormat.JSON:
        typer.echo(validate_decks(root=root, deck=deck, output_format="json"))
    else:
        for result in summary.decks:
            if result.ok:
                emit(
                    f"Deck {result.name} valid.\nCards: {len(result.cards)}\nErrors: {len(result.issues)}\nWarnings: {len(result.warnings)}"
                )
            else:
                issues = "\n".join(f"- {issue.code}: {issue.message}" for issue in result.issues)
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
        emit(f"{action} {len(result.added_ids)} ids for deck {deck}: {', '.join(result.added_ids)}")
    else:
        emit(f"No changes needed for deck {deck}")


@app.command("scan")
@command_handler
def scan_command(
    deck: str | None = typer.Option(None, "--deck"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    result = scan_run(repo_root=Path.cwd(), deck=deck, output_format=output_format)
    _emit_serialized(result, output_format)


@app.command("next")
@command_handler
def next_command(
    deck: str = typer.Option(..., "--deck"),
    limit: int = typer.Option(1, "--limit"),
    show_answer: bool = typer.Option(False, "--show-answer"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
    shuffle: bool = typer.Option(False, "--shuffle"),
) -> None:
    result = next_run(
        repo_root=Path.cwd(),
        deck=deck,
        limit=limit,
        show_answer=show_answer,
        output_format=output_format,
        shuffle=shuffle,
    )
    _emit_serialized(result, output_format)


@app.command("review")
@command_handler
def review_command(
    deck: str = typer.Option(..., "--deck"),
    card_id: str = typer.Option(..., "--card-id"),
    rating: str = typer.Option(..., "--rating"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    if rating not in {Rating.AGAIN, Rating.HARD, Rating.GOOD, Rating.EASY}:
        from recall.errors import InvalidArgumentsError

        raise InvalidArgumentsError(f"Invalid rating: {rating}")
    result = review_run(repo_root=Path.cwd(), deck=deck, card_id=card_id, rating=rating, output_format=output_format)
    _emit_serialized(result, output_format)


@app.command("stats")
@command_handler
def stats_command(
    deck: str | None = typer.Option(None, "--deck"),
    output_format: str = typer.Option(OutputFormat.TEXT, "--format"),
) -> None:
    result = stats_run(repo_root=Path.cwd(), deck=deck, output_format=output_format)
    _emit_serialized(result, output_format)


def main() -> int:
    app()
    return int(ExitCode.OK)


if __name__ == "__main__":
    raise SystemExit(main())
