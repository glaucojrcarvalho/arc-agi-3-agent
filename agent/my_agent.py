"""Minimal ARC-AGI-3 policy baseline.

This implementation is intentionally simple. Its purpose is to validate the
end-to-end environment and submission pipeline before adding learned policies,
memory, or planning.

The class follows the public Agent interface from:
https://github.com/arcprize/ARC-AGI-3-Agents
"""

from __future__ import annotations

import hashlib
import random
from typing import Any

from arcengine import FrameData, GameAction, GameState
from agents.agent import Agent


class MyAgent(Agent):
    """Reproducible random-action baseline for pipeline validation."""

    ACTION_COORDINATE_LIMIT = 64

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        digest = hashlib.sha256(self.game_id.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], byteorder="big", signed=False)
        self._rng = random.Random(seed)

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Stop only after the environment reports a win."""
        return latest_frame.state is GameState.WIN

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose among actions exposed by the current environment state."""
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET

        candidates = self._available_actions(latest_frame)
        action = self._rng.choice(candidates)

        if action.is_complex():
            action.set_data(self._random_coordinates(latest_frame))

        action.reasoning = {
            "policy": "reproducible-random-baseline",
            "history_length": len(frames),
            "candidate_actions": len(candidates),
        }
        return action

    def _available_actions(self, latest_frame: FrameData) -> list[GameAction]:
        """Convert valid integer action ids into GameAction values when available."""
        action_ids = getattr(latest_frame, "available_actions", None) or []
        candidates: list[GameAction] = []

        for action_id in action_ids:
            if isinstance(action_id, bool) or not isinstance(action_id, int):
                continue
            try:
                action = GameAction.from_id(action_id)
            except (TypeError, ValueError):
                continue
            if action is not GameAction.RESET:
                candidates.append(action)

        if candidates:
            return candidates

        return [action for action in GameAction if action is not GameAction.RESET]

    def _random_coordinates(self, latest_frame: FrameData) -> dict[str, int]:
        """Sample valid ACTION6 coordinates, respecting frame and ARC bounds."""
        frame = latest_frame.frame or []

        if frame and frame[0] and frame[0][0]:
            observed_height = len(frame[0])
            observed_width = len(frame[0][0])
            height = max(1, min(observed_height, self.ACTION_COORDINATE_LIMIT))
            width = max(1, min(observed_width, self.ACTION_COORDINATE_LIMIT))
        else:
            height = width = self.ACTION_COORDINATE_LIMIT

        return {
            "x": self._rng.randrange(width),
            "y": self._rng.randrange(height),
        }
