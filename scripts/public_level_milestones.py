"""Record the earliest action at which each PUBLIC game level was completed.

For local fake-model evaluation only; these observations are not ARC RHAE
scores, hidden-game trajectories or Kaggle competition results.
"""
from __future__ import annotations


def record_milestones(
    milestones: dict[int, int], *,
    highest_level: int, observed_level: int, action_index: int,
) -> int:
    for value in (highest_level, observed_level, action_index):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("level/action counters must be nonnegative integers")
    if action_index == 0:
        raise ValueError("a completed action must have an index >= 1")
    if observed_level > highest_level:
        for level in range(highest_level + 1, observed_level + 1):
            milestones.setdefault(level, action_index)
    return max(highest_level, observed_level)
