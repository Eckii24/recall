import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recall.sidecar import SCHEMA_VERSION, create_empty_sidecar, load_sidecar, save_sidecar
from recall.scheduler.base import CardState


class SidecarPersistenceTests(unittest.TestCase):
    def test_save_and_load_sidecar_uses_stable_pretty_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "architecture.flashcards.json"
            sidecar = {
                "version": SCHEMA_VERSION,
                "deck": "architecture",
                "cards": {
                    "architecture-cqrs": CardState(
                        due=date(2026, 6, 6),
                        ease=2.36,
                        interval=1,
                        reps=1,
                    ),
                },
            }

            save_sidecar(path, sidecar)
            raw = path.read_text(encoding="utf-8")

            self.assertTrue(raw.endswith("\n"))
            self.assertIn('  "cards": {\n    "architecture-cqrs": {\n      "due": "2026-06-06",\n      "ease": 2.36,\n      "interval": 1,\n      "reps": 1\n    }\n  },', raw)
            loaded = load_sidecar(path)
            self.assertEqual(loaded["deck"], "architecture")
            self.assertEqual(loaded["cards"]["architecture-cqrs"], sidecar["cards"]["architecture-cqrs"])

    def test_save_sidecar_is_atomic_and_does_not_leave_tmp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "architecture.flashcards.json"
            save_sidecar(path, create_empty_sidecar("architecture"))

            save_sidecar(
                path,
                {
                    "version": SCHEMA_VERSION,
                    "deck": "architecture",
                    "cards": {
                        "a": CardState(due=date(2026, 6, 5), ease=2.5, interval=0, reps=0)
                    },
                },
            )

            self.assertFalse(path.with_suffix(path.suffix + ".tmp").exists())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["deck"], "architecture")

    def test_load_sidecar_returns_empty_structure_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "architecture.flashcards.json"

            loaded = load_sidecar(path, deck_name="architecture")

            self.assertEqual(loaded, create_empty_sidecar("architecture"))


if __name__ == "__main__":
    unittest.main()
