"""EXP-016 ablation: perceptual similarity is not level progress."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from arc_agent.coarse_exploration import coarse_state_key
from build_exp016_variant import build_variant


class CoarseExplorationTests(unittest.TestCase):
    def test_deterministic_and_empty(self):
        board = [[0] * 8 for _ in range(8)]
        self.assertEqual(coarse_state_key([board]), coarse_state_key([board]))
        self.assertNotEqual(coarse_state_key([]), coarse_state_key([board]))

    def test_animation_uses_final_board(self):
        first = [[1, 1], [1, 1]]
        final = [[1, 0], [1, 0]]
        self.assertEqual(coarse_state_key([first, final]), coarse_state_key([final]))

    def test_coarse_key_deliberately_merges_small_motion(self):
        a, b = [[0] * 16 for _ in range(16)], [[0] * 16 for _ in range(16)]
        a[0][0], b[1][1] = 1, 1
        self.assertEqual(coarse_state_key([a], bins=2), coarse_state_key([b], bins=2))
        self.assertNotEqual(a, b)

    def test_distinguishes_larger_changes(self):
        a, b = [[0] * 16 for _ in range(16)], [[0] * 16 for _ in range(16)]
        for y in range(6):
            for x in range(6):
                b[y][x] = 1
        self.assertNotEqual(coarse_state_key([a], bins=4), coarse_state_key([b], bins=4))

    def test_invalid_parameters_and_shape(self):
        for bad in [0, 9, True]:
            with self.assertRaises(ValueError):
                coarse_state_key([[[0]]], bins=bad)
        with self.assertRaises(ValueError):
            coarse_state_key([[[0], [0, 0]]])
        with self.assertRaises(ValueError):
            build_variant(quantum=33)

    def test_standalone_compiles_exact_feedback_unchanged(self):
        generated = build_variant(bins=2)
        compile(generated, "<exp016-standalone>", "exec")
        self.assertIn("exploration_key", generated)
        self.assertIn("self._feedback.observe(frame=settled_frame", generated)
        self.assertIn("fingerprint=fingerprint),", generated)


if __name__ == "__main__":
    unittest.main()
