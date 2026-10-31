"""Bounded per-visible-state click exploration: never a level-progress proxy."""
from __future__ import annotations

import unittest
from arc_agent.novelty_explorer import NoveltyExplorer


class StateClickMemoryTests(unittest.TestCase):
    def test_remembers_clicks_in_a_specific_visible_state(self):
        explorer = NoveltyExplorer("synthetic-game")
        explorer._rng.random = lambda: 0.9
        explorer.note_action(fingerprint="A", action_id=6, data={"x":1,"y":1})
        kwargs = {
            "legal_actions": [6], "complex_action_ids": {6},
            "candidates": [{"x":1,"y":1},{"x":2,"y":2}],
            "width":4,"height":4,
        }
        action, data = explorer.choose(fingerprint="A",**kwargs)
        self.assertEqual((action,data),(6,{"x":2,"y":2}))
        action, data = explorer.choose(fingerprint="B",**kwargs)
        self.assertEqual(action,6)
        self.assertIn(data,({"x":1,"y":1},{"x":2,"y":2}))

    def test_bounded_per_state_history(self):
        explorer = NoveltyExplorer("synthetic-game")
        for i in range(300):
            explorer.note_action(fingerprint=str(i % 13),action_id=6,
                                 data={"x":i % 8,"y":i % 11})
        self.assertEqual(len(explorer._click_history),256)
        self.assertEqual(sum(explorer._state_click_attempts.values()),256)
        self.assertGreater(len(explorer._state_click_attempts),0)
        explorer.progress()
        self.assertFalse(explorer._click_history)
        self.assertFalse(explorer._state_click_attempts)

    def test_non_coordinate_actions_have_no_click_memory(self):
        explorer = NoveltyExplorer("synthetic-game")
        explorer.note_action(fingerprint="A",action_id=1,data={})
        self.assertFalse(explorer._state_click_attempts)
        self.assertEqual(len(explorer._click_history),0)

    def test_state_count_is_not_progress(self):
        explorer = NoveltyExplorer("synthetic-game")
        explorer.note_action(fingerprint="A",action_id=6,data={"x":0,"y":0})
        explorer.note_action(fingerprint="B",action_id=6,data={"x":0,"y":1})
        self.assertEqual(explorer.progress_resets,0)
        self.assertEqual(len(explorer._click_history),2)


if __name__ == "__main__":
    unittest.main()
