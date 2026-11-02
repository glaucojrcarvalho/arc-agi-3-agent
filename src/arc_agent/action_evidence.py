"""Bounded, game-independent action-attempt evidence for model reasoning.

This is descriptive history, not an action-selection heuristic. Only an
increase in the authoritative levels_completed field verifies progress.
A changed screenshot or a frequently used action cannot establish success
or failure. Pixel images, raw coordinates and game-specific rules are never
retained.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any


class ActionEvidence:
    """A small per-level ledger included only in the Qwen prompt."""

    def __init__(self, *, recent_limit: int = 12, spatial_limit: int = 8) -> None:
        if not 1 <= recent_limit <= 24 or not 1 <= spatial_limit <= 16:
            raise ValueError("invalid evidence bounds")
        self._recent: deque[int] = deque(maxlen=recent_limit)
        self._counts: Counter[int] = Counter()
        self._regions: Counter[tuple[int, int, int]] = Counter()
        self._level: int | None = None
        self._attempts = 0
        self._spatial_limit = spatial_limit

    def reset(self) -> None:
        self._recent.clear()
        self._counts.clear()
        self._regions.clear()
        self._attempts = 0
        self._level = None

    def observe_level(self, levels_completed: int) -> None:
        if isinstance(levels_completed, bool) or not isinstance(levels_completed, int):
            raise ValueError("levels_completed must be an integer")
        if levels_completed < 0:
            raise ValueError("levels_completed must be nonnegative")
        if self._level is not None and levels_completed != self._level:
            # Discard prior-level attempts both when a level is completed and
            # when a new game / restart changes the counter.
            self.reset()
        self._level = levels_completed

    def record(self, action_id: int, data: dict[str, int], *, width: int, height: int) -> None:
        if isinstance(action_id, bool) or not isinstance(action_id, int):
            raise ValueError("invalid action_id")
        if width < 1 or height < 1:
            raise ValueError("invalid frame dimensions")
        self._attempts += 1
        self._counts[action_id] += 1
        self._recent.append(action_id)
        x, y = data.get("x"), data.get("y")
        if (
            isinstance(x, int) and not isinstance(x, bool)
            and isinstance(y, int) and not isinstance(y, bool)
            and 0 <= x < width and 0 <= y < height
        ):
            # Normalized 4-by-4 sectors are enough to describe search effort.
            # Never persist stale exact click coordinates.
            self._regions[(action_id, (4*x)//width, (4*y)//height)] += 1

    def prompt_context(self) -> dict[str, Any]:
        controls = [
            {"action": action, "attempts": attempts}
            for action, attempts in sorted(self._counts.items())
        ]
        regions = [
            {"action": action, "sector_x": x, "sector_y": y, "attempts": count}
            for (action, x, y), count in sorted(
                self._regions.items(),
                key=lambda item: (-item[1], item[0]),
            )[:self._spatial_limit]
        ]
        return {
            "attempts_this_level": self._attempts,
            "control_attempts": controls,
            "recent_controls": list(self._recent),
            "most_attempted_click_sectors_4x4": regions,
            "evidence_caveat": (
                "Counts describe attempts, NOT success or failure. Repeating "
                "an action may be needed. Only an increase in levels_completed "
                "verifies level progress; changed pixels are not progress."
            ),
        }
