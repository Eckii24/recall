# recall

`recall` is a headless command-line tool for spaced repetition on top of plain Markdown files.
It keeps the source material in human-readable deck files and stores scheduling state in sidecar JSON files next to each deck.

## What it does

- uses Markdown as the source of truth for flashcards
- validates deck structure before review sessions
- normalizes missing `recall:id` comments into stable card IDs
- schedules reviews with an `sm2` scheduler
- exposes scriptable CLI commands with text and JSON output modes

## Project layout

```text
.
├── decks/
├── recall.config.json
├── src/recall/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   ├── interfaces/
│   └── cli.py
└── tests/
```

Key files:

- `decks/*.md`: Markdown deck sources
- `decks/*.flashcards.json`: per-deck review state sidecars
- `recall.config.json`: project configuration
- `src/recall/domain/`: flashcard/review entities plus Markdown parsing and normalization
- `src/recall/application/`: typed use cases for init, deck management, validation, and learning flows
- `src/recall/infrastructure/`: filesystem adapters for config, decks, and sidecar persistence
- `src/recall/interfaces/`: delivery adapters, currently the Typer CLI
- `src/recall/cli.py`: compatibility wrapper to the CLI entrypoint
- `tests/`: CLI and behavior tests

## Installation

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- Python 3.11+ available through uv

This repository includes a `.python-version` file pinned to Python 3.11 for predictable local environments.

### Clone and sync the project

```bash
git clone <repo-url>
cd recall
uv sync
```

This creates `.venv/`, installs the package in editable mode, and installs the dev tools declared in `pyproject.toml`.

### Install the CLI as a tool

If you want a globally available `recall` command from this checkout:

```bash
uv tool install .
```

If `recall` is already installed from a previous local checkout state and you want to refresh that installation in place, use:

```bash
uv tool install --reinstall .
```

You can then run:

```bash
recall --help
```

## Quick start

Initialize a project in an empty directory:

```bash
uv run recall init
```

Create a deck:

```bash
uv run recall deck create architecture
```

Example deck content:

```md
# Architecture

## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt Commands und Queries.
```

Check the deck:

```bash
uv run recall validate --deck architecture
```

Find due cards:

```bash
uv run recall next --deck architecture --show-answer
```

Record a review:

```bash
uv run recall review --deck architecture --card-id architecture-cqrs --rating good
```

Show stats:

```bash
uv run recall stats --deck architecture
```

## Deck format

A flashcard is defined by:

1. a Markdown heading
2. the `#flashcard` tag in the heading text
3. an HTML comment with `recall:id=...` directly below the heading
4. the answer content below that comment

Example:

```md
## What is CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS separates commands from queries.
```

Notes:

- card IDs must be explicit for validation to pass
- `uv run recall normalize --deck <name> --write` inserts missing IDs
- fenced code blocks are ignored as card boundaries
- deck names are constrained to lowercase letters, digits, `-`, and `_`

## Configuration

Project configuration lives in `recall.config.json`.
Current supported keys are:

- `version`: config schema version, currently `1`
- `decks_dir`: directory containing Markdown decks
- `default_auto_mode`: when `true`, headings at or below `default_min_heading_level` become cards without needing `#flashcard`
- `default_min_heading_level`: minimum heading depth used in auto mode
- `sidecar_suffix`: suffix for per-deck scheduling state files
- `scheduler`: scheduler name, currently `sm2`

Example:

```json
{
  "version": 1,
  "decks_dir": "decks",
  "default_auto_mode": false,
  "default_min_heading_level": 2,
  "sidecar_suffix": ".flashcards.json",
  "scheduler": "sm2"
}
```

## CLI commands

Main commands:

- `uv run recall init [--decks-dir <path>]`
- `uv run recall deck create <name>`
- `uv run recall deck list [--format text|json]`
- `uv run recall validate [--deck <name>] [--format text|json]`
- `uv run recall normalize --deck <name> [--write]`
- `uv run recall scan [--deck <name>] [--format text|json]`
- `uv run recall next --deck <name> [--limit N] [--show-answer] [--shuffle] [--format text|json]`
- `uv run recall review --deck <name> --card-id <id> --rating again|hard|good|easy [--format text|json]`
- `uv run recall stats [--deck <name>] [--format text|json]`

Useful machine-readable workflows:

```bash
uv run recall scan --deck architecture --format json
uv run recall next --deck architecture --format json
uv run recall stats --format json
```

## Development workflow

### Core uv commands

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run recall --help
uv tool install .
```

Astral toolchain used in this repository:

- `uv`: dependency management, locking, execution, and `uv tool install`
- `ruff`: linting and formatting
- `ty`: static type checking

### Formatting and linting

- `ruff check` handles linting
- `ruff format --check` verifies formatting without rewriting files
- `ty check` provides static type checking

If you want Ruff to rewrite code locally:

```bash
uv run ruff check --fix .
uv run ruff format .
```

## Architecture overview

At a high level the project is split into four layers:

1. `recall.domain`: core entities and Markdown-specific domain logic
2. `recall.application`: typed use cases with no CLI formatting concerns
3. `recall.infrastructure`: filesystem-backed adapters for config, decks, and sidecars
4. `recall.interfaces`: interface adapters, currently the CLI

Operational model:

- Markdown files define cards and answers
- parsing produces validated card objects
- sidecar JSON stores per-card review state
- application use cases load decks, apply scheduler logic, and return typed results
- the CLI is a thin adapter that serializes those results as text or JSON

This split is deliberate so a future terminal UI can call the same `application/*` use cases without re-implementing parsing, scheduling, or persistence rules.

## Packaging notes

This repository is configured as a standard Python package with:

- `hatchling` as the build backend
- a console script entry point: `recall`
- dev dependencies managed through uv dependency groups
- Ruff and ty installed as project dev tools
- a checked-in `.python-version` for predictable local interpreter selection

That means the following workflows are first-class and documented:

- local development with `uv sync`
- command execution through `uv run ...`
- installable CLI via `uv tool install .`

## Testing

Run the test suite:

```bash
uv run pytest
```

The existing tests exercise the CLI end-to-end, including validation, normalization, scanning, review updates, and stats output.
