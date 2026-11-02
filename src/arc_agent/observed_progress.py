"""Game-local, bounded observation of authoritative level progress.

These action sequences preceded level changes; they do not establish
mechanics, causal effects, or transfer to other levels.
"""
from __future__ import annotations
from collections import deque
from copy import deepcopy
from typing import Any, Mapping

class ObservedProgressMemory:
    def __init__(self, *, max_levels: int = 3, max_steps: int = 4) -> None:
        if not 1 <= max_levels <= 8 or not 1 <= max_steps <= 12:
            raise ValueError("invalid observed-progress bounds")
        self._completed: deque[dict[str, Any]] = deque(maxlen=max_levels)
        self._recent: deque[dict[str, Any]] = deque(maxlen=max_steps)
        self._level: int | None = None
        self.progress_observations = 0

    @staticmethod
    def _safe_step(t: Mapping[str, Any]) -> dict[str, Any] | None:
        action = t.get("action")
        if type(action) is not int or not 0 <= action <= 7:
            return None
        data = t.get("data", {})
        safe_data = {}
        if isinstance(data, dict):
            for key in ("x", "y"):
                v = data.get(key)
                if type(v) is int and 0 <= v < 64:
                    safe_data[key] = v
        cells = t.get("changed_cells")
        return {
            "action": action, "data": safe_data,
            "observed_changed_cells": (
                min(cells, 4096) if type(cells) is int and cells >= 0 else None
            ),
            "observed_noop": t.get("proven_noop") is True,
        }

    def observe(self, *, level: int, transition: Mapping[str, Any] | None) -> None:
        if type(level) is not int or level < 0:
            raise ValueError("invalid observed level")
        if self._level is None:
            self._level = level
            return
        if level < self._level:
            self.on_reset()
            self._level = level
            return
        if level > self._level:
            delta = transition.get("levels_delta") if transition else None
            last = self._safe_step(transition) if transition else None
            if type(delta) is int and delta == level - self._level and last:
                self._completed.append({
                    "from_level": self._level, "to_level": level,
                    "observed_steps_before_completion":
                        [*self._recent, last][-self._recent.maxlen:],
                })
                self.progress_observations += 1
            self._recent.clear()
        elif transition is not None and transition.get("levels_delta") == 0:
            step = self._safe_step(transition)
            if step is not None:
                self._recent.append(step)
        self._level = level

    def prompt_context(self) -> dict[str, Any]:
        return {
            "evidence_type": "environment_levels_completed_increase",
            "causality_warning": (
                "These actions were observed before a completed level. "
                "They do not prove mechanics, causation, or transfer; "
                "verify hypotheses on the current board."
            ),
            # Caller-owned snapshots must not mutate evidence kept for later levels.
            "completed_level_traces": deepcopy(list(self._completed)),
        }

    def on_reset(self) -> None:
        self._completed.clear()
        self._recent.clear()
        self._level = None
        self.progress_observations = 0
