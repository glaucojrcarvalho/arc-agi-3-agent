"""Deterministic controller RNG seed for *evaluation-only* public-game tests.

Keep this stdlib-only module importable by repository CI without arc_agi;
it is not imported by the competition agent.
"""
from __future__ import annotations

import hashlib
import re


def policy_rng_seed(game: str, evaluation_seed: int) -> int:
    """Derive a reproducible controller seed independently for each game/trial."""
    if not isinstance(game, str) or not game:
        raise ValueError("game must be a nonempty string")
    if not isinstance(evaluation_seed, int) or isinstance(evaluation_seed, bool) or evaluation_seed < 0:
        raise ValueError("evaluation seed must be a nonnegative integer")
    # Arcade accepts either a short public game slug or a full slug-hash ID.
    # Treat both spellings as the same controller seed, otherwise the same
    # public game/seed pair silently produces different trajectories.
    match = re.fullmatch(r"([a-z0-9]{4})-[a-f0-9]{8}", game)
    canonical_game = match.group(1) if match else game
    payload = f"public-policy-evaluation-v1:{canonical_game}:{evaluation_seed}"
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")
