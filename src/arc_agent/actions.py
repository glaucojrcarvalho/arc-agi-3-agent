"""Model-output parsing and action validation independent from ARC runtime types."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

ARC_ACTION_COORDINATE_LIMIT = 64


class ActionValidationError(ValueError):
    """Raised when a proposed action cannot be executed safely."""


@dataclass(frozen=True)
class ActionProposal:
    action_id: int
    data: dict[str, int]
    reason: str = ""


def parse_action_json(text: str) -> Mapping[str, Any]:
    """Parse a model response that must be exactly one JSON object."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ActionValidationError("response is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise ActionValidationError("response must be a JSON object")
    return payload


def _strict_action_ids(values: Sequence[int]) -> tuple[int, ...]:
    action_ids: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ActionValidationError("available action ids must be integers")
        action_ids.append(value)
    return tuple(action_ids)


def validate_action_proposal(
    payload: Mapping[str, Any],
    *,
    available_action_ids: Sequence[int],
    complex_action_ids: set[int] | frozenset[int] = frozenset(),
    width: int | None = None,
    height: int | None = None,
) -> ActionProposal:
    """Validate a structured action against the current environment contract."""
    raw_action = payload.get("action")
    if isinstance(raw_action, bool) or not isinstance(raw_action, int):
        raise ActionValidationError("action must be an integer id")

    allowed = set(_strict_action_ids(available_action_ids))
    if raw_action not in allowed:
        raise ActionValidationError("action is not currently available")

    raw_data = payload.get("data", {})
    if raw_data is None:
        raw_data = {}
    if not isinstance(raw_data, dict):
        raise ActionValidationError("data must be a JSON object")

    data: dict[str, int] = {}
    if raw_action in complex_action_ids:
        if width is None or height is None or width <= 0 or height <= 0:
            raise ActionValidationError("complex action requires valid frame bounds")

        valid_width = min(width, ARC_ACTION_COORDINATE_LIMIT)
        valid_height = min(height, ARC_ACTION_COORDINATE_LIMIT)

        x = raw_data.get("x")
        y = raw_data.get("y")
        if (
            isinstance(x, bool)
            or isinstance(y, bool)
            or not isinstance(x, int)
            or not isinstance(y, int)
        ):
            raise ActionValidationError("complex action requires integer x and y")
        if not 0 <= x < valid_width or not 0 <= y < valid_height:
            raise ActionValidationError("coordinates are outside ARC/frame bounds")
        data = {"x": x, "y": y}

    reason = payload.get("reason", "")
    if reason is None:
        reason = ""
    if not isinstance(reason, str):
        raise ActionValidationError("reason must be a string")

    return ActionProposal(action_id=raw_action, data=data, reason=reason)


def deterministic_fallback(available_action_ids: Sequence[int]) -> int:
    """Return a stable legal fallback action id."""
    action_ids = _strict_action_ids(available_action_ids)
    if not action_ids:
        raise ActionValidationError("no actions are available")
    return min(action_ids)
