"""Pure, dependency-free authoritative level-completion accounting.

Pixel changes are never progress. Kept out of ARC SDK imports so evaluation
protocol regressions can be tested in the public GitHub Actions runner.
"""
from __future__ import annotations


def record_level_milestones(
    max_level_seen: int, observed_level: int, action_index: int,
    milestones: list[int],
) -> int:
    """Append completion indices once; ignore level-counter resets or pixels."""
    if not all(
        isinstance(n, int) and not isinstance(n, bool) and n >= 0
        for n in (max_level_seen, observed_level, action_index)
    ):
        raise ValueError("level counters and action index must be nonnegative integers")
    if observed_level > max_level_seen:
        milestones.extend([action_index] * (observed_level - max_level_seen))
    return max(max_level_seen, observed_level)
