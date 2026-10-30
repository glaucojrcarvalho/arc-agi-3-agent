from __future__ import annotations

import json
import unittest

from arc_agent.model import build_policy_prompt
from arc_agent.perception import salient_click_targets, symbol_grid


class PerceptionTests(unittest.TestCase):
    def test_symbol_grid_is_lossless_for_multiple_layers(self) -> None:
        frame = [[[0, 1, 15], [2, 10, 7]], [[11, 12, 13], [14, 9, 8]]]
        encoded = symbol_grid(frame)
        recovered = [
            [[int(char, 16) for char in line.split("|", 1)[1]] for line in layer["rows"]]
            for layer in encoded["layers"]
        ]
        self.assertEqual(recovered, frame)
        self.assertEqual(encoded["palette_counts"]["15"], 1)

    def test_unusual_palette_keeps_exact_integer_indices(self) -> None:
        frame = [[[-2, 16, 100], [31, 5, 0]]]
        encoded = symbol_grid(frame)
        self.assertIn("signed_decimal", encoded["encoding"])
        recovered = [
            [int(v) for v in line.split("|", 1)[1].split()]
            for line in encoded["layers"][0]["rows"]
        ]
        self.assertEqual(recovered, frame[0])

    def test_targets_are_within_bounds_and_on_their_color(self) -> None:
        frame = [
            [[0] * 8 for _ in range(8)],
            [[2] * 8 for _ in range(8)],
        ]
        frame[0][2][3] = 15
        frame[0][3][3] = 15
        frame[1][7][6] = 11
        targets = salient_click_targets(frame, max_targets=20)
        self.assertTrue(targets)
        for target in targets:
            self.assertLess(target["x"], 8)
            self.assertLess(target["y"], 8)
            self.assertGreaterEqual(target["x"], 0)
            self.assertGreaterEqual(target["y"], 0)
            self.assertEqual(frame[target["layer"]][target["y"]][target["x"]], target["color"])
        self.assertIn((3, 2), {(x["x"], x["y"]) for x in targets})

    def test_prioritizes_rare_visible_regions(self) -> None:
        frame = [[[0] * 8 for _ in range(8)]]
        frame[0][3][5] = 12
        targets = salient_click_targets(frame)
        self.assertTrue(targets)
        self.assertEqual((targets[0]["x"], targets[0]["y"], targets[0]["color"]), (5, 3, 12))

    def test_symbol_grid_is_smaller_on_realistic_uniform_background(self) -> None:
        frame = [[[5] * 64 for _ in range(64)], [[10] * 64 for _ in range(64)]]
        raw = build_policy_prompt(
            frame=frame, state="NOT_FINISHED", levels_completed=0,
            available_action_ids=[1, 6], complex_action_ids=[6], width=64, height=64,
        )
        packed = build_policy_prompt(
            frame=frame, state="NOT_FINISHED", levels_completed=0,
            available_action_ids=[1, 6], complex_action_ids=[6], width=64, height=64,
            frame_representation="symbol_grid",
        )
        self.assertLess(len(packed), len(raw))
        parsed = json.loads(packed)
        self.assertNotIn("frame", parsed)
        self.assertEqual(len(parsed["visual_observation"]["layers"]), 2)
        self.assertIn("pixel_coordinate_convention", parsed)

    def test_click_candidates_are_optional_and_capped(self) -> None:
        frame = [[[0, 1]]]
        prompt = build_policy_prompt(
            frame=frame, state="NOT_FINISHED", levels_completed=0,
            available_action_ids=[6], complex_action_ids=[6], width=2, height=1,
            frame_representation="symbol_grid",
            click_candidates=[{"x": i, "y": 0} for i in range(30)],
        )
        self.assertEqual(len(json.loads(prompt)["candidate_click_pixels"]), 24)
        with self.assertRaises(ValueError):
            salient_click_targets(frame, max_targets=0)
        with self.assertRaises(ValueError):
            build_policy_prompt(
                frame=frame, state="NOT_FINISHED", levels_completed=0,
                available_action_ids=[6], complex_action_ids=[6], width=2, height=1,
                frame_representation="invalid",
            )


if __name__ == "__main__":
    unittest.main()
