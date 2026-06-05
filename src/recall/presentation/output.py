from __future__ import annotations

import json
from typing import Any

import typer


def emit(payload: Any, *, output_format: str = "text") -> None:
    if output_format == "json":
        typer.echo(json.dumps(payload, indent=2, sort_keys=False))
        return

    if isinstance(payload, str):
        typer.echo(payload)
        return

    raise TypeError("Text output requires a string payload")


def emit_error(message: str) -> None:
    typer.echo(message, err=True)
