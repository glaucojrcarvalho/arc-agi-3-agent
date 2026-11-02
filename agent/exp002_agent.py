"""EXP-002: Qwen direct policy with verified transition feedback.

It retains the EXP-001 model/runtime contract, adding bounded memory of
action outcomes and a no-op guard only for exact same-state transitions.
It does not use game IDs, hardcoded puzzles, APIs or private evaluation data.
"""
from __future__ import annotations

from typing import Any

from arcengine import FrameData, GameAction, GameState
from agents.agent import Agent

from arc_agent.actions import (
    ActionValidationError,
    parse_action_json,
    validate_action_proposal,
)
from arc_agent.model import LocalChatModel, build_policy_prompt
from arc_agent.transition_policy import TransitionPolicy


class MyAgent(Agent):
    ACTION_COORDINATE_LIMIT = 64

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._model: LocalChatModel | None = None
        self._feedback = TransitionPolicy(memory_limit=6, state_limit=256)
        self.model_calls = 0
        self.validation_fallbacks = 0

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            self._feedback.on_reset()
            return GameAction.RESET

        action_ids = self._available_action_ids(latest_frame)
        if not action_ids:
            raise RuntimeError("environment exposed no executable actions")
        complex_ids = set(self._complex_action_ids(action_ids))
        width, height = self._frame_bounds(latest_frame)
        frame = latest_frame.frame or []
        level = int(getattr(latest_frame, "levels_completed", 0) or 0)
        state = getattr(latest_frame.state, "name", str(latest_frame.state))

        fingerprint = self._feedback.observe(frame=frame, level=level, state=state)
        prompt = build_policy_prompt(
            frame=frame,
            state=state,
            levels_completed=level,
            available_action_ids=action_ids,
            complex_action_ids=sorted(complex_ids),
            width=width,
            height=height,
            transition_feedback=self._feedback.feedback(),
            blocked_actions=self._feedback.blocked(level=level, fingerprint=fingerprint),
        )

        model = self._get_model()
        self.model_calls += 1
        raw_response = model.complete(prompt)

        proposed: tuple[int, dict[str, int]] | None = None
        reason = ""
        try:
            proposal = validate_action_proposal(
                parse_action_json(raw_response),
                available_action_ids=action_ids,
                complex_action_ids=complex_ids,
                width=width,
                height=height,
            )
            proposed = proposal.action_id, proposal.data
            reason = proposal.reason
        except ActionValidationError:
            self.validation_fallbacks += 1
            reason = "invalid-model-action"

        action_id, data, redirected = self._feedback.redirect(
            level=level,
            fingerprint=fingerprint,
            action_ids=action_ids,
            complex_action_ids=complex_ids,
            width=width,
            height=height,
            proposed=proposed,
        )
        self._feedback.record(
            frame=frame, level=level, state=state, action_id=action_id, data=data
        )
        action = GameAction.from_id(action_id)
        if action.is_complex():
            action.set_data(data)
        action.reasoning = {
            "policy": "exp-002-transition-aware",
            "model": model.model,
            "redirected": redirected,
            "reason": reason,
            "model_calls": self.model_calls,
            "validation_fallbacks": self.validation_fallbacks,
            "proven_noops": self._feedback.proven_noops,
            "level_progress_events": self._feedback.progress_events,
        }
        return action

    def _get_model(self) -> LocalChatModel:
        if self._model is None:
            self._model = LocalChatModel.from_env()
        return self._model

    def _available_action_ids(self, latest_frame: FrameData) -> list[int]:
        valid: list[int] = []
        for action_id in getattr(latest_frame, "available_actions", None) or []:
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
