"""Public-only EXP-017 structural and controller-behavior regression tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_exp017_variant import build_variant  # noqa: E402
from arc_agent.novelty_explorer import NoveltyExplorer  # noqa: E402

class TestExp017(unittest.TestCase):
    def test_level_coverage_variant_compiles_and_keeps_feedback_exact(self):
        src = build_variant(mode="level")
        compile(src, "exp017-level", "exec")
        self.assertIn('exploration_key = f"level:{level}"', src)
        self.assertEqual(src.count("fingerprint=exploration_key"), 2)
        self.assertIn("fingerprint = self._feedback.observe(", src)
        self.assertIn("fingerprint=fingerprint,", src)

    def test_window_coverage_variant_compiles(self):
        src = build_variant(mode="window", window=12)
        compile(src, "exp017-window", "exec")
        self.assertIn('window:{self._feedback.turns // 12}', src)
        self.assertEqual(src.count("fingerprint=exploration_key"), 2)

    def test_rejects_unsupported_window_or_mode(self):
        for value in (True, 3, 33, "12"):
            with self.assertRaises(ValueError):
                build_variant(mode="window", window=value)
        with self.assertRaises(ValueError):
            build_variant(mode="random")

    def test_same_state_action_balance(self):
        explorer = NoveltyExplorer("synthetic-public-smoke")
        counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for _ in range(40):
            action, data = explorer.choose(
                fingerprint="level:0", legal_actions=[1,2,3,4],
                complex_action_ids=set(), candidates=[], width=64, height=64,
            )
            self.assertEqual(data, {})
            counts[action] += 1
            explorer.note_action(fingerprint="level:0", action_id=action, data=data)
        self.assertEqual(set(counts.values()), {10})
        explorer.progress()
        self.assertEqual(len(explorer._visits), 0)

if __name__ == "__main__":
    unittest.main()
