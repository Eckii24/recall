from __future__ import annotations

import json

from typer.testing import CliRunner

from recall.presentation.cli import app
from recall.presentation.exit_codes import ExitCode

runner = CliRunner()


def test_init_creates_default_project_structure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == ExitCode.OK
    assert (tmp_path / "decks").is_dir()
    config_path = tmp_path / "recall.config.json"
    assert config_path.is_file()
    assert json.loads(config_path.read_text()) == {
        "version": 1,
        "decks_dir": "decks",
        "default_auto_mode": False,
        "default_min_heading_level": 2,
        "sidecar_suffix": ".flashcards.json",
        "scheduler": "sm2",
    }


def test_init_supports_custom_decks_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "--decks-dir", "notes"])

    assert result.exit_code == ExitCode.OK
    assert (tmp_path / "notes").is_dir()
    assert (
        json.loads((tmp_path / "recall.config.json").read_text())["decks_dir"]
        == "notes"
    )


def test_init_rejects_invalid_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "recall.config.json").write_text("not-json")

    result = runner.invoke(app, ["init"])

    assert result.exit_code == ExitCode.INVALID_CONFIG
    assert "Invalid configuration" in result.stderr
