from __future__ import annotations

import unittest
from arc_agent.novelty_explorer import NoveltyExplorer


class NoveltyExplorerTests(unittest.TestCase):
    def test_is_seeded_and_avoids_recent_clicks(self):
        a=NoveltyExplorer("public-sample")
        b=NoveltyExplorer("public-sample")
        kwargs=dict(fingerprint="abc",legal_actions=[6],complex_action_ids={6},
                    candidates=[{"x":1,"y":1},{"x":2,"y":2}],width=4,height=4)
        for i in range(3):
            self.assertEqual(a.choose(**kwargs),b.choose(**kwargs))

    def test_legal_action_and_coordinates(self):
        e=NoveltyExplorer("abc")
        for i in range(6):
            action,data=e.choose(
                fingerprint="same",legal_actions=[1,6],complex_action_ids={6},
                candidates=[{"x":-1,"y":10},{"x":2,"y":1}],
                width=4,height=4)
            self.assertIn(action,[1,6])
            if action==6:
                self.assertTrue(0<=data["x"]<4 and 0<=data["y"]<4)
            else:
                self.assertEqual(data,{})
            e.note_action(fingerprint="same",action_id=action,data=data)
        self.assertEqual(e.heuristic_calls,6)
        e.progress()
        self.assertEqual(e.progress_resets,1)
        self.assertEqual(len(e._visits),0)

    def test_invalid_limits(self):
        with self.assertRaises(ValueError):
            NoveltyExplorer("a",recent_clicks=0)
        with self.assertRaises(ValueError):
            NoveltyExplorer("a").choose(
                fingerprint="foo",legal_actions=[],complex_action_ids=set(),
                candidates=[],width=1,height=1)


if __name__=="__main__":
    unittest.main()
