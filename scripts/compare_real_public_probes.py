"""Compare paired public-game real-model probes without exposing action traces.

This tool does not compute RHAE, infer progress from pixels, read private
evaluation assets, or send competition submissions. Only aggregated results
are emitted; input trace data is used solely for authoritative level milestones.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _number(value: Any, field: str, *, integer: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid {field}")
    if integer and not isinstance(value, int):
        raise ValueError(f"invalid {field}")
    if value < 0 or value != value or value == float("inf"):
        raise ValueError(f"invalid {field}")
    return float(value)


def _read(path: Path) -> tuple[dict[str, dict[str, Any]], tuple[Any, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("probe_complete") is not True:
        raise ValueError("only fully completed public probes may be compared")
    protocol = data.get("probe_protocol") or {}
    pair_key = (
        protocol.get("controller_seed"),
        protocol.get("environment_seed", 0),
    )
    if pair_key[0] is not None:
        _number(pair_key[0], "controller seed", integer=True)
    _number(pair_key[1], "environment seed", integer=True)
    rows = {}
    for row in data.get("results", []):
        game = row.get("game")
        if not isinstance(game, str) or not game or game in rows:
            raise ValueError("invalid or duplicate public game")
        # A probe-level seed is not enough to prove pairing: reject a result
        # assembled from mixed controller trials. Legacy unseeded probes did
        # not record per-row seed metadata, so remain backward compatible.
        if pair_key[0] is not None and "controller_seed" not in row:
            raise ValueError("seeded public result missing game controller seed")
        if "controller_seed" in row and row["controller_seed"] != pair_key[0]:
            raise ValueError("game controller seed disagrees with probe protocol")
        if pair_key[0] is not None and "environment_seed" not in row:
            raise ValueError("seeded public result missing game environment seed")
        if "environment_seed" in row and row["environment_seed"] != pair_key[1]:
            raise ValueError("game environment seed disagrees with probe protocol")
        actions = int(_number(row.get("actions"), "actions", integer=True))
        max_level = int(_number(row.get("max_levels_completed"), "max levels", integer=True))
        _number(row.get("model_calls"), "model calls", integer=True)
        _number(row.get("elapsed_seconds"), "elapsed seconds")
        trace = row.get("action_trace")
        if not isinstance(trace, list) or len(trace) != actions:
            raise ValueError("missing or mismatched authoritative action trace")
        progress = []
        observed_max = 0
        for action_index, event in enumerate(trace, 1):
            if not isinstance(event, dict):
                raise ValueError("invalid trace event")
            level = int(_number(event.get("levels_completed"), "level counter", integer=True))
            if level > observed_max:
                progress.extend(
                    {"level": n, "after_action": action_index}
                    for n in range(observed_max + 1, level + 1)
                )
            observed_max = max(observed_max, level)
        if observed_max != max_level:
            raise ValueError("reported levels disagree with authoritative trace")
        reported = row.get("level_completion_actions")
        if reported is not None and reported != progress:
            raise ValueError("published milestones disagree with authoritative trace")
        rows[game] = {
            "game": game, "actions": actions, "max_levels": max_level,
            "model_calls": row["model_calls"],
            "wallclock_seconds": row["elapsed_seconds"],
            "completion_actions": progress,
        }
    if not rows or len(rows) != data.get("completed_games"):
        raise ValueError("missing public-game results")
    return rows, pair_key


def _percent(old: float, new: float) -> float | None:
    return round((old - new) * 100 / old, 2) if old else None


def compare(baseline: Path, candidate: Path) -> dict[str, Any]:
    before, before_seed = _read(baseline)
    after, after_seed = _read(candidate)
    if before_seed != after_seed:
        raise ValueError(
            "controller/environment seeds differ; an unpaired Qwen comparison is invalid"
        )
    if before.keys() != after.keys():
        raise ValueError("public-game inventories differ")
    games = []
    for name in sorted(before):
        old, new = before[name], after[name]
        old_levels, new_levels = old["max_levels"], new["max_levels"]
        first_old = old["completion_actions"][0]["after_action"] if old_levels else None
        first_new = new["completion_actions"][0]["after_action"] if new_levels else None
        first_delta = (
            first_new - first_old
            if old_levels == new_levels and old_levels > 0
            else None
        )
        games.append({
            "game": name,
            "baseline_levels": old_levels,
            "candidate_levels": new_levels,
            "level_delta": new_levels - old_levels,
            "baseline_first_completion_action": first_old,
            "candidate_first_completion_action": first_new,
            "paired_first_completion_action_delta": first_delta,
            "baseline_model_calls": old["model_calls"],
            "candidate_model_calls": new["model_calls"],
            "baseline_wallclock_seconds": old["wallclock_seconds"],
            "candidate_wallclock_seconds": new["wallclock_seconds"],
        })
    sum_old_calls = sum(row["model_calls"] for row in before.values())
    sum_new_calls = sum(row["model_calls"] for row in after.values())
    sum_old_wall = sum(row["wallclock_seconds"] for row in before.values())
    sum_new_wall = sum(row["wallclock_seconds"] for row in after.values())
    return {
        "protocol": "paired-4-public-games/real-model/no-RHAE/no-private-data",
        "controller_seed": before_seed[0],
        "environment_seed": before_seed[1],
        "games": len(games),
        "baseline_levels": sum(row["max_levels"] for row in before.values()),
        "candidate_levels": sum(row["max_levels"] for row in after.values()),
        "baseline_actions": sum(row["actions"] for row in before.values()),
        "candidate_actions": sum(row["actions"] for row in after.values()),
        "baseline_model_calls": sum_old_calls,
        "candidate_model_calls": sum_new_calls,
        "model_call_reduction_percent": _percent(sum_old_calls, sum_new_calls),
        "baseline_wallclock_seconds": round(sum_old_wall, 2),
        "candidate_wallclock_seconds": round(sum_new_wall, 2),
        "wallclock_reduction_percent": _percent(sum_old_wall, sum_new_wall),
        "public_games": games,
        "interpretation": (
            "Levels and completion actions are verified using levels_completed, "
            "not pixel changes. A single public run does not establish RHAE "
            "or competition-score improvement; CPU/GPU wallclock varies."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    aggregate = compare(args.baseline, args.candidate)
    output = json.dumps(aggregate, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
