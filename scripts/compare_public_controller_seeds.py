"""Compare paired *public-only*, randomized-controller fake-model ARC runs.

This is an evaluation audit, not a Kaggle or RHAE scoring implementation.
Environment seeds alone may produce identical initial frames; use only
runs explicitly marked controller_seed_varied=true. Compute game-level
differences as well as session-level counts to avoid treating repeated
public-game trials as independent games.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _rows(payload: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    if payload.get("summary", {}).get("controller_seed_varied") is not True:
        raise ValueError("not a randomized-controller evaluation")
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for item in payload.get("games", []):
        if item.get("controller_seed_varied") is not True:
            raise ValueError("missing per-session controller RNG marker")
        game, seed = item.get("game"), item.get("seed")
        if not isinstance(game, str) or isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("invalid game or evaluation seed")
        key = game, seed
        if key in rows:
            raise ValueError(f"duplicate game/seed: {key}")
        if any(
            isinstance(item.get(field), bool)
            or not isinstance(item.get(field), (int, float))
            or item[field] < 0
            for field in ("actions", "max_levels", "model_calls", "wallclock_seconds")
        ):
            raise ValueError(f"malformed metrics for {key}")
        rows[key] = item
    if not rows:
        raise ValueError("empty evaluation")
    if payload.get("summary", {}).get("sessions") != len(rows):
        raise ValueError("summary/session count mismatch")
    return rows


def compare(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Match exact (public game, randomized-controller seed) pairs."""
    before, after = _rows(baseline), _rows(candidate)
    if before.keys() != after.keys():
        raise ValueError("unpaired game/seed inventory; comparisons are invalid")

    improvements = regressions = ties = 0
    per_game: dict[str, dict[str, int]] = defaultdict(
        lambda: {"sessions": 0, "level_delta": 0, "improvements": 0, "regressions": 0}
    )
    for game, seed in sorted(before):
        old, new = before[game, seed], after[game, seed]
        delta = int(new["max_levels"]) - int(old["max_levels"])
        metrics = per_game[game]
        metrics["sessions"] += 1
        metrics["level_delta"] += delta
        if delta > 0:
            improvements += 1
            metrics["improvements"] += 1
        elif delta < 0:
            regressions += 1
            metrics["regressions"] += 1
        else:
            ties += 1

    def sum_metric(rows: dict, key: str) -> float:
        return sum(item[key] for item in rows.values())

    calls_old = int(sum_metric(before, "model_calls"))
    calls_new = int(sum_metric(after, "model_calls"))
    games_pos = sum(v["level_delta"] > 0 for v in per_game.values())
    games_neg = sum(v["level_delta"] < 0 for v in per_game.values())
    result = {
        "protocol": "public-games/paired-controller-rng/fake-model/no-RHAE",
        "games": len(per_game),
        "sessions": len(before),
        "seeds": sorted({seed for _, seed in before}),
        "baseline_total_max_levels": int(sum_metric(before, "max_levels")),
        "candidate_total_max_levels": int(sum_metric(after, "max_levels")),
        "baseline_sessions_with_levels": sum(x["max_levels"] > 0 for x in before.values()),
        "candidate_sessions_with_levels": sum(x["max_levels"] > 0 for x in after.values()),
        "session_improvements": improvements,
        "session_regressions": regressions,
        "session_ties": ties,
        "games_with_net_improvement": games_pos,
        "games_with_net_regression": games_neg,
        "games_with_no_net_change": len(per_game) - games_pos - games_neg,
        "baseline_actions": int(sum_metric(before, "actions")),
        "candidate_actions": int(sum_metric(after, "actions")),
        "baseline_fake_model_calls": calls_old,
        "candidate_fake_model_calls": calls_new,
        "fake_model_call_reduction_percent": (
            round(100 * (calls_old - calls_new) / calls_old, 2) if calls_old else None
        ),
        "baseline_sum_cpu_wallclock_seconds": round(sum_metric(before, "wallclock_seconds"), 3),
        "candidate_sum_cpu_wallclock_seconds": round(sum_metric(after, "wallclock_seconds"), 3),
        "by_public_game": dict(sorted(per_game.items())),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(
        json.loads(args.baseline.read_text(encoding="utf-8")),
        json.loads(args.candidate.read_text(encoding="utf-8")),
    )
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
