from __future__ import annotations

from typer.testing import CliRunner

from recall.presentation.cli import app
from recall.presentation.exit_codes import ExitCode

runner = CliRunner()


def test_root_help_describes_main_scopes() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == ExitCode.OK
    assert "Markdown-based spaced repetition CLI" in result.stdout
    assert "single-file review" in result.stdout
    assert "multi-file scopes" in result.stdout
    assert "deck" in result.stdout
    assert "collection" in result.stdout
    assert "validate" in result.stdout
    assert "Show the next due cards for a deck or collection." in result.stdout


def test_collection_subtool_help_describes_commands() -> None:
    result = runner.invoke(app, ["collection", "--help"])

    assert result.exit_code == ExitCode.OK
    assert "Inspect configured collections" in result.stdout
    assert "list" in result.stdout
    assert "show" in result.stdout
    assert "resolved files and configured globs" in result.stdout


def test_next_help_describes_scope_and_options() -> None:
    result = runner.invoke(app, ["next", "--help"])

    assert result.exit_code == ExitCode.OK
    assert "Show the next due cards for a deck or collection." in result.stdout
    assert "--deck" in result.stdout
    assert "Review scope: one deck by name." in result.stdout
    assert "unless --collection is set." in result.stdout
    assert "--collection" in result.stdout
    assert "--limit" in result.stdout
    assert "Maximum number of due cards to return." in result.stdout
    assert "--show-answer" in result.stdout
    assert "--shuffle" in result.stdout
    assert "--new-only" in result.stdout


def test_deck_create_help_describes_required_argument() -> None:
    result = runner.invoke(app, ["deck", "create", "--help"])

    assert result.exit_code == ExitCode.OK
    assert "Create a new empty deck Markdown file." in result.stdout
    assert "NAME" in result.stdout
    assert "Deck name." in result.stdout
