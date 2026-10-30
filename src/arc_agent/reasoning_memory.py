"""Compact persistent belief and bounded action plans for interactive puzzles.

The state is game-local. Hypotheses are model-generated guesses, not verified
facts; game observations remain the source of truth. No external APIs.
"""
from __future__ import annotations

import json
from collections import deque
from typing import Any, Mapping, Sequence

from .actions import ActionValidationError, validate_action_proposal


class ReasoningMemory:
    def __init__(self, *, max_planned_actions: int = 2, max_stagnation: int = 16) -> None:
        if not 0 <= max_planned_actions <= 4 or max_stagnation < 1:
            raise ValueError("invalid reasoning memory bounds")
        self.max_planned_actions = max_planned_actions
        self.max_stagnation = max_stagnation
        self.goal = ""
        self.hypothesis = ""
        self._plans: deque[tuple[int, dict[str, int]]] = deque()
        self._level: int | None = None
        self.steps_without_progress = 0
        self.plan_actions_taken = 0
        self.belief_revisions = 0
        self.plan_interruptions = 0
        self.stagnation_events = 0
        self._stagnation_reported = False

    def observe(
        self,
        *,
        level: int,
        state: str,
        latest_transition: Mapping[str, Any] | None,
    ) -> None:
        if self._level is None:
            self._level = level
            return
        if level > self._level:
            self._plans.clear()
            self.goal = ""
            self.hypothesis = ""
            self.steps_without_progress = 0
            self._stagnation_reported = False
            self._level = level
            return
        self._level = level
        if latest_transition is None:
            return
        self.steps_without_progress += 1
        # A plan is interrupted by an observed no-op or a terminal state
        # change. Large *nonzero* changes are not necessarily progress.
        if self._plans and (
            latest_transition.get("proven_noop") is True
            or latest_transition.get("state_changed") is True
        ):
            self._plans.clear()
            self.plan_interruptions += 1
        if self.steps_without_progress >= self.max_stagnation and not self._stagnation_reported:
            self._plans.clear()
            self.stagnation_events += 1
            self._stagnation_reported = True

    def prompt_context(self) -> dict[str, Any]:
        return {
            "unverified_goal_hypothesis": self.goal,
            "unverified_dynamics_hypothesis": self.hypothesis,
            "steps_without_level_progress": self.steps_without_progress,
            "remaining_planned_keyboard_actions": [
                {"action": action, "data": data} for action, data in self._plans
            ],
            "stagnation_warning": self.steps_without_progress >= self.max_stagnation,
            "instructions": (
                "Treat hypotheses as unverified. Revise them when observed "
                "transitions contradict them. Seek level completion rather "
                "than maximizing raw changed pixel counts."
            ),
        }

    @staticmethod
    def _short_text(value: Any, limit: int = 200) -> str | None:
        if not isinstance(value, str):
            return None
        # Prevent model output from growing the prompt unboundedly.
        compact = " ".join(value.split()).strip()
        return compact[:limit]

    def absorb(
        self,
        raw_response: str,
        *,
        legal_actions: Sequence[int],
        complex_action_ids: set[int],
        width: int,
        height: int,
    ) -> None:
        try:
            payload = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            self._plans.clear()
            return
        if not isinstance(payload, dict):
            self._plans.clear()
            return

        goal = self._short_text(payload.get("goal"))
        hypothesis = self._short_text(payload.get("hypothesis"))
        if goal is not None and goal != self.goal:
            self.goal = goal
            self.belief_revisions += 1
        if hypothesis is not None and hypothesis != self.hypothesis:
            self.hypothesis = hypothesis
            self.belief_revisions += 1

        self._plans.clear()
        plan = payload.get("next_actions")
        if not isinstance(plan, list):
            return
        for entry in plan[:self.max_planned_actions]:
            if not isinstance(entry, dict):
                continue
            try:
                proposal = validate_action_proposal(
                    entry,
                    available_action_ids=legal_actions,
                    complex_action_ids=complex_action_ids,
                    width=width,
                    height=height,
                )
            except ActionValidationError:
                continue
            # Coordinates are based on current frame and likely stale next
            # turn. Only pre-plan non-complex controls.
            if proposal.action_id not in complex_action_ids:
                self._plans.append((proposal.action_id, proposal.data))

    def take_plan(self, *, legal_actions: Sequence[int]) -> tuple[int, dict[str, int]] | None:
        while self._plans:
            action, data = self._plans.popleft()
            if action in legal_actions:
                self.plan_actions_taken += 1
                return action, data
        return None

    def abort_plan(self) -> None:
        if self._plans:
            self._plans.clear()
            self.plan_interruptions += 1

    def on_reset(self) -> None:
        self._plans.clear()
        self._level = None
        self.steps_without_progress = 0
        self._stagnation_reported = False
