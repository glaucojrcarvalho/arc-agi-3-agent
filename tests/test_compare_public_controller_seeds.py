"""Auditable paired public-only fake-policy comparison."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_public_controller_seeds import compare


def run(rows, *, randomized=True):
    return {
        "summary": {"sessions": len(rows), "controller_seed_varied": randomized},
        "games": [
            {
                "game": g, "seed": seed, "max_levels": levels, "model_calls": calls,
                "actions": 80, "wallclock_seconds": 1.5,
                "controller_seed_varied": randomized,
            }
            for g, seed, levels, calls in rows
        ],
    }


class PairedControllerComparisonTests(unittest.TestCase):
    def test_paired_sessions_and_clustered_games(self):
        old = run([("a", 0, 0, 5), ("a", 1, 1, 7), ("b", 0, 1, 8)])
        new = run([("b", 0, 0, 3), ("a", 1, 1, 5), ("a", 0, 1, 2)])
        result = compare(old, new)
        self.assertEqual(result["session_improvements"], 1)
        self.assertEqual(result["session_regressions"], 1)
        self.assertEqual(result["session_ties"], 1)
        self.assertEqual(result["games_with_net_improvement"], 1)
        self.assertEqual(result["games_with_net_regression"], 1)
        self.assertEqual(result["baseline_fake_model_calls"], 20)
        self.assertEqual(result["candidate_fake_model_calls"], 10)
        self.assertEqual(result["fake_model_call_reduction_percent"], 50.0)

    def test_rejects_mismatched_seeds(self):
        with self.assertRaisesRegex(ValueError, "unpaired"):
            compare(run([("a", 0, 0, 1)]), run([("a", 1, 0, 1)]))

    def test_rejects_fake_independence_and_duplicates(self):
        with self.assertRaisesRegex(ValueError, "randomized-controller"):
            compare(run([("a", 0, 0, 1)], randomized=False), run([("a", 0, 0, 1)]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare(run([("a", 0, 0, 1), ("a", 0, 0, 1)]),
                    run([("a", 0, 0, 1)]))


class PublicActionMilestoneComparisonTests(unittest.TestCase):
    def test_detects_action_efficiency_with_equal_level_counts(self):
        baseline = run([("a", 0, 1, 7), ("b", 0, 1, 7), ("c", 0, 0, 7)])
        candidate = run([("a", 0, 1, 5), ("b", 0, 1, 5), ("c", 0, 0, 5)])
        for row in baseline["games"]:
            row["level_completion_action_indices"] = (
                [20] if row["game"] == "a" else [30] if row["game"] == "b" else []
            )
        for row in candidate["games"]:
            row["level_completion_action_indices"] = (
                [16] if row["game"] == "a" else [35] if row["game"] == "b" else []
            )
        metric = compare(baseline, candidate)["first_level_action_efficiency"]
        self.assertEqual(metric["paired_sessions_with_first_level"], 2)
        self.assertEqual(metric["candidate_faster"], 1)
        self.assertEqual(metric["candidate_slower"], 1)
        self.assertEqual(metric["baseline_sum_first_level_action_index"], 50)
        self.assertEqual(metric["candidate_sum_first_level_action_index"], 51)

    def test_rejects_mismatched_or_invalid_milestones(self):
        baseline = run([("a", 0, 1, 7)])
        candidate = run([("a", 0, 1, 7)])
        baseline["games"][0]["level_completion_action_indices"] = [5]
        with self.assertRaisesRegex(ValueError, "mixed milestone"):
            compare(baseline, candidate)
        candidate["games"][0]["level_completion_action_indices"] = [0]
        with self.assertRaisesRegex(ValueError, "invalid action milestones"):
            compare(baseline, candidate)


if __name__ == "__main__":
    unittest.main()
