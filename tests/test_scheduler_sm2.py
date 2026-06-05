import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recall.scheduler.base import CardState
from recall.scheduler.sm2 import SM2Scheduler, rating_to_quality


class SM2SchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = SM2Scheduler()
        self.today = date(2026, 6, 5)

    def test_new_card_state_is_due_today(self) -> None:
        state = self.scheduler.new_card(self.today)
        self.assertEqual(state, CardState(due=self.today, ease=2.5, interval=0, reps=0))

    def test_rating_mapping_matches_prd(self) -> None:
        self.assertEqual(rating_to_quality("again"), 0)
        self.assertEqual(rating_to_quality("hard"), 2)
        self.assertEqual(rating_to_quality("good"), 3)
        self.assertEqual(rating_to_quality("easy"), 5)

    def test_is_due_checks_calendar_day(self) -> None:
        self.assertTrue(self.scheduler.is_due(CardState(due=self.today, ease=2.5, interval=0, reps=0), self.today))
        self.assertFalse(self.scheduler.is_due(CardState(due=date(2026, 6, 6), ease=2.5, interval=0, reps=0), self.today))

    def test_review_good_on_new_card_advances_interval(self) -> None:
        new_state = self.scheduler.review(
            CardState(due=self.today, ease=2.5, interval=0, reps=0),
            "good",
            self.today,
        )
        self.assertEqual(new_state, CardState(due=date(2026, 6, 6), ease=2.36, interval=1, reps=1))

    def test_review_again_resets_reps_and_due_to_tomorrow(self) -> None:
        state = CardState(due=self.today, ease=2.5, interval=6, reps=2)
        reviewed = self.scheduler.review(state, "again", self.today)
        self.assertEqual(reviewed, CardState(due=date(2026, 6, 6), ease=1.7, interval=1, reps=0))


if __name__ == "__main__":
    unittest.main()
