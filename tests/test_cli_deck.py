from __future__ import annotations

import json

from typer.testing import CliRunner

from recall.cli import app
from recall.exit_codes import ExitCode

runner = CliRunner()


def test_deck_create_uses_default_config_and_creates_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["deck", "create", "architecture"])

    assert result.exit_code == ExitCode.OK
    assert (tmp_path / "decks" / "architecture.md").read_text() == "# Architecture\n"
    assert json.loads((tmp_path / "decks" / "architecture.flashcards.json").read_text()) == {
        "version": 1,
        "deck": "architecture",
        "cards": {},
    }


def test_deck_create_uses_configured_decks_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "recall.config.json").write_text(
        json.dumps(
            {
                "version": 1,
                "decks_dir": "knowledge",
                "default_auto_mode": False,
                "default_min_heading_level": 2,
                "sidecar_suffix": ".flashcards.json",
                "scheduler": "sm2",
            }
        )
    )

    result = runner.invoke(app, ["deck", "create", "python-basics"])

    assert result.exit_code == ExitCode.OK
    assert (tmp_path / "knowledge" / "python-basics.md").is_file()
    assert (tmp_path / "knowledge" / "python-basics.flashcards.json").is_file()


def test_deck_create_rejects_invalid_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["deck", "create", "bad/name"])

    assert result.exit_code == ExitCode.INVALID_ARGUMENTS
    assert "Invalid deck name" in result.stderr


def test_deck_create_returns_write_error_when_deck_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    (decks_dir / "architecture.md").write_text("# Architecture\n")
    (decks_dir / "architecture.flashcards.json").write_text('{"version": 1, "deck": "architecture", "cards": {}}')

    result = runner.invoke(app, ["deck", "create", "architecture"])

    assert result.exit_code == ExitCode.WRITE_ERROR
    assert "already exists" in result.stderr


def test_deck_list_human_output_and_json_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    (decks_dir / "zeta.md").write_text("# Zeta\n")
    (decks_dir / "alpha.md").write_text("# Alpha\n")
    (decks_dir / "alpha.flashcards.json").write_text('{"version": 1, "deck": "alpha", "cards": {"one": {}}}')
    (decks_dir / "zeta.flashcards.json").write_text('{"version": 1, "deck": "zeta", "cards": {}}')

    text_result = runner.invoke(app, ["deck", "list"])
    json_result = runner.invoke(app, ["deck", "list", "--format", "json"])

    assert text_result.exit_code == ExitCode.OK
    assert text_result.stdout.strip().splitlines() == [
        "alpha (1 cards)",
        "zeta (0 cards)",
    ]
    assert json_result.exit_code == ExitCode.OK
    assert json.loads(json_result.stdout) == {
        "decks": [
            {"name": "alpha", "path": "decks/alpha.md", "card_count": 1},
            {"name": "zeta", "path": "decks/zeta.md", "card_count": 0},
        ]
    }


def test_deck_list_returns_invalid_config_for_broken_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "recall.config.json").write_text('{"version": 1, "decks_dir": 7}')

    result = runner.invoke(app, ["deck", "list"])

    assert result.exit_code == ExitCode.INVALID_CONFIG
    assert "Invalid configuration" in result.stderr
