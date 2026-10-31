"""Safety checks for isolated EXP-013 no-op evidence ablation."""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_exp013_variant import HELPER, build_variant  # noqa: E402


class OutcomeGateTests(unittest.TestCase):
    def test_builds_only_local_standalone_agent_and_compiles(self):
        baseline = (ROOT / "agent/exp005_agent.py").read_text()
        experiment = build_variant(min_noops=2, fast_after=4)
        compile(experiment, "exp013_standalone.py", "exec")
        self.assertIn("def _exp013_recent_exact_noops(", experiment)
        self.assertIn("exact_noop_evidence", experiment)
        self.assertNotIn("_exp013_recent_exact_noops", baseline)

    def test_both_threshold_variants_differ(self):
        low = build_variant(min_noops=2, fast_after=4)
        high = build_variant(min_noops=3, fast_after=4)
        self.assertNotEqual(low, high)

    def test_noop_counter_stops_at_level_progress_or_terminal_change(self):
        code = ast.parse(HELPER)
        helper = next(n for n in code.body
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "_exp013_recent_exact_noops")
        ns = {}
        exec(compile(ast.Module(body=[helper], type_ignores=[]), "helper.py", "exec"), ns)
        count = ns["_exp013_recent_exact_noops"]
        no = {"proven_noop": True, "levels_delta": 0, "state_changed": False}
        effect = {"proven_noop": False, "levels_delta": 0, "state_changed": False}
        progress = {"proven_noop": False, "levels_delta": 1, "state_changed": False}
        terminal = {"proven_noop": False, "levels_delta": 0, "state_changed": True}
        self.assertEqual(count([no, no, effect]), 2)
        self.assertEqual(count([no, no, progress, no]), 1)
        self.assertEqual(count([no, terminal, no]), 1)
        self.assertEqual(count([no] * 7), 4)
        self.assertEqual(count([effect, effect]), 0)

    def test_rejects_invalid_config(self):
        for args in ({"min_noops": 0}, {"min_noops": 5},
                     {"fast_after": 0}, {"fast_after": 8}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                build_variant(**args)


if __name__ == "__main__":
    unittest.main()
