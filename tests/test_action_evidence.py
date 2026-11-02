"""EXPERIMENTAL model-prompt evidence: never treat pixel change as progress."""
from __future__ import annotations

import json
import unittest

from arc_agent.action_evidence import ActionEvidence


class ActionEvidenceTests(unittest.TestCase):
    def test_attempts_are_descriptive_not_rewards(self):
        ledger = ActionEvidence()
        ledger.observe_level(0)
        ledger.record(2, {}, width=8, height=8)
        ledger.record(2, {}, width=8, height=8)
        ledger.record(1, {}, width=8, height=8)
        result = ledger.prompt_context()
        self.assertEqual(result["attempts_this_level"], 3)
        self.assertEqual(result["control_attempts"], [
            {"action": 1, "attempts": 1},
            {"action": 2, "attempts": 2},
        ])
        self.assertEqual(result["recent_controls"], [2, 2, 1])
        self.assertIn("NOT success or failure", result["evidence_caveat"])
        self.assertIn("levels_completed", result["evidence_caveat"])

    def test_spatial_sectors_are_normalized_and_bounded(self):
        ledger = ActionEvidence(spatial_limit=2)
        ledger.observe_level(0)
        ledger.record(6, {"x": 12, "y": 2}, width=16, height=16)
        ledger.record(6, {"x": 15, "y": 3}, width=16, height=16)
        ledger.record(6, {"x": 3, "y": 15}, width=16, height=16)
        ledger.record(6, {"x": 16, "y": 15}, width=16, height=16)
        ledger.record(6, {"x": True, "y": 0}, width=16, height=16)
        regions = ledger.prompt_context()["most_attempted_click_sectors_4x4"]
        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0], {
            "action": 6, "sector_x": 3, "sector_y": 0, "attempts": 2,
        })
        self.assertNotIn("x", regions[0])  # no exact coordinates persist

    def test_progress_requires_authoritative_level_change(self):
        ledger = ActionEvidence()
        ledger.observe_level(0)
        ledger.record(1, {}, width=2, height=2)
        # Observing any number of changed frames does not affect this ledger.
        ledger.observe_level(0)
        self.assertEqual(ledger.prompt_context()["attempts_this_level"], 1)
        ledger.observe_level(1)
        self.assertEqual(ledger.prompt_context()["attempts_this_level"], 0)
        ledger.record(2, {}, width=2, height=2)
        ledger.observe_level(0)  # restart / new game
        self.assertEqual(ledger.prompt_context()["attempts_this_level"], 0)

    def test_bounded_context_for_long_sessions(self):
        ledger = ActionEvidence(recent_limit=5, spatial_limit=3)
        ledger.observe_level(0)
        for n in range(1000):
            ledger.record(n % 7, {"x": n % 64, "y": n % 64},
                          width=64, height=64)
        context = ledger.prompt_context()
        self.assertEqual(context["attempts_this_level"], 1000)
        self.assertLessEqual(len(context["recent_controls"]), 5)
        self.assertLessEqual(len(context["most_attempted_click_sectors_4x4"]), 3)
        self.assertLess(len(json.dumps(context)), 1400)

    def test_invalid_arguments_and_reset(self):
        ledger = ActionEvidence()
        with self.assertRaises(ValueError):
            ledger.observe_level(-1)
        with self.assertRaises(ValueError):
            ledger.record(True, {}, width=1, height=1)
        with self.assertRaises(ValueError):
            ledger.record(1, {}, width=0, height=1)
        with self.assertRaises(ValueError):
            ActionEvidence(recent_limit=0)
        ledger.record(1, {}, width=1, height=1)
        ledger.reset()
        self.assertEqual(ledger.prompt_context()["attempts_this_level"], 0)


if __name__ == "__main__":
    unittest.main()
