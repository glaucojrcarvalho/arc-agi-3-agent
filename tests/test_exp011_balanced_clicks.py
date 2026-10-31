"""Local-only EXP-011 ablation, never imported by the competition agent."""
from __future__ import annotations

import unittest
from experiments.exp011_balanced_click_explorer import NoveltyExplorer


class BalancedClickAblationTests(unittest.TestCase):
    def test_balanced_clicks_spread_across_targets(self):
        explorer = NoveltyExplorer("test", recent_clicks=1, balanced_clicks=True)
        kwargs = dict(
            fingerprint="frame", legal_actions=[6], complex_action_ids={6},
            candidates=[{"x": x, "y": 0} for x in range(20)],
            width=20, height=1,
        )
        for i in range(100):
            action, data = explorer.choose(**kwargs)
            self.assertEqual(action, 6)
            explorer.note_action(fingerprint="frame", action_id=action, data=data)
        self.assertGreaterEqual(len(explorer._click_attempts), 15)
        self.assertEqual(sum(explorer._click_attempts.values()), 100)

    def test_click_memory_bounded_and_reset(self):
        explorer = NoveltyExplorer("test", balanced_clicks=True)
        for i in range(700):
            explorer.note_action(
                fingerprint="frame", action_id=6,
                data={"x": i % 64, "y": i // 64},
            )
        self.assertEqual(sum(explorer._click_attempts.values()), 512)
        self.assertEqual(len(explorer._click_fifo), 512)
        explorer.progress()
        self.assertFalse(explorer._click_attempts)
        self.assertFalse(explorer._click_fifo)

    def test_deterministic_selection(self):
        a = NoveltyExplorer("test", balanced_clicks=True)
        b = NoveltyExplorer("test", balanced_clicks=True)
        kwargs = dict(
            fingerprint="frame", legal_actions=[6], complex_action_ids={6},
            candidates=[{"x": x, "y": 0} for x in range(8)],
            width=8, height=1,
        )
        for _ in range(50):
            action_a, data_a = a.choose(**kwargs)
            action_b, data_b = b.choose(**kwargs)
            self.assertEqual((action_a, data_a), (action_b, data_b))
            a.note_action(fingerprint="frame", action_id=action_a, data=data_a)
            b.note_action(fingerprint="frame", action_id=action_b, data=data_b)

    def test_builder_is_isolated_from_competition_agent(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        from build_exp011_variant import build_variant
        source = (Path(__file__).resolve().parents[1] / "agent" / "exp005_agent.py").read_text()
        self.assertNotIn("BALANCED_CLICK_EXPLORATION", source)
        standalone = build_variant()
        self.assertIn("BALANCED_CLICK_EXPLORATION = True", standalone)
        self.assertNotIn("BALANCED_CLICK_EXPLORATION", source)


if __name__ == "__main__":
    unittest.main()
