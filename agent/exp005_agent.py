"""EXP-005: persistent hypotheses, short action plans, spatial feedback.

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
from arc_agent.perception import salient_click_targets
from arc_agent.transition_policy import TransitionPolicy
from arc_agent.reasoning_memory import ReasoningMemory
from arc_agent.novelty_explorer import NoveltyExplorer


class MyAgent(Agent):
    ACTION_COORDINATE_LIMIT = 64
    # Early exploration for coordinate-only controls avoids repeated expensive
    # LLM clicks; retain longer planning for directional/keyboard puzzles.
    COMPLEX_NOVELTY_AFTER = 8
    KEYBOARD_NOVELTY_AFTER = 16
    COMPLEX_MODEL_REFRESH_EVERY = 8
    KEYBOARD_MODEL_REFRESH_EVERY = 12

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._model: LocalChatModel | None = None
        self._feedback = TransitionPolicy(memory_limit=6, state_limit=256, click_cooldown=8)
        self._belief = ReasoningMemory(max_planned_actions=2, max_stagnation=16)
        self._last_processed_turn = 0
        self._last_progress_events = 0
        self._explorer = NoveltyExplorer(self.game_id)
        self.model_calls = 0
        self.validation_fallbacks = 0

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            self._feedback.on_reset()
            self._belief.on_reset()
            self._last_processed_turn = self._feedback.turns
            return GameAction.RESET

        action_ids = self._available_action_ids(latest_frame)
        if not action_ids:
            raise RuntimeError("environment exposed no executable actions")
        complex_ids = set(self._complex_action_ids(action_ids))
        width, height = self._frame_bounds(latest_frame)
        frame = latest_frame.frame or []
        # ARC frame[0..N] is an animation; only frame[-1] is the settled
        # post-action board. Do not treat a changing animation length as
        # a different game state or as level progress.
        settled_frame = frame[-1:] if frame else []
        level = int(getattr(latest_frame, "levels_completed", 0) or 0)
        state = getattr(latest_frame.state, "name", str(latest_frame.state))

        fingerprint = self._feedback.observe(frame=settled_frame, level=level, state=state)
        if self._feedback.progress_events != self._last_progress_events:
            self._last_progress_events = self._feedback.progress_events
            self._explorer.progress()
        recent_transitions = self._feedback.feedback()
        newly_observed = self._feedback.turns != self._last_processed_turn
        self._last_processed_turn = self._feedback.turns
        self._belief.max_stagnation = (
            self.COMPLEX_NOVELTY_AFTER if complex_ids else self.KEYBOARD_NOVELTY_AFTER
        )
        self._belief.observe(
            level=level,
            state=state,
            latest_transition=(
                recent_transitions[-1]
                if newly_observed and recent_transitions else None
            ),
        )
        click_targets = (
            salient_click_targets(settled_frame, max_targets=24) if complex_ids else []
        )
        model = self._get_model()
        stuck = self._belief.steps_without_progress >= self._belief.max_stagnation
        refresh_period = (
            self.COMPLEX_MODEL_REFRESH_EVERY if complex_ids
            else self.KEYBOARD_MODEL_REFRESH_EVERY
        )
        heuristic_step = stuck and self._belief.steps_without_progress % refresh_period != 0
        if heuristic_step:
            self._belief.abort_plan()
        plan_step = (
            None if heuristic_step
            else self._belief.take_plan(legal_actions=action_ids)
        )
        proposed: tuple[int, dict[str, int]] | None = None
        reason = ""
        planned_action = plan_step is not None
        if heuristic_step:
            proposed = self._explorer.choose(
                fingerprint=fingerprint,
                legal_actions=action_ids,
                complex_action_ids=complex_ids,
                candidates=click_targets,
                width=width,
                height=height,
            )
            reason = "model-free-state-novelty-exploration"
        elif plan_step is not None:
            proposed = plan_step
            reason = "validated-keyboard-plan"
        else:
            prompt = build_policy_prompt(
                frame=frame,
                state=state,
                levels_completed=level,
                available_action_ids=action_ids,
                complex_action_ids=sorted(complex_ids),
                width=width,
                height=height,
                transition_feedback=recent_transitions,
                blocked_actions=self._feedback.blocked(level=level, fingerprint=fingerprint),
                frame_representation="bounded_animation",
                click_candidates=click_targets if complex_ids else None,
                recent_click_cooldowns=(
                    self._feedback.cooled_clicks(level) if complex_ids else None
                ),
                reasoning_context=self._belief.prompt_context(),
            )

            self.model_calls += 1
            raw_response = model.complete(prompt)
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
                self._belief.absorb(
                    raw_response,
                    legal_actions=action_ids,
                    complex_action_ids=complex_ids,
                    width=width,
                    height=height,
                )
            except ActionValidationError:
                self.validation_fallbacks += 1
                self._belief.abort_plan()
                reason = "invalid-model-action"

        action_id, data, redirected = self._feedback.redirect(
            level=level,
            fingerprint=fingerprint,
            action_ids=action_ids,
            complex_action_ids=complex_ids,
            width=width,
            height=height,
            proposed=proposed,
            candidate_coordinates=click_targets,
        )
        if redirected:
            self._belief.abort_plan()
        self._feedback.record(
            frame=settled_frame, level=level, state=state, action_id=action_id, data=data
        )
        self._explorer.note_action(
            fingerprint=fingerprint, action_id=action_id, data=data
        )
        action = GameAction.from_id(action_id)
        if action.is_complex():
            action.set_data(data)
        action.reasoning = {
            "policy": "exp-005-belief-and-novelty",
            "model": model.model,
            "redirected": redirected,
            "reason": reason,
            "spatial_candidates": len(click_targets),
            "animation_frame_count": len(frame),
            "recent_click_cooldown_count": len(self._feedback.cooled_clicks(level)),
            "model_calls": self.model_calls,
            "planned_action": planned_action,
            "heuristic_step": heuristic_step,
            "heuristic_calls": self._explorer.heuristic_calls,
            "plan_actions_taken": self._belief.plan_actions_taken,
            "belief_revisions": self._belief.belief_revisions,
            "stagnation_events": self._belief.stagnation_events,
            "novelty_after_steps": self._belief.max_stagnation,
            "model_refresh_every": refresh_period,
            "steps_without_progress": self._belief.steps_without_progress,
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
        if frame and frame[-1] and frame[-1][0]:
            height = max(1, min(len(frame[-1]), self.ACTION_COORDINATE_LIMIT))
            width = max(1, min(len(frame[-1][0]), self.ACTION_COORDINATE_LIMIT))
            return width, height
        return self.ACTION_COORDINATE_LIMIT, self.ACTION_COORDINATE_LIMIT
