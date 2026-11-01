"""Public experiment guardrails: valid thresholds and authoritative milestones."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from build_exp018_variant import build_variant  # noqa: E402
from smoke_exp005_public_offline import record_level_milestones  # noqa: E402


class Exp018BuilderTests(unittest.TestCase):
    def test_both_thresholds_change_without_touching_model_or_policy(self):
        agent = build_variant(complex_after=4, keyboard_after=8)
        compile(agent, "exp018-early", "exec")
        self.assertIn("COMPLEX_NOVELTY_AFTER = 4", agent)
        self.assertIn("KEYBOARD_NOVELTY_AFTER = 8", agent)
        self.assertIn("model-free-state-novelty-exploration", agent)

    def test_invalid_threshold_rejected(self):
        for value in (0, 1, 49, True, 2.5, "4"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    build_variant(complex_after=value, keyboard_after=16)

    def test_later_threshold_builds(self):
        compile(build_variant(complex_after=12, keyboard_after=24), "late", "exec")


class MilestoneTests(unittest.TestCase):
    def test_no_false_progress_on_equal_level_or_reset(self):
        milestones = []
        seen = record_level_milestones(0, 0, 1, milestones)
        seen = record_level_milestones(seen, 1, 11, milestones)
        seen = record_level_milestones(seen, 0, 13, milestones)
        seen = record_level_milestones(seen, 1, 18, milestones)
        seen = record_level_milestones(seen, 2, 22, milestones)
        self.assertEqual(seen, 2)
        self.assertEqual(milestones, [11, 22])

    def test_level_jump_records_only_actual_counter_increments(self):
        milestones = []
        seen = record_level_milestones(0, 2, 4, milestones)
        self.assertEqual(seen, 2)
        self.assertEqual(milestones, [4, 4])

    def test_invalid_metrics_rejected(self):
        with self.assertRaises(ValueError):
            record_level_milestones(0, True, 1, [])
        with self.assertRaises(ValueError):
            record_level_milestones(-1, 0, 1, [])


if __name__ == "__main__":
    unittest.main()
