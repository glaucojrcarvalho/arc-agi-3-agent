"""Public-only EXP-015 tests: state transitions are not scored progress."""
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_exp015_variant import build_explorer_source, build_variant


def explorer_class(probability: float = 1.0):
    name = "arc_agent._exp015_explorer_test"
    module = types.ModuleType(name)
    module.__package__ = "arc_agent"
    exec(compile(build_explorer_source(probability=probability), name, "exec"), module.__dict__)
    return module.NoveltyExplorer


def choose(explorer, frame: str, *, legal=(1, 2), complex_ids=frozenset(), targets=()):
    return explorer.choose(
        fingerprint=frame, legal_actions=list(legal),
        complex_action_ids=set(complex_ids),
        candidates=list(targets), width=8, height=8,
    )


class MomentumTests(unittest.TestCase):
    def test_repeat_after_novel_settled_transition(self):
        explorer = explorer_class()("synthetic")
        explorer.note_action(fingerprint="A", action_id=2, data={})
        explorer._visits[("B", 2)] = 100
        self.assertEqual(choose(explorer, "B"), (2, {}))
        self.assertEqual(explorer.momentum_actions, 1)
        self.assertEqual(explorer.progress_resets, 0)

    def test_pixel_change_not_success(self):
        explorer = explorer_class()("synthetic")
        explorer.note_action(fingerprint="A", action_id=1, data={})
        choose(explorer, "B")
        self.assertEqual(explorer.progress_resets, 0)

    def test_noop_does_not_trigger_momentum(self):
        explorer = explorer_class()("synthetic")
        explorer.note_action(fingerprint="A", action_id=2, data={})
        explorer._visits[("A", 2)] = 100
        self.assertEqual(choose(explorer, "A")[0], 1)
        self.assertEqual(explorer.momentum_actions, 0)

    def test_recent_cycle_disables_momentum(self):
        explorer = explorer_class()("synthetic")
        explorer.note_action(fingerprint="A", action_id=2, data={})
        explorer.note_action(fingerprint="B", action_id=2, data={})
        explorer._visits[("A", 2)] = 100
        self.assertEqual(choose(explorer, "A")[0], 1)
        self.assertEqual(explorer.momentum_actions, 0)

    def test_chain_length_is_bounded(self):
        explorer = explorer_class()("synthetic")
        for i in range(3):
            explorer.note_action(fingerprint=str(i), action_id=2, data={})
        explorer._visits[("new", 2)] = 100
        self.assertEqual(choose(explorer, "new")[0], 1)

    def test_verified_level_progress_clears_memory(self):
        explorer = explorer_class()("synthetic")
        explorer.note_action(fingerprint="A", action_id=1, data={})
        explorer.progress()  # only caller with observed levels_completed increment
        self.assertFalse(explorer._recent_frames)
        self.assertIsNone(explorer._previous_keyboard_action)
        self.assertEqual(explorer.progress_resets, 1)

    def test_coordinate_action_not_repeated_by_momentum(self):
        explorer = explorer_class()("synthetic")
        explorer.note_action(fingerprint="A", action_id=6, data={"x":2,"y":3})
        choose(explorer, "B", legal=(1,6), complex_ids={6},
               targets=({"x":2,"y":3},))
        self.assertEqual(explorer.momentum_actions, 0)

    def test_parameter_bounds_and_standalone_compilation(self):
        with self.assertRaises(ValueError):
            build_explorer_source(probability=-0.1)
        with self.assertRaises(ValueError):
            build_explorer_source(probability=0.5, max_chain=1)
        compile(build_variant(probability=0.55), "<exp015-standalone>", "exec")


if __name__ == "__main__":
    unittest.main()
