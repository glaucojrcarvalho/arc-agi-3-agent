"""Deterministic, model-free novelty exploration after prolonged stagnation.

Never embeds public puzzle solutions, hidden evaluation data or game IDs as
rules. SHA256(game_id) is solely a reproducible random seed.
"""
from __future__ import annotations

import hashlib
import random
from collections import Counter, deque
from typing import Sequence


class NoveltyExplorer:
    def __init__(self, game_id: str, *, recent_clicks: int = 12) -> None:
        if not 1 <= recent_clicks <= 32:
            raise ValueError("recent_clicks must be between 1 and 32")
        seed = int.from_bytes(
            hashlib.sha256(game_id.encode("utf-8")).digest()[:8], "big"
        )
        self._rng = random.Random(seed)
        self._visits: Counter[tuple[str, int]] = Counter()
        self._recent_points: deque[tuple[int, int]] = deque(maxlen=recent_clicks)
        # Remember attempted (visible state, action, coordinate) combinations,
        # with bounded memory independent of the LLM feedback window.
        self._state_click_attempts: Counter[tuple[str, int, int, int]] = Counter()
        self._click_history: deque[tuple[str, int, int, int]] = deque()
        self._click_history_limit = 256
        self.heuristic_calls = 0
        self.progress_resets = 0

    def note_action(
        self, *, fingerprint: str, action_id: int, data: dict[str, int]
    ) -> None:
        self._visits[(fingerprint, action_id)] += 1
        if "x" in data and "y" in data:
            self._recent_points.append((data["x"], data["y"]))
            key = (fingerprint, action_id, data["x"], data["y"])
            if len(self._click_history) == self._click_history_limit:
                old_key = self._click_history.popleft()
                self._state_click_attempts[old_key] -= 1
                if self._state_click_attempts[old_key] == 0:
                    del self._state_click_attempts[old_key]
            self._click_history.append(key)
            self._state_click_attempts[key] += 1

    def progress(self) -> None:
        self._visits.clear()
        self._recent_points.clear()
        self._state_click_attempts.clear()
        self._click_history.clear()
        self.progress_resets += 1

    def choose(
        self,
        *,
        fingerprint: str,
        legal_actions: Sequence[int],
        complex_action_ids: set[int],
        candidates: Sequence[dict[str, int]],
        width: int,
        height: int,
    ) -> tuple[int, dict[str, int]]:
        actions = sorted(set(legal_actions))
        if not actions or width < 1 or height < 1:
            raise ValueError("no legal action or invalid frame bounds")
        # Fewest visits to (exact frame, action ID), random tie break.
        ranked = [
            (self._visits[(fingerprint, action)], self._rng.random(), action)
            for action in actions
        ]
        action = min(ranked)[2]
        data: dict[str, int] = {}
        if action in complex_action_ids:
            points = [
                (target["x"], target["y"])
                for target in candidates
                if (
                    isinstance(target.get("x"), int)
                    and not isinstance(target.get("x"), bool)
                    and isinstance(target.get("y"), int)
                    and not isinstance(target.get("y"), bool)
                    and 0 <= target["x"] < width
                    and 0 <= target["y"] < height
                )
            ]
            self._rng.shuffle(points)
            unique_points = list(dict.fromkeys(points))
            if not unique_points or self._rng.random() < .20:
                point = (self._rng.randrange(width), self._rng.randrange(height))
            else:
                # Prefer an untried point in this *exact* visible state, then
                # avoid recent clicks to break deterministic short loops.
                count = lambda p: self._state_click_attempts[
                    (fingerprint, action, p[0], p[1])
                ]
                min_attempts = min(map(count, unique_points))
                eligible = [p for p in unique_points if count(p) == min_attempts]
                novel = [p for p in eligible if p not in self._recent_points]
                point = (novel or eligible)[0]
            data = {"x": point[0], "y": point[1]}
        self.heuristic_calls += 1
        return action, data
