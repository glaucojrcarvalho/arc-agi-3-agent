"""Deterministic controller RNG seed for *evaluation-only* public-game tests.

Keep this stdlib-only module importable by repository CI without arc_agi;
it is not imported by the competition agent.
"""
from __future__ import annotations

import hashlib


def policy_rng_seed(game: str, evaluation_seed: int) -> int:
    """Derive a reproducible controller seed independently for each game/trial."""
    if not isinstance(game, str) or not game:
        raise ValueError("game must be a nonempty string")
    if not isinstance(evaluation_seed, int) or isinstance(evaluation_seed, bool) or evaluation_seed < 0:
        raise ValueError("evaluation seed must be a nonnegative integer")
    payload = f"public-policy-evaluation-v1:{game}:{evaluation_seed}"
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")
