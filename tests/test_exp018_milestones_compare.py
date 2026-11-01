"""Milestone comparison must not treat pixel motion as level completion."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_exp018_milestones import compare, session_map


def row(game, seed, max_levels, milestones, model_calls=5):
    return dict(game=game, seed=seed, max_levels=max_levels,
                level_completion_actions=milestones, actions=30, model_calls=model_calls,
                wallclock_seconds=1.0, controller_seed_varied=True)


def fixture(*rows):
    return {"summary": {"controller_seed_varied": True, "sessions": len(rows)}, "games": list(rows)}


class MilestoneComparisonTest(unittest.TestCase):
    def test_matched_earlier_and_later(self):
        baseline = fixture(row("a", 0, 1, [12]), row("b", 0, 1, [9]))
        trial = fixture(row("a", 0, 1, [8]), row("b", 0, 1, [13]))
        comparison = compare(baseline, trial)
        self.assertEqual(comparison["matched_level_milestones"], 2)
        self.assertEqual(comparison["milestones_earlier"], 1)
        self.assertEqual(comparison["milestones_later"], 1)

    def test_level_regression_not_mislabeled_as_action_gain(self):
        baseline = fixture(row("a", 0, 1, [12]))
        trial = fixture(row("a", 0, 0, []))
        comparison = compare(baseline, trial)
        self.assertEqual(comparison["paired_session_regressions"], 1)
        self.assertEqual(comparison["matched_level_milestones"], 0)

    def test_missing_pair_and_fake_milestone_rejected(self):
        baseline = fixture(row("a", 0, 1, [12]))
        with self.assertRaises(ValueError):
            compare(baseline, fixture(row("a", 1, 1, [9])))
        with self.assertRaises(ValueError):
            session_map(fixture(row("a", 0, 0, [3])))
        with self.assertRaises(ValueError):
            session_map(fixture(row("a", 0, 1, [31])))
        with self.assertRaises(ValueError):
            session_map(fixture(row("a", 0, 1, [2]), row("a", 0, 1, [2])))


if __name__ == "__main__":
    unittest.main()
