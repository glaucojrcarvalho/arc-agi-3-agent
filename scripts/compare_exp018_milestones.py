#!/usr/bin/env python3
"""Paired comparison of verified public-game level milestones and action cost.

Each row is a (public game, controller RNG seed) session, not an independent task.
Model transport is deterministic fake; no leaderboard/RHAE inference is possible.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from compare_public_controller_seeds import compare as compare_levels


def session_map(result: dict) -> dict[tuple[str, int], dict]:
    rows = {}
    for item in result["games"]:
        key = (item["game"], item["seed"])
        if key in rows:
            raise ValueError("duplicate public-game/controller-seed row")
        levels = item["max_levels"]
        actions = item["actions"]
        milestones = item["level_completion_actions"]
        if (
            not isinstance(levels, int) or levels < 0
            or not isinstance(actions, int) or actions < 0
            or not isinstance(milestones, list) or len(milestones) != levels
            or any(not isinstance(a, int) or isinstance(a, bool) or a < 1 or a > actions
                   for a in milestones)
            or milestones != sorted(milestones)
        ):
            raise ValueError("invalid level milestone evidence")
        rows[key] = item
    return rows


def compare(baseline: dict, candidate: dict) -> dict:
    base = session_map(baseline)
    trial = session_map(candidate)
    if base.keys() != trial.keys():
        raise ValueError("unpaired controller-seed inventories")
    aggregate = compare_levels(baseline, candidate)
    earlier = later = same = 0
    baseline_indices = candidate_indices = 0
    for key in sorted(base):
        before, after = base[key], trial[key]
        # A policy completing fewer/more levels does not have comparable
        # milestone efficiency; that distinction is counted separately.
        if before["max_levels"] < 1 or before["max_levels"] != after["max_levels"]:
            continue
        for old, new in zip(before["level_completion_actions"],
                            after["level_completion_actions"]):
            earlier += new < old
            later += new > old
            same += new == old
            baseline_indices += old
            candidate_indices += new
    return {
        "protocol": "public-games/paired-controller-seed/fake-model/authoritative-level-index",
        "baseline_completed_levels": aggregate["baseline_total_max_levels"],
        "candidate_completed_levels": aggregate["candidate_total_max_levels"],
        "paired_session_improvements": aggregate["session_improvements"],
        "paired_session_regressions": aggregate["session_regressions"],
        "paired_session_ties": aggregate["session_ties"],
        "matched_level_milestones": earlier + later + same,
        "milestones_earlier": earlier,
        "milestones_later": later,
        "milestones_equal": same,
        "matched_baseline_action_index_sum": baseline_indices,
        "matched_candidate_action_index_sum": candidate_indices,
        "baseline_fake_model_calls": aggregate["baseline_fake_model_calls"],
        "candidate_fake_model_calls": aggregate["candidate_fake_model_calls"],
        "baseline_sum_cpu_wallclock_seconds": aggregate["baseline_sum_cpu_wallclock_seconds"],
        "candidate_sum_cpu_wallclock_seconds": aggregate["candidate_sum_cpu_wallclock_seconds"],
        "distinct_games": aggregate["games"],
        "controller_seeds": aggregate["seeds"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(json.loads(args.baseline.read_text()),
                     json.loads(args.candidate.read_text()))
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
