"""Bounded, game-agnostic action feedback for the ARC-AGI-3 model policy.

No private game IDs, external services, or public-game solutions are used.
A no-op is proven only when the visible frame, level and game state match
exactly before and after a move. This is a conservative approximation: it
does not equate visual changes with progress.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Sequence

from .state import Frame, diff_frames, frame_fingerprint


@dataclass(frozen=True)
class PendingAction:
    level: int
    state: str
    before: tuple[tuple[tuple[int, ...], ...], ...]
    fingerprint: str
    action_id: int
    data: tuple[tuple[str, int], ...]


def freeze_frame(frame: Frame) -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Own the previous observation even if the game engine reuses buffers."""
    return tuple(
        tuple(tuple(int(value) for value in row) for row in layer)
        for layer in frame
    )


class TransitionPolicy:
    """Per-game transition monitor, bounded feedback, and no-op rejection."""

    def __init__(self, *, memory_limit: int = 6, state_limit: int = 256) -> None:
        if memory_limit <= 0 or state_limit <= 0:
            raise ValueError("history bounds must be positive")
        self._memory: deque[dict[str, Any]] = deque(maxlen=memory_limit)
        self._blocked: dict[tuple[int, str], set[tuple[int, tuple[tuple[str, int], ...]]]] = {}
        self._state_fifo: deque[tuple[int, str]] = deque()
        self._state_limit = state_limit
        self._pending: PendingAction | None = None
        self._level: int | None = None
        self.turns = 0
        self.proven_noops = 0
        self.redirects = 0
        self.progress_events = 0

    @staticmethod
    def _key(action_id: int, data: dict[str, int]) -> tuple[int, tuple[tuple[str, int], ...]]:
        return (action_id, tuple(sorted(data.items())))

    def observe(self, *, frame: Frame, level: int, state: str) -> str:
        """Consume the outcome of the preceding action, if one was recorded."""
        frozen = freeze_frame(frame)
        fingerprint = frame_fingerprint(frozen)
        pending = self._pending
        self._pending = None

        if pending is not None:
            delta = diff_frames(pending.before, frozen)
            progressed = level > pending.level
            same = (
                level == pending.level
                and state == pending.state
                and fingerprint == pending.fingerprint
            )
            if same:
                state_key = (pending.level, pending.fingerprint)
                if state_key not in self._blocked:
                    if len(self._state_fifo) >= self._state_limit:
                        evicted = self._state_fifo.popleft()
                        self._blocked.pop(evicted, None)
                    self._state_fifo.append(state_key)
                    self._blocked[state_key] = set()
                self._blocked[state_key].add((pending.action_id, pending.data))
                self.proven_noops += 1
            if progressed:
                self.progress_events += 1
                self._blocked.clear()
                self._state_fifo.clear()
            self._memory.append({
                "action": pending.action_id,
                "data": dict(pending.data),
                "changed_cells": delta.changed_cells,
                "levels_delta": level - pending.level,
                "state_changed": state != pending.state,
                "proven_noop": same,
            })
        self._level = level
        return fingerprint

    def feedback(self) -> list[dict[str, Any]]:
        return list(self._memory)

    def blocked(self, *, level: int, fingerprint: str) -> list[dict[str, Any]]:
        blocked = self._blocked.get((level, fingerprint), set())
        return [
            {"action": action, "data": dict(data)}
            for action, data in sorted(blocked)
        ]

    def is_blocked(
        self, *, level: int, fingerprint: str, action_id: int, data: dict[str, int]
    ) -> bool:
        return self._key(action_id, data) in self._blocked.get((level, fingerprint), set())

    @staticmethod
    def _candidate_coordinates(width: int, height: int) -> list[dict[str, int]]:
        """Small spread of generic exploratory points, never game-specific."""
        if width <= 0 or height <= 0:
            return []
        points = [
            (width // 2, height // 2),
            (width // 4, height // 4),
            ((3 * width) // 4, height // 4),
            (width // 4, (3 * height) // 4),
            ((3 * width) // 4, (3 * height) // 4),
            (0, 0),
            (width - 1, height - 1),
        ]
        seen: set[tuple[int, int]] = set()
        result: list[dict[str, int]] = []
        for x, y in points:
            point = (min(width - 1, x), min(height - 1, y))
            if point not in seen:
                seen.add(point)
                result.append({"x": point[0], "y": point[1]})
        return result

    def redirect(
        self,
        *,
        level: int,
        fingerprint: str,
        action_ids: Sequence[int],
        complex_action_ids: set[int],
        width: int,
        height: int,
        proposed: tuple[int, dict[str, int]] | None,
    ) -> tuple[int, dict[str, int], bool]:
        """Accept a novel legal proposal, otherwise explore without another LLM call."""
        if proposed is not None:
            action_id, data = proposed
            if not self.is_blocked(level=level, fingerprint=fingerprint, action_id=action_id, data=data):
                return action_id, data, False

        options: list[tuple[int, dict[str, int]]] = []
        for action_id in sorted(set(action_ids)):
            if action_id in complex_action_ids:
                for point in self._candidate_coordinates(width, height):
                    options.append((action_id, point))
            else:
                options.append((action_id, {}))

        if not options:
            raise ValueError("no legal actions to select")

        # Rotate candidates so malformed responses do not always select ACTION1.
        start = self.turns % len(options)
        rotated = options[start:] + options[:start]
        for action_id, data in rotated:
            if not self.is_blocked(level=level, fingerprint=fingerprint, action_id=action_id, data=data):
                self.redirects += 1
                return action_id, data, True

        # Every explored candidate is known ineffective in this exact state.
        # Degrade to a legal action rather than attempting a potentially unsafe reset.
        self.redirects += 1
        action_id, data = rotated[0]
        return action_id, data, True

    def record(
        self, *, frame: Frame, level: int, state: str, action_id: int, data: dict[str, int]
    ) -> None:
        frozen = freeze_frame(frame)
        self._pending = PendingAction(
            level=level,
            state=state,
            before=frozen,
            fingerprint=frame_fingerprint(frozen),
            action_id=action_id,
            data=tuple(sorted(data.items())),
        )
        self.turns += 1

    def on_reset(self) -> None:
        """A restart invalidates one-step observations, not all learned failures."""
        self._pending = None
