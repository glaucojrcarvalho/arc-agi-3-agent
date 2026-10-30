from __future__ import annotations
import unittest
from arc_agent.transition_policy import TransitionPolicy


class TransitionPolicyTests(unittest.TestCase):
    def test_exact_noop_blocks_same_move(self) -> None:
        policy = TransitionPolicy()
        frame = [[[0, 1], [2, 3]]]
        policy.observe(frame=frame, level=0, state="PLAYING")
        policy.record(frame=frame, level=0, state="PLAYING", action_id=1, data={})
        fp = policy.observe(frame=frame, level=0, state="PLAYING")
        self.assertEqual(policy.proven_noops, 1)
        self.assertEqual(policy.feedback()[-1]["proven_noop"], True)
        self.assertEqual(policy.blocked(level=0, fingerprint=fp), [{"action": 1, "data": {}}])
        self.assertEqual(policy.redirect(
            level=0, fingerprint=fp, action_ids=[1, 2],
            complex_action_ids=set(), width=2, height=2, proposed=(1, {}),
        ), (2, {}, True))

    def test_effect_is_not_progress(self) -> None:
        policy = TransitionPolicy()
        before = [[[0, 0]]]
        after = [[[1, 0]]]
        policy.observe(frame=before, level=0, state="PLAYING")
        policy.record(frame=before, level=0, state="PLAYING", action_id=1, data={})
        fp = policy.observe(frame=after, level=0, state="PLAYING")
        self.assertEqual(policy.proven_noops, 0)
        self.assertEqual(policy.progress_events, 0)
        self.assertEqual(policy.feedback()[-1]["changed_cells"], 1)
        self.assertEqual(policy.feedback()[-1]["levels_delta"], 0)
        self.assertFalse(policy.blocked(level=0, fingerprint=fp))

    def test_mutated_engine_buffer(self) -> None:
        policy = TransitionPolicy()
        frame = [[[0, 0]]]
        policy.record(frame=frame, level=0, state="PLAYING", action_id=1, data={})
        frame[0][0][0] = 5
        policy.observe(frame=frame, level=0, state="PLAYING")
        self.assertEqual(policy.feedback()[-1]["changed_cells"], 1)
        self.assertEqual(policy.proven_noops, 0)

    def test_same_click_avoided_different_coordinate_allowed(self) -> None:
        policy = TransitionPolicy()
        frame = [[[0, 0, 0], [0, 0, 0], [0, 0, 0]]]
        policy.record(frame=frame, level=0, state="PLAYING", action_id=6, data={"x": 1, "y": 1})
        fp = policy.observe(frame=frame, level=0, state="PLAYING")
        action, data, redirected = policy.redirect(
            level=0, fingerprint=fp, action_ids=[6], complex_action_ids={6},
            width=3, height=3, proposed=(6, {"x": 1, "y": 1}),
        )
        self.assertEqual(action, 6)
        self.assertTrue(redirected)
        self.assertNotEqual(data, {"x": 1, "y": 1})

    def test_progress_invalidates_noop_memo(self) -> None:
        policy = TransitionPolicy()
        frame = [[[3]]]
        policy.record(frame=frame, level=0, state="PLAYING", action_id=1, data={})
        fp = policy.observe(frame=frame, level=0, state="PLAYING")
        self.assertTrue(policy.blocked(level=0, fingerprint=fp))
        policy.record(frame=frame, level=0, state="PLAYING", action_id=2, data={})
        policy.observe(frame=frame, level=1, state="PLAYING")
        self.assertEqual(policy.progress_events, 1)
        self.assertFalse(policy.blocked(level=0, fingerprint=fp))

    def test_fallback_rotates_when_model_invalid(self) -> None:
        policy = TransitionPolicy()
        frame = [[[2]]]
        fp = policy.observe(frame=frame, level=0, state="PLAYING")
        result = policy.redirect(
            level=0, fingerprint=fp, action_ids=[1, 2],
            complex_action_ids=set(), width=1, height=1, proposed=None,
        )
        self.assertEqual(result, (1, {}, True))
        policy.record(frame=frame, level=0, state="PLAYING", action_id=1, data={})
        fp = policy.observe(frame=frame, level=0, state="PLAYING")
        result = policy.redirect(
            level=0, fingerprint=fp, action_ids=[1, 2],
            complex_action_ids=set(), width=1, height=1, proposed=None,
        )
        self.assertEqual(result, (2, {}, True))

    def test_history_and_state_keys_bounded(self) -> None:
        policy = TransitionPolicy(memory_limit=2, state_limit=1)
        for color in range(5):
            frame = [[[color]]]
            policy.record(frame=frame, level=0, state="PLAYING", action_id=1, data={})
            policy.observe(frame=frame, level=0, state="PLAYING")
        self.assertEqual(len(policy.feedback()), 2)
        self.assertEqual(len(policy._blocked), 1)

    def test_invalid_bounds(self) -> None:
        with self.assertRaises(ValueError):
            TransitionPolicy(memory_limit=0)
        with self.assertRaises(ValueError):
            TransitionPolicy(state_limit=0)


if __name__ == "__main__":
    unittest.main()
