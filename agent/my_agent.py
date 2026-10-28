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
from arc_agent.memory import TransitionMemory
from arc_agent.model import LocalChatModel, build_policy_prompt
from arc_agent.state import frame_fingerprint


class MyAgent(Agent):
    """Direct local-model policy with strict action validation."""

    ACTION_COORDINATE_LIMIT = 64

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._model: LocalChatModel | None = None
        self.model_calls = 0
        self.validation_fallbacks = 0
        self.transition_memory = TransitionMemory(maxlen=64)
        self._pending_action_id: int | None = None
        self._pending_frame: tuple[tuple[tuple[int, ...], ...], ...] | None = None
        self._pending_levels = 0
        self._pending_state: object | None = None

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
            self._clear_pending_transition()
            return GameAction.RESET

        self._record_pending_transition(latest_frame)

        available_action_ids = self._available_action_ids(latest_frame)
        if not available_action_ids:
            raise RuntimeError("environment exposed no executable actions")

        suppressed_action_ids = self._suppressed_noop_actions(
            latest_frame,
            available_action_ids,
        )
        policy_action_ids = [
            action_id
            for action_id in available_action_ids
            if action_id not in suppressed_action_ids
        ]
        if not policy_action_ids:
            policy_action_ids = available_action_ids
            suppressed_action_ids = []

        complex_action_ids = self._complex_action_ids(policy_action_ids)
        width, height = self._frame_bounds(latest_frame)

        prompt = build_policy_prompt(
            frame=latest_frame.frame or [],
            state=getattr(latest_frame.state, "name", str(latest_frame.state)),
            levels_completed=int(getattr(latest_frame, "levels_completed", 0) or 0),
            available_action_ids=policy_action_ids,
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
                available_action_ids=policy_action_ids,
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
            action_id = deterministic_fallback(policy_action_ids)
            action_data = {"x": 0, "y": 0} if action_id in complex_action_ids else {}
            reason = "deterministic-validation-fallback"

        action = GameAction.from_id(action_id)
        if action.is_complex():
            action.set_data(action_data)

        self._remember_pending_action(action_id, latest_frame)

        action.reasoning = {
            "policy": "deadline-transition-aware-model",
            "model": model.model,
            "fallback": used_fallback,
            "reason": reason,
            "model_calls": self.model_calls,
            "validation_fallbacks": self.validation_fallbacks,
            "suppressed_noop_actions": suppressed_action_ids,
            "transition_count": len(self.transition_memory),
        }
        return action

    def _snapshot_frame(
        self,
        latest_frame: FrameData,
    ) -> tuple[tuple[tuple[int, ...], ...], ...]:
        frame = latest_frame.frame or []
        return tuple(
            tuple(
                tuple(int(value) for value in row)
                for row in layer
            )
            for layer in frame
        )

    def _clear_pending_transition(self) -> None:
        self._pending_action_id = None
        self._pending_frame = None
        self._pending_levels = 0
        self._pending_state = None

    def _record_pending_transition(self, latest_frame: FrameData) -> None:
        if self._pending_action_id is None or self._pending_frame is None:
            return

        self.transition_memory.record(
            action_id=self._pending_action_id,
            before_frame=self._pending_frame,
            after_frame=self._snapshot_frame(latest_frame),
            before_levels=self._pending_levels,
            after_levels=int(
                getattr(latest_frame, "levels_completed", 0) or 0
            ),
            before_state=self._pending_state,
            after_state=latest_frame.state,
        )
        self._clear_pending_transition()

    def _remember_pending_action(
        self,
        action_id: int,
        latest_frame: FrameData,
    ) -> None:
        self._pending_action_id = action_id
        self._pending_frame = self._snapshot_frame(latest_frame)
        self._pending_levels = int(
            getattr(latest_frame, "levels_completed", 0) or 0
        )
        self._pending_state = latest_frame.state

    def _suppressed_noop_actions(
        self,
        latest_frame: FrameData,
        available_action_ids: list[int],
    ) -> list[int]:
        current_fingerprint = frame_fingerprint(self._snapshot_frame(latest_frame))
        suppressed: list[int] = []

        for action_id in available_action_ids:
            action = GameAction.from_id(action_id)
            if action.is_complex():
                continue

            matching = [
                transition
                for transition in self.transition_memory.transitions
                if transition.action_id == action_id
                and transition.before_fingerprint == current_fingerprint
            ]
            if len(matching) >= 2 and all(
                not transition.effectful
                for transition in matching
            ):
                suppressed.append(action_id)

        return suppressed

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
