"""Evaluation-only randomization must never leak into the production agent."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from smoke_exp005_public_offline import _policy_rng_seed


class EvaluationPolicySeedTests(unittest.TestCase):
    def test_deterministic_but_independent_controller_seeds(self):
        self.assertEqual(_policy_rng_seed("test-game", 1),
                         _policy_rng_seed("test-game", 1))
        self.assertNotEqual(_policy_rng_seed("test-game", 1),
                            _policy_rng_seed("test-game", 2))
        self.assertNotEqual(_policy_rng_seed("test-game", 1),
                            _policy_rng_seed("other-game", 1))

    def test_rejects_invalid_randomization_seeds(self):
        for value in (-1, True, 1.5, "1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _policy_rng_seed("test-game", value)


if __name__ == "__main__":
    unittest.main()
