from __future__ import annotations

import unittest
from arc_agent.transition_policy import TransitionPolicy


class ClickCooldownTests(unittest.TestCase):
    def test_reject_repeated_click_with_frame_transition(self) -> None:
        policy = TransitionPolicy(click_cooldown=3)
        frame = [[[1, 2]]]
        policy.record(
            frame=frame, level=0, state="PLAYING",
            action_id=6, data={"x": 1, "y": 0}
        )
        newframe = [[[1, 3]]]
        fingerprint = policy.observe(frame=newframe, level=0, state="PLAYING")
        self.assertEqual(policy.proven_noops, 0)
        selected = policy.redirect(
            level=0, fingerprint=fingerprint, action_ids=[6],
            complex_action_ids={6}, width=2, height=1,
            proposed=(6, {"x": 1, "y": 0}),
            candidate_coordinates=[{"x": 0, "y": 0}],
        )
        self.assertEqual(selected, (6, {"x": 0, "y": 0}, True))

    def test_cooldown_expires_and_is_bounded(self) -> None:
        policy = TransitionPolicy(click_cooldown=2)
        frame = [[[1, 2, 3]]]
        for x in (0, 1, 2):
            policy.record(
                frame=frame, level=0, state="PLAYING",
                action_id=6, data={"x": x, "y": 0}
            )
        cooled = policy.cooled_clicks(level=0)
        self.assertEqual([item["x"] for item in cooled], [2, 1])
        self.assertFalse(policy._cooled(0, 6, {"x": 0, "y": 0}))
        self.assertTrue(policy._cooled(0, 6, {"x": 1, "y": 0}))

    def test_progress_clears_cooldown_and_reset_clears_it_too(self) -> None:
        policy = TransitionPolicy(click_cooldown=2)
        frame = [[[1]]]
        policy.record(
            frame=frame, level=0, state="PLAYING",
            action_id=6, data={"x": 0, "y": 0}
        )
        policy.observe(frame=frame, level=1, state="PLAYING")
        self.assertEqual(policy.cooled_clicks(level=0), [])
        policy.record(
            frame=frame, level=1, state="PLAYING",
            action_id=6, data={"x": 0, "y": 0}
        )
        self.assertTrue(policy.cooled_clicks(level=1))
        policy.on_reset()
        self.assertEqual(policy.cooled_clicks(level=1), [])

    def test_no_repeat_block_for_noncomplex_action(self) -> None:
        policy = TransitionPolicy(click_cooldown=8)
        frame = [[[0]]]
        policy.record(frame=frame, level=0, state="PLAYING", action_id=1, data={})
        self.assertEqual(policy.cooled_clicks(level=0), [])

    def test_invalid_cooldown_limits(self) -> None:
        with self.assertRaises(ValueError):
            TransitionPolicy(click_cooldown=-1)
        with self.assertRaises(ValueError):
            TransitionPolicy(click_cooldown=33)


if __name__ == "__main__":
    unittest.main()
