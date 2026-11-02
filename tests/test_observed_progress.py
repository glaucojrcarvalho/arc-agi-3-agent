"""EXP-023: evidence of progress is bounded, grounded, and isolated."""
from __future__ import annotations
import unittest
from arc_agent.observed_progress import ObservedProgressMemory

def step(a: int, delta: int = 0) -> dict:
    return {"action": a, "data": {}, "levels_delta": delta,
            "changed_cells": 2, "proven_noop": False}

class ObservedProgressTests(unittest.TestCase):
    def test_progress_only_on_authoritative_increment(self):
        m = ObservedProgressMemory()
        m.observe(level=0, transition=None)
        m.observe(level=0, transition=step(1))
        m.observe(level=1, transition=step(2, delta=0))
        self.assertEqual(m.progress_observations, 0)
        m.observe(level=2, transition=step(3, delta=1))
        self.assertEqual(m.progress_observations, 1)
        self.assertEqual(
            m.prompt_context()["completed_level_traces"][0]["to_level"], 2)
        self.assertIn("do not prove", m.prompt_context()["causality_warning"])

    def test_bounded_steps_and_completed_levels(self):
        m = ObservedProgressMemory(max_levels=2, max_steps=3)
        m.observe(level=0, transition=None)
        for a in (1, 2, 3, 4):
            m.observe(level=0, transition=step(a))
        m.observe(level=1, transition=step(5, delta=1))
        first = m.prompt_context()["completed_level_traces"][0]
        self.assertEqual(
            [x["action"] for x in first["observed_steps_before_completion"]],
            [3, 4, 5])
        m.observe(level=2, transition=step(1, delta=1))
        m.observe(level=3, transition=step(2, delta=1))
        self.assertEqual(
            [x["to_level"] for x in m.prompt_context()["completed_level_traces"]],
            [2, 3])

    def test_rejects_unauthenticated_progress(self):
        m = ObservedProgressMemory()
        m.observe(level=0, transition=None)
        m.observe(level=1, transition={"levels_delta": 1, "action": True})
        m.observe(level=2, transition=None)
        self.assertEqual(m.progress_observations, 0)

    def test_reset_and_rollbacks_clear_history(self):
        m = ObservedProgressMemory()
        m.observe(level=0, transition=None)
        m.observe(level=1, transition=step(1, delta=1))
        m.on_reset()
        self.assertEqual(m.progress_observations, 0)
        m.observe(level=0, transition=None)
        m.observe(level=1, transition=step(2, delta=1))
        m.observe(level=0, transition=step(3))
        self.assertEqual(m.prompt_context()["completed_level_traces"], [])

    def test_sanitize_unsafe_and_untrusted_data(self):
        m = ObservedProgressMemory()
        m.observe(level=0, transition=None)
        m.observe(level=1, transition={
            "action": 6, "data": {"x": 3, "y": -4, "reason": "hallucination"},
            "levels_delta": 1, "changed_cells": 100000, "secret": "NEVER_COPY"})
        result = m.prompt_context()
        self.assertNotIn("NEVER_COPY", str(result))
        self.assertNotIn("hallucination", str(result))
        last = result["completed_level_traces"][0]["observed_steps_before_completion"][-1]
        self.assertEqual(last["data"], {"x": 3})
        self.assertEqual(last["observed_changed_cells"], 4096)

    def test_invalid_parameters(self):
        for kwargs in ({"max_steps": 0}, {"max_levels": 0}, {"max_levels": 9}):
            with self.assertRaises(ValueError):
                ObservedProgressMemory(**kwargs)

if __name__ == "__main__":
    unittest.main()
