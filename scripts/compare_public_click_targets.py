"""Measure one-action effects of generic click targets on PUBLIC ARC games.

This is a diagnostic probe, not a performance or leaderboard evaluation.
Every probe begins at a fresh reset with fixed seed. No environment is solved.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from arc_agi import Arcade, OperationMode
from arcengine import GameAction
from arc_agent.perception import salient_click_targets
from arc_agent.state import diff_frames


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environments-dir", type=Path, required=True)
    parser.add_argument("--games", nargs="+", default=["vc33", "tn36"])
    parser.add_argument("--max-clicks", type=int, default=7)
    args = parser.parse_args()
    if not 1 <= args.max_clicks <= 7:
        parser.error("max-clicks must be 1..7 for balanced comparison")
    arc = Arcade(
        operation_mode=OperationMode.OFFLINE,
        environments_dir=str(args.environments_dir),
        recordings_dir="/tmp/arc3-spatial-click-probe",
    )
    for game in args.games:
        env = arc.make(game, seed=0, save_recording=False)
        if env is None:
            raise RuntimeError(f"public game {game} not available")
        initial = env.reset()
        if 6 not in initial.available_actions:
            print(json.dumps({"game": game, "skipped": "no click action"}))
            continue
        frame = [layer.tolist() for layer in initial.frame]
        width = len(frame[0][0])
        height = len(frame[0])
        targets = salient_click_targets(frame, max_targets=10)
        baseline = [
            {"x": width//2, "y": height//2},
            {"x": width//4, "y": height//4},
            {"x": width*3//4, "y": height//4},
            {"x": width//4, "y": height*3//4},
            {"x": width*3//4, "y": height*3//4},
            {"x": 0, "y": 0},
            {"x": width-1, "y": height-1},
        ]
        for label, positions in (("fixed_grid", baseline), ("salient_regions", targets)):
            rows = []
            for t in positions[:args.max_clicks]:
                env.reset()
                action = GameAction.ACTION6
                data = {"x": t["x"], "y": t["y"]}
                action.set_data(data)
                result = env.step(action, data=action.action_data.model_dump())
                if result is None:
                    continue
                after = [layer.tolist() for layer in result.frame]
                change = diff_frames(frame, after)
                rows.append({
                    "x": t["x"],
                    "y": t["y"],
                    "changed_cells": change.changed_cells,
                    "level_delta": result.levels_completed - initial.levels_completed,
                })
            print(json.dumps({
                "game": game,
                "policy": label,
                "probes": len(rows),
                "effectful": sum(r["changed_cells"] > 0 for r in rows),
                "progress": sum(r["level_delta"] > 0 for r in rows),
                "mean_changed_cells": round(sum(r["changed_cells"] for r in rows)/max(1,len(rows)),2),
                "rows": rows,
            }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
