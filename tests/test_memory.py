from __future__ import annotations

import unittest

from arc_agent.memory import TransitionMemory


class TransitionMemoryTests(unittest.TestCase):
    def test_records_noop_and_effectful_transitions(self) -> None:
        memory = TransitionMemory(maxlen=4)
        frame = [[[0, 0], [0, 0]]]

        noop = memory.record(
            action_id=1,
            before_frame=frame,
            after_frame=frame,
            before_state="playing",
            after_state="playing",
        )
        effectful = memory.record(
            action_id=1,
            before_frame=frame,
            after_frame=[[[0, 1], [0, 0]]],
            before_state="playing",
            after_state="playing",
        )

        self.assertFalse(noop.effectful)
        self.assertTrue(effectful.effectful)
        self.assertFalse(effectful.progressed)

        stats = memory.stats(1)
        self.assertEqual(stats.attempts, 2)
        self.assertEqual(stats.effectful_attempts, 1)
        self.assertEqual(stats.total_changed_cells, 1)
        self.assertEqual(stats.effect_rate, 0.5)
        self.assertEqual(stats.progress_rate, 0.0)
        self.assertEqual(stats.mean_changed_cells, 0.5)

    def test_level_progress_is_recorded_separately_from_effect(self) -> None:
        memory = TransitionMemory()
        frame = [[[7]]]

        transition = memory.record(
            action_id=2,
            before_frame=frame,
            after_frame=frame,
            before_levels=0,
            after_levels=1,
            before_state="playing",
            after_state="playing",
        )

        self.assertTrue(transition.effectful)
        self.assertTrue(transition.progressed)
        stats = memory.stats(2)
        self.assertEqual(stats.progress_attempts, 1)
        self.assertEqual(stats.progress_rate, 1.0)

    def test_game_over_state_change_is_effect_not_progress(self) -> None:
        memory = TransitionMemory()
        frame = [[[0]]]

        transition = memory.record(
            action_id=3,
            before_frame=frame,
            after_frame=frame,
            before_state="playing",
            after_state="game_over",
        )

        self.assertTrue(transition.effectful)
        self.assertFalse(transition.progressed)
        stats = memory.stats(3)
        self.assertEqual(stats.effectful_attempts, 1)
        self.assertEqual(stats.progress_attempts, 0)

    def test_memory_is_bounded(self) -> None:
        memory = TransitionMemory(maxlen=2)
        frame = [[[0]]]

        for action_id in (1, 2, 3):
            memory.record(
                action_id=action_id,
                before_frame=frame,
                after_frame=frame,
            )

        self.assertEqual(len(memory), 2)
        self.assertEqual([item.action_id for item in memory.transitions], [2, 3])

    def test_rejects_non_positive_capacity(self) -> None:
        with self.assertRaises(ValueError):
            TransitionMemory(maxlen=0)


if __name__ == "__main__":
    unittest.main()
