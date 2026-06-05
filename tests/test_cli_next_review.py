import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recall.commands.next import run as next_run
from recall.commands.review import run as review_run
from recall.commands.scan import run as scan_run
from recall.commands.stats import run as stats_run
from recall.scheduler.base import CardState
from recall.sidecar import save_sidecar

DECK_CONTENT = """# Architecture

## Was ist CQRS? #flashcard
<!-- recall:id=architecture-cqrs -->

CQRS trennt das Command-/Write-Modell vom Query-/Read-Modell.

## Was ist Event Sourcing? #flashcard
<!-- recall:id=architecture-event-sourcing -->

Event Sourcing speichert Zustandsänderungen als Event-Log.
"""


class CLINextReviewStatsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmpdir.name)
        decks_dir = self.repo / "decks"
        decks_dir.mkdir()
        (decks_dir / "architecture.md").write_text(DECK_CONTENT, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_scan_creates_missing_sidecar_and_reports_json(self) -> None:
        result = scan_run(
            repo_root=self.repo,
            deck="architecture",
            output_format="json",
            today=date(2026, 6, 5),
        )

        payload = json.loads(result)
        self.assertEqual(
            payload,
            {
                "cards_due": 2,
                "cards_total": 2,
                "decks_scanned": 1,
                "errors": [],
            },
        )
        sidecar_path = self.repo / "decks" / "architecture.flashcards.json"
        self.assertTrue(sidecar_path.exists())
        saved = json.loads(sidecar_path.read_text(encoding="utf-8"))
        self.assertEqual(saved, {"cards": {}, "deck": "architecture", "version": 1})

    def test_next_returns_due_cards_in_file_order_and_can_show_answer(self) -> None:
        save_sidecar(
            self.repo / "decks" / "architecture.flashcards.json",
            {
                "version": 1,
                "deck": "architecture",
                "cards": {
                    "architecture-cqrs": CardState(
                        due=date(2026, 6, 5), ease=2.5, interval=0, reps=0
                    ),
                    "architecture-event-sourcing": CardState(
                        due=date(2026, 6, 7), ease=2.5, interval=0, reps=0
                    ),
                },
            },
        )

        result = next_run(
            repo_root=self.repo,
            deck="architecture",
            limit=5,
            show_answer=True,
            output_format="json",
            shuffle=False,
            today=date(2026, 6, 5),
        )

        payload = json.loads(result)
        self.assertEqual(payload["deck"], "architecture")
        self.assertEqual(len(payload["cards"]), 1)
        self.assertEqual(payload["cards"][0]["card_id"], "architecture-cqrs")
        self.assertIn("answer", payload["cards"][0])
        self.assertEqual(payload["cards"][0]["state"]["due"], "2026-06-05")

    def test_review_updates_sidecar_and_returns_old_and_new_state(self) -> None:
        save_sidecar(
            self.repo / "decks" / "architecture.flashcards.json",
            {
                "version": 1,
                "deck": "architecture",
                "cards": {
                    "architecture-cqrs": CardState(
                        due=date(2026, 6, 5), ease=2.5, interval=0, reps=0
                    ),
                },
            },
        )

        result = review_run(
            repo_root=self.repo,
            deck="architecture",
            card_id="architecture-cqrs",
            rating="good",
            output_format="json",
            today=date(2026, 6, 5),
        )

        payload = json.loads(result)
        self.assertEqual(
            payload["old_state"],
            {"due": "2026-06-05", "ease": 2.5, "interval": 0, "reps": 0},
        )
        self.assertEqual(
            payload["new_state"],
            {"due": "2026-06-06", "ease": 2.36, "interval": 1, "reps": 1},
        )
        updated = json.loads(
            (self.repo / "decks" / "architecture.flashcards.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(updated["cards"]["architecture-cqrs"], payload["new_state"])

    def test_stats_supports_global_and_per_deck_json(self) -> None:
        (self.repo / "decks" / "systems.md").write_text(
            "# Systems\n\n"
            "## Was ist RAID? #flashcard\n"
            "<!-- recall:id=systems-raid -->\n\n"
            "Eine Speichertechnik.\n",
            encoding="utf-8",
        )
        save_sidecar(
            self.repo / "decks" / "architecture.flashcards.json",
            {
                "version": 1,
                "deck": "architecture",
                "cards": {
                    "architecture-cqrs": CardState(
                        due=date(2026, 6, 5), ease=2.5, interval=0, reps=0
                    ),
                    "architecture-event-sourcing": CardState(
                        due=date(2026, 6, 10), ease=2.4, interval=10, reps=2
                    ),
                },
            },
        )
        save_sidecar(
            self.repo / "decks" / "systems.flashcards.json",
            {
                "version": 1,
                "deck": "systems",
                "cards": {
                    "systems-raid": CardState(
                        due=date(2026, 6, 4), ease=2.6, interval=25, reps=4
                    ),
                },
            },
        )

        deck_payload = json.loads(
            stats_run(
                repo_root=self.repo,
                deck="architecture",
                output_format="json",
                today=date(2026, 6, 5),
            )
        )
        self.assertEqual(
            deck_payload,
            {
                "cards_total": 2,
                "deck": "architecture",
                "due_today": 1,
                "mature": 0,
                "new": 1,
                "young": 1,
            },
        )

        global_payload = json.loads(
            stats_run(
                repo_root=self.repo,
                deck=None,
                output_format="json",
                today=date(2026, 6, 5),
            )
        )
        self.assertEqual(
            global_payload,
            {
                "cards_total": 3,
                "decks": 2,
                "due_today": 2,
                "mature": 1,
                "new": 1,
                "young": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
