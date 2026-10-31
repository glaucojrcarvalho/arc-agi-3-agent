"""Evaluation-only randomization must never leak into the production agent."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from public_policy_rng import policy_rng_seed


class EvaluationPolicySeedTests(unittest.TestCase):
    def test_deterministic_but_independent_controller_seeds(self):
        self.assertEqual(policy_rng_seed("test-game", 1),
                         policy_rng_seed("test-game", 1))
        self.assertNotEqual(policy_rng_seed("test-game", 1),
                            policy_rng_seed("test-game", 2))
        self.assertNotEqual(policy_rng_seed("test-game", 1),
                            policy_rng_seed("other-game", 1))

    def test_public_game_full_id_and_prefix_have_identical_rng(self):
        for seed in range(6):
            self.assertEqual(
                policy_rng_seed("abcd", seed),
                policy_rng_seed("abcd-0123abcd", seed),
            )
        self.assertNotEqual(
            policy_rng_seed("abcd", 2), policy_rng_seed("abce", 2)
        )

    def test_rejects_invalid_randomization_seeds(self):
        for value in (-1, True, 1.5, "1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                policy_rng_seed("test-game", value)


if __name__ == "__main__":
    unittest.main()
