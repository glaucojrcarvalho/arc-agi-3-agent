from __future__ import annotations

import unittest

from arc_agent.actions import (
    ActionValidationError,
    deterministic_fallback,
    parse_action_json,
    validate_action_proposal,
)


class ActionValidationTests(unittest.TestCase):
    def test_parses_valid_json_object(self) -> None:
        payload = parse_action_json('{"action": 2, "data": {}, "reason": "test"}')
        self.assertEqual(payload["action"], 2)

    def test_rejects_non_object_json(self) -> None:
        with self.assertRaises(ActionValidationError):
            parse_action_json("[1, 2, 3]")

    def test_rejects_unavailable_action(self) -> None:
        with self.assertRaises(ActionValidationError):
            validate_action_proposal(
                {"action": 5},
                available_action_ids=[1, 2, 3],
            )

    def test_rejects_malformed_available_action_ids(self) -> None:
        for malformed in ([True, 2], ["1", 2], [1.5, 2]):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ActionValidationError):
                    validate_action_proposal(
                        {"action": 2},
                        available_action_ids=malformed,  # type: ignore[arg-type]
                    )

    def test_validates_complex_action_coordinates(self) -> None:
        proposal = validate_action_proposal(
            {"action": 6, "data": {"x": 3, "y": 4}, "reason": "inspect"},
            available_action_ids=[1, 6],
            complex_action_ids={6},
            width=8,
            height=8,
        )

        self.assertEqual(proposal.action_id, 6)
        self.assertEqual(proposal.data, {"x": 3, "y": 4})

    def test_rejects_out_of_bounds_coordinates(self) -> None:
        with self.assertRaises(ActionValidationError):
            validate_action_proposal(
                {"action": 6, "data": {"x": 8, "y": 0}},
                available_action_ids=[6],
                complex_action_ids={6},
                width=8,
                height=8,
            )

    def test_arc_coordinate_limit_applies_even_for_oversized_frame(self) -> None:
        with self.assertRaises(ActionValidationError):
            validate_action_proposal(
                {"action": 6, "data": {"x": 64, "y": 0}},
                available_action_ids=[6],
                complex_action_ids={6},
                width=80,
                height=80,
            )

    def test_boolean_is_not_accepted_as_action_id(self) -> None:
        with self.assertRaises(ActionValidationError):
            validate_action_proposal(
                {"action": True},
                available_action_ids=[1],
            )

    def test_fallback_is_deterministic(self) -> None:
        self.assertEqual(deterministic_fallback([4, 2, 3]), 2)

    def test_fallback_rejects_malformed_action_ids(self) -> None:
        with self.assertRaises(ActionValidationError):
            deterministic_fallback([True, 2])

    def test_fallback_requires_available_action(self) -> None:
        with self.assertRaises(ActionValidationError):
            deterministic_fallback([])


if __name__ == "__main__":
    unittest.main()
