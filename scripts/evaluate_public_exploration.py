"""Reproducible public-game protocol screening (not Kaggle scoring).

All games come from the official public environment_files. Experiments use
at most 80 actions and no hardcoded game IDs, layouts, goals or solutions.
Explore random, random+salient clicks, and visitation-aware alternatives.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from collections import Counter, deque
from pathlib import Path

from arc_agi import Arcade, OperationMode
from arcengine import GameAction, GameState
from arc_agent.perception import salient_click_targets
from arc_agent.state import frame_fingerprint


def as_frame(raw):
    return [array.tolist() for array in raw.frame]


class Policy:
    def __init__(self, game_id: str, name: str, seed: int = 0):
        seed_key = game_id if seed == 0 else f"{game_id}:{seed}"
        self.rng = random.Random(int.from_bytes(
            hashlib.sha256(seed_key.encode("utf-8")).digest()[:8], "big"
        ))
        self.name = name
        self.counts = Counter()
        self.previous_points: deque[tuple[int, int]] = deque(maxlen=12)
        self.last_frame = None
        self.last_level = 0
        self.last_action = None
        self.progress_actions = 0
        self.detected_noops = 0
        self.effects = 0

    def choose(self, raw):
        actions = [int(x) for x in raw.available_actions if isinstance(x, int) and x != 0]
        if not actions:
            raise ValueError("no actions exposed")
        if raw.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET, {}
        frame = as_frame(raw)
        level = raw.levels_completed
        fingerprint = frame_fingerprint(frame)
        if self.last_frame is not None:
            before = self.last_frame
            if frame != before:
                self.effects += 1
            else:
                self.detected_noops += 1
            if level > self.last_level:
                self.progress_actions += 1
                self.counts.clear()
                self.previous_points.clear()
        if self.name == "random":
            action_id = self.rng.choice(actions)
        elif self.name in {"salient", "novelty"}:
            if self.name == "salient":
                action_id = self.rng.choice(actions)
            else:
                # Explore action IDs with the fewest attempts in the same exact state.
                scores = [
                    (self.counts[(fingerprint, action)], self.rng.random(), action)
                    for action in actions
                ]
                action_id = min(scores)[2]
        else:
            raise ValueError(self.name)
        data = {}
        action = GameAction.from_id(action_id)
        if action.is_complex():
            height = max(1, min(len(frame[0]), 64))
            width = max(1, min(len(frame[0][0]), 64))
            if self.name == "random":
                data = {"x": self.rng.randrange(width), "y": self.rng.randrange(height)}
            else:
                targets = salient_click_targets(frame, max_targets=24, max_per_color=4)
                points = [(t["x"],t["y"]) for t in targets]
                self.rng.shuffle(points)
                unseen = [p for p in points if p not in self.previous_points]
                if not unseen or self.rng.random() < .20:
                    point = (self.rng.randrange(width), self.rng.randrange(height))
                else:
                    point = unseen[0]
                data = {"x": point[0], "y": point[1]}
                self.previous_points.append(point)
        self.counts[(fingerprint, action_id)] += 1
        self.last_frame = frame
        self.last_level = level
        self.last_action = (action_id, data)
        return action, data


def run_game(arc, game, name, max_actions, *, seed=0):
    env = arc.make(game, seed=seed, save_recording=False)
    if env is None:
        raise RuntimeError(f"could not load {game}")
    raw = env.reset()
    policy = Policy(game, name, seed=seed)
    max_levels = 0
    seen_states = set()
    actions_taken = 0
    started = time.monotonic()
    for _ in range(max_actions):
        if raw is None or raw.state is GameState.WIN:
            break
        action, data = policy.choose(raw)
        action.set_data(data)
        raw = env.step(action, data=action.action_data.model_dump())
        actions_taken += 1
        if raw is None:
            break
        max_levels = max(max_levels, raw.levels_completed)
        seen_states.add(frame_fingerprint(as_frame(raw)))
    return {"game": game[:4], "policy": name, "seed": seed,
            "actions": actions_taken, "levels": max_levels,
            "unique_frames": len(seen_states),
            "state": raw.state.name if raw else "NONE",
            "effectful": policy.effects, "noops": policy.detected_noops,
            "wallclock_seconds": round(time.monotonic() - started, 3)}


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--environments-dir", type=Path, required=True)
    parser.add_argument("--actions", type=int, default=80)
    parser.add_argument("--policies", nargs="+", default=["random","salient","novelty"])
    parser.add_argument("--games", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0])
    parser.add_argument("--output", type=Path)
    args=parser.parse_args()
    if not 1<=args.actions<=80:
        parser.error("actions must be 1..80")
    if len(set(args.seeds)) != len(args.seeds) or any(x < 0 or x >= 2**31 for x in args.seeds):
        parser.error("seeds must be unique nonnegative 31-bit integers")
    arc=Arcade(operation_mode=OperationMode.OFFLINE, environments_dir=str(args.environments_dir),
               recordings_dir="/tmp/arc3-public-exploration")
    games=sorted(info.game_id for info in arc.get_environments()
                 if args.games is None or any(info.game_id.startswith(prefix) for prefix in args.games))
    results=[]
    for name in args.policies:
        for seed in args.seeds:
            for game in games:
                try:
                    r=run_game(arc,game,name,args.actions,seed=seed)
                except Exception as exc:
                    print("EVAL_ERROR",name,seed,game,type(exc).__name__,str(exc),flush=True)
                    raise
                results.append(r)
                if r["levels"]>0:
                    print("LEVEL_PROGRESS",json.dumps(r,sort_keys=True),flush=True)
        selected=[r for r in results if r["policy"]==name]
        print("EVAL_SUMMARY",json.dumps({
          "policy":name,"seeds":args.seeds,"unique_games":len(games),
          "sessions":len(selected),
          "sessions_with_level_progress":sum(r["levels"]>0 for r in selected),
          "games_with_level_progress":len({r["game"] for r in selected if r["levels"]>0}),
          "total_levels":sum(r["levels"] for r in selected),
          "actions_sum":sum(r["actions"] for r in selected),
          "wallclock_seconds":round(sum(r["wallclock_seconds"] for r in selected),3),
          "unique_frames_sum":sum(r["unique_frames"] for r in selected),
          "observed_noops":sum(r["noops"] for r in selected),
        },sort_keys=True),flush=True)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({
          "public_game_count":len(games),"action_cap":args.actions,
          "seeds":args.seeds,"results":results
        },indent=2)+"\n")
        print("EVAL_OUTPUT",args.output,flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
