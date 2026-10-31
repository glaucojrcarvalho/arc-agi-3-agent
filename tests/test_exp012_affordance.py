"""Purely experimental EXP-012 affordance A/B guardrails."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_exp012_variant import build_variant, build_explorer_source


class ExperimentalAffordanceTests(unittest.TestCase):
    def test_probability_guard(self):
        with self.assertRaises(ValueError):
            build_variant(complex_action_probability=-.01)
        with self.assertRaises(ValueError):
            build_variant(complex_action_probability=1.01)

    def test_official_agent_unchanged_and_valid_python(self):
        source = (ROOT / "agent/exp005_agent.py").read_text()
        original_explorer = (ROOT / "src/arc_agent/novelty_explorer.py").read_text()
        variant = build_variant()
        self.assertNotIn("EXP-012", source)
        self.assertNotIn("EXP-012", original_explorer)
        self.assertIn("EXP-012 local A/B only", build_explorer_source())
        compile(variant, "exp012_standalone", "exec")

    def test_determinism_and_click_safety(self):
        ns = {"__name__": "exp012_test_agent"}
        exec(compile(build_explorer_source(), "exp012_explorer", "exec"), ns)
        cls = ns["NoveltyExplorer"]
        a, b = cls("public-random-demo"), cls("public-random-demo")
        kwargs = dict(fingerprint="stable", legal_actions=[1, 2, 6],
                      complex_action_ids={6},
                      candidates=[{"x": x, "y": 1} for x in range(5)],
                      width=8, height=8)
        for _ in range(64):
            action_a, data_a = a.choose(**kwargs)
            action_b, data_b = b.choose(**kwargs)
            self.assertEqual((action_a, data_a), (action_b, data_b))
            self.assertIn(action_a, [1, 2, 6])
            if action_a == 6:
                self.assertTrue(0 <= data_a["x"] < 8 and 0 <= data_a["y"] < 8)
            else:
                self.assertEqual(data_a, {})
            a.note_action(fingerprint="stable", action_id=action_a, data=data_a)
            b.note_action(fingerprint="stable", action_id=action_b, data=data_b)

    def test_high_bias_increases_complex_actions_on_stable_frame(self):
        from arc_agent.novelty_explorer import NoveltyExplorer as Baseline
        ns = {"__name__": "exp012_test_agent"}
        exec(compile(build_explorer_source(complex_action_probability=0.65),
                     "exp012_explorer", "exec"), ns)
        scenarios = (Baseline("public-random-demo"),
                     ns["NoveltyExplorer"]("public-random-demo"))
        kwargs = dict(fingerprint="stable", legal_actions=[1, 2, 6],
                      complex_action_ids={6},
                      candidates=[{"x": x, "y": 1} for x in range(5)],
                      width=8, height=8)
        counts = []
        for explorer in scenarios:
            complex_count = 0
            for _ in range(200):
                action, data = explorer.choose(**kwargs)
                complex_count += int(action == 6)
                explorer.note_action(fingerprint="stable", action_id=action, data=data)
            counts.append(complex_count)
        self.assertGreater(counts[1], counts[0] + 30)

    def test_no_change_without_complex_control(self):
        ns = {"__name__": "exp012_test_agent"}
        exec(compile(build_explorer_source(), "exp012_explorer", "exec"), ns)
        variant = ns["NoveltyExplorer"]("same-public-seed")
        from arc_agent.novelty_explorer import NoveltyExplorer as Baseline
        baseline = Baseline("same-public-seed")
        kwargs = dict(fingerprint="stable", legal_actions=[1, 2, 3, 4],
                      complex_action_ids=set(), candidates=[], width=8, height=8)
        for _ in range(48):
            x = baseline.choose(**kwargs)
            y = variant.choose(**kwargs)
            self.assertEqual(x, y)
            baseline.note_action(fingerprint="stable", action_id=x[0], data=x[1])
            variant.note_action(fingerprint="stable", action_id=y[0], data=y[1])


if __name__ == "__main__":
    unittest.main()
