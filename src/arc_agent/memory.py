"""Compact transition memory for action-effect analysis."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .state import Frame, diff_frames, frame_fingerprint


@dataclass(frozen=True)
class Transition:
    action_id: int
    before_fingerprint: str
    after_fingerprint: str
    changed_cells: int
    change_ratio: float
    levels_delta: int
    state_changed: bool

    @property
    def effectful(self) -> bool:
        """Whether the action produced any observable transition.

        This deliberately does not imply that the transition was beneficial.
        A death/game-over transition is effectful, but it is not progress.
        """
        return self.changed_cells > 0 or self.levels_delta != 0 or self.state_changed

    @property
    def progressed(self) -> bool:
        """Whether the transition increased completed-level count."""
        return self.levels_delta > 0


@dataclass(frozen=True)
class ActionStats:
    attempts: int
    effectful_attempts: int
    total_changed_cells: int
    progress_attempts: int

    @property
    def effect_rate(self) -> float:
        return self.effectful_attempts / self.attempts if self.attempts else 0.0

    @property
    def progress_rate(self) -> float:
        return self.progress_attempts / self.attempts if self.attempts else 0.0

    @property
    def mean_changed_cells(self) -> float:
        return self.total_changed_cells / self.attempts if self.attempts else 0.0


class TransitionMemory:
    """Bounded in-memory history of observed action effects."""

    def __init__(self, maxlen: int = 64) -> None:
        if maxlen <= 0:
            raise ValueError("maxlen must be positive")
        self._transitions: deque[Transition] = deque(maxlen=maxlen)

    def __len__(self) -> int:
        return len(self._transitions)

    @property
    def transitions(self) -> tuple[Transition, ...]:
        return tuple(self._transitions)

    def record(
        self,
        *,
        action_id: int,
        before_frame: Frame,
        after_frame: Frame,
        before_levels: int = 0,
        after_levels: int = 0,
        before_state: object | None = None,
        after_state: object | None = None,
    ) -> Transition:
        delta = diff_frames(before_frame, after_frame)
        transition = Transition(
            action_id=action_id,
            before_fingerprint=frame_fingerprint(before_frame),
            after_fingerprint=frame_fingerprint(after_frame),
            changed_cells=delta.changed_cells,
            change_ratio=delta.change_ratio,
            levels_delta=after_levels - before_levels,
            state_changed=before_state != after_state,
        )
        self._transitions.append(transition)
        return transition

    def stats(self, action_id: int) -> ActionStats:
        selected = [item for item in self._transitions if item.action_id == action_id]
        return ActionStats(
            attempts=len(selected),
            effectful_attempts=sum(item.effectful for item in selected),
            total_changed_cells=sum(item.changed_cells for item in selected),
            progress_attempts=sum(item.progressed for item in selected),
        )
