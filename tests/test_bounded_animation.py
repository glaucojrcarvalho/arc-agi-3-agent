"""EXP-008: bounded but semantically explicit ARC animation observations."""
from __future__ import annotations

import json
import unittest

from arc_agent.model import build_policy_prompt
from arc_agent.perception import bounded_animation_observation


def grid(color: int) -> list[list[int]]:
    return [[color] * 64 for _ in range(64)]


class BoundedAnimationTests(unittest.TestCase):
    def test_long_animation_dictionary_is_lossless_and_bounded(self):
        # 23 rendered animation frames but only four unique full boards.
        frames = [grid(1)] * 11 + [grid(2)] * 10 + [grid(3), grid(4)]
        observation = bounded_animation_observation(frames)
        self.assertEqual(observation["encoding"], "lossless_animation_frame_dictionary")
        self.assertEqual(observation["animation_frame_count"], 23)
        self.assertEqual(observation["settled_frame_id"], 3)
        self.assertEqual(observation["frame_runs"], [
            {"frame_id": 0, "count": 11},
            {"frame_id": 1, "count": 10},
            {"frame_id": 2, "count": 1},
            {"frame_id": 3, "count": 1},
        ])
        self.assertEqual(len(observation["unique_frames"]), 4)
        self.assertLess(len(json.dumps(observation)), 24000)

    def test_large_distinct_animation_samples_settled_frame(self):
        frames = [grid(i % 16) for i in range(79)]
        result = bounded_animation_observation(frames)
        self.assertEqual(result["encoding"], "sampled_animation_keyframes")
        self.assertEqual(result["animation_frame_count"], 79)
        self.assertEqual(result["settled_frame_index"], 78)
        self.assertEqual(result["sampled_frames"][-1]["original_frame_index"], 78)
        self.assertLessEqual(len(result["sampled_frames"]), 4)
        self.assertEqual(
            result["omitted_frame_count"] + len(result["sampled_frames"]), 79
        )
        self.assertLess(len(json.dumps(result)), 24000)

    def test_frequent_animation_alternation_is_bounded(self):
        frames = [grid(i % 2) for i in range(100)]
        result = bounded_animation_observation(frames)
        self.assertEqual(result["encoding"], "sampled_animation_keyframes")
        self.assertEqual(result["settled_frame_index"], 99)

    def test_small_animation_preserves_all_intermediate_boards(self):
        frames = [grid(1), grid(2), grid(1)]
        result = bounded_animation_observation(frames)
        self.assertEqual(result["encoding"], "lossless_animation_frame_dictionary")
        self.assertEqual(len(result["unique_frames"]), 2)
        self.assertEqual([run["frame_id"] for run in result["frame_runs"]], [0, 1, 0])

    def test_empty_animation(self):
        self.assertEqual(bounded_animation_observation([])["animation_frame_count"], 0)
        with self.assertRaises(ValueError):
            bounded_animation_observation([grid(1)], max_unique_frames=1)

    def test_actual_policy_prompt_is_bounded_with_many_frames(self):
        frames = [grid(1)] * 11 + [grid(2)] * 10 + [grid(3), grid(4)]
        prompt = build_policy_prompt(
            frame=frames, state="NOT_FINISHED", levels_completed=0,
            available_action_ids=[1], complex_action_ids=[],
            width=64, height=64, frame_representation="bounded_animation",
            transition_feedback=[{"changed_cells": 4096}],
        )
        self.assertLess(len(prompt.encode("utf-8")), 25000)
        self.assertEqual(
            json.loads(prompt)["visual_observation"]["settled_frame_id"], 3
        )


if __name__ == "__main__":
    unittest.main()
