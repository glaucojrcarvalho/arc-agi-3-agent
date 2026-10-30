"""EXP-001 direct-model policy for ARC-AGI-3.

This experiment intentionally uses only the current observation, the current
environment state, and the currently legal action set. It does not use
persistent transition memory, reflection, search, or game-specific rules.
"""

from __future__ import annotations

from typing import Any

from arcengine import FrameData, GameAction, GameState
from agents.agent import Agent

from arc_agent.actions import (
    ActionValidationError,
    deterministic_fallback,
    parse_action_json,
    validate_action_proposal,
)
from arc_agent.model import LocalChatModel, build_policy_prompt


class MyAgent(Agent):
    """Direct local-model policy with strict action validation."""

    ACTION_COORDINATE_LIMIT = 64

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._model: LocalChatModel | None = None
        self.model_calls = 0
        self.validation_fallbacks = 0

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Stop only after the environment reports a win."""
        return latest_frame.state is GameState.WIN

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose one action from the current observation using the local model."""
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET

        available_action_ids = self._available_action_ids(latest_frame)
        if not available_action_ids:
            raise RuntimeError("environment exposed no executable actions")

        complex_action_ids = self._complex_action_ids(available_action_ids)
        width, height = self._frame_bounds(latest_frame)

        prompt = build_policy_prompt(
            frame=latest_frame.frame or [],
            state=getattr(latest_frame.state, "name", str(latest_frame.state)),
            levels_completed=int(getattr(latest_frame, "levels_completed", 0) or 0),
            available_action_ids=available_action_ids,
            complex_action_ids=complex_action_ids,
            width=width,
            height=height,
        )

        model = self._get_model()
        self.model_calls += 1
        raw_response = model.complete(prompt)

        used_fallback = False
        reason = ""
        try:
            proposal = validate_action_proposal(
                parse_action_json(raw_response),
                available_action_ids=available_action_ids,
                complex_action_ids=set(complex_action_ids),
                width=width,
                height=height,
            )
            action_id = proposal.action_id
            action_data = proposal.data
            reason = proposal.reason
        except ActionValidationError:
            used_fallback = True
            self.validation_fallbacks += 1
            action_id = deterministic_fallback(available_action_ids)
            action_data = {"x": 0, "y": 0} if action_id in complex_action_ids else {}
            reason = "deterministic-validation-fallback"

        action = GameAction.from_id(action_id)
        if action.is_complex():
            action.set_data(action_data)

        action.reasoning = {
            "policy": "exp-001-direct-model",
            "model": model.model,
            "fallback": used_fallback,
            "reason": reason,
            "model_calls": self.model_calls,
            "validation_fallbacks": self.validation_fallbacks,
        }
        return action

    def _get_model(self) -> LocalChatModel:
        if self._model is None:
            self._model = LocalChatModel.from_env()
        return self._model

    def _available_action_ids(self, latest_frame: FrameData) -> list[int]:
        action_ids = getattr(latest_frame, "available_actions", None) or []
        valid: list[int] = []

        for action_id in action_ids:
            if isinstance(action_id, bool) or not isinstance(action_id, int):
                continue
            try:
                action = GameAction.from_id(action_id)
            except (TypeError, ValueError):
                continue
            if action is not GameAction.RESET:
                valid.append(action_id)

        return valid

    def _complex_action_ids(self, action_ids: list[int]) -> list[int]:
        return [
            action_id
            for action_id in action_ids
            if GameAction.from_id(action_id).is_complex()
        ]

    def _frame_bounds(self, latest_frame: FrameData) -> tuple[int, int]:
        frame = latest_frame.frame or []
        if frame and frame[0] and frame[0][0]:
            height = max(1, min(len(frame[0]), self.ACTION_COORDINATE_LIMIT))
            width = max(1, min(len(frame[0][0]), self.ACTION_COORDINATE_LIMIT))
            return width, height

        return self.ACTION_COORDINATE_LIMIT, self.ACTION_COORDINATE_LIMIT
