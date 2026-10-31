"""Evaluation milestones must track action efficiency, not changed pixels."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from public_level_milestones import record_milestones


class LevelMilestoneTests(unittest.TestCase):
    def test_only_actual_level_increase_creates_a_milestone(self):
        metrics = {}
        highest = record_milestones(metrics, highest_level=0, observed_level=0, action_index=1)
        self.assertEqual((highest, metrics), (0, {}))
        highest = record_milestones(metrics, highest_level=highest, observed_level=1, action_index=7)
        self.assertEqual((highest, metrics), (1, {1: 7}))
        highest = record_milestones(metrics, highest_level=highest, observed_level=1, action_index=8)
        self.assertEqual((highest, metrics), (1, {1: 7}))

    def test_reset_and_replay_cannot_overwrite_earliest_completion(self):
        metrics = {1: 7}
        highest = record_milestones(metrics, highest_level=1, observed_level=0, action_index=8)
        highest = record_milestones(metrics, highest_level=highest, observed_level=1, action_index=12)
        self.assertEqual((highest, metrics), (1, {1: 7}))

    def test_multiple_levels_completed_on_one_action(self):
        metrics = {}
        highest = record_milestones(metrics, highest_level=0, observed_level=2, action_index=12)
        self.assertEqual((highest, metrics), (2, {1: 12, 2: 12}))

    def test_invalid_metrics_rejected(self):
        for kwargs in (
            {"highest_level": -1, "observed_level": 0, "action_index": 1},
            {"highest_level": 0, "observed_level": True, "action_index": 1},
            {"highest_level": 0, "observed_level": 1, "action_index": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                record_milestones({}, **kwargs)


if __name__ == "__main__":
    unittest.main()
