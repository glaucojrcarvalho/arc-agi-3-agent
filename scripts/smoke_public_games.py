"""Compare EXP-001 and EXP-002 contracts in real public ARC games.

This uses a deterministic *dummy* policy instead of Qwen: it verifies integration
and transition behavior, not real model quality or Kaggle leaderboard score.
Supply the official public environment_files folder; never supply private games.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import types
from pathlib import Path

from arc_agi import Arcade, OperationMode
from arcengine import FrameData, GameState


def _convert(raw):
    return FrameData(
        game_id=raw.game_id,
        frame=[array.tolist() for array in raw.frame],
        state=raw.state,
        levels_completed=raw.levels_completed,
        win_levels=raw.win_levels,
        guid=raw.guid,
        full_reset=raw.full_reset,
        available_actions=raw.available_actions,
    )


class StubModel:
    model = "deterministic-protocol-probe-NOT-QWEN"
    def complete(self, prompt: str) -> str:
        request = json.loads(prompt)
        allowed = request["available_action_ids"]
        action = min(allowed)
        if action in request["complex_action_ids"]:
            data = {
                "x": request["coordinate_bounds"]["x_max_exclusive"] // 2,
                "y": request["coordinate_bounds"]["y_max_exclusive"] // 2,
            }
        else:
            data = {}
        return json.dumps({"action": action, "data": data, "reason": "protocol probe"})


def run(agent_class, *, arc, game: str, max_actions: int):
    env = arc.make(game, seed=0, save_recording=False)
    if env is None:
        raise RuntimeError(f"public environment {game} could not load")
    current = _convert(env.reset())
    agent = agent_class(game_id=game)
    agent._model = StubModel()
    executed: list[int] = []
    completed = 0
    for _ in range(max_actions):
        if agent.is_done([], current):
            break
        action = agent.choose_action([], current)
        executed.append(action.value)
        raw = env.step(action, data=action.action_data.model_dump())
        if raw is None:
            break
        current = _convert(raw)
        completed = max(completed, current.levels_completed)
    return {
        "game": game,
        "agent": agent.__class__.__module__,
        "steps": len(executed),
        "distinct_actions": len(set(executed)),
        "levels_completed": completed,
        "state": current.state.name,
        "redirects": getattr(getattr(agent, "_feedback", None), "redirects", 0),
        "proven_noops": getattr(getattr(agent, "_feedback", None), "proven_noops", 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environments-dir", type=Path, required=True)
    parser.add_argument("--games", nargs="+", default=["ls20", "vc33"])
    parser.add_argument("--max-actions", type=int, default=40)
    args = parser.parse_args()
    if not 1 <= args.max_actions <= 200:
        parser.error("max-actions must be 1..200")
    if not args.environments_dir.is_dir():
        parser.error("environment directory missing")

    # The framework base needs a remote scorecard/Swarm. This probe tests
    # only choose_action using a minimal base, keeping SDK observations real.
    agents = types.ModuleType("agents")
    agent_mod = types.ModuleType("agents.agent")
    class Base:
        def __init__(self, *args, **kwargs):
            pass
    agent_mod.Agent = Base
    agents.agent = agent_mod
    sys.modules["agents"] = agents
    sys.modules["agents.agent"] = agent_mod
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    direct = importlib.import_module("agent.my_agent").MyAgent
    adaptive = importlib.import_module("agent.exp002_agent").MyAgent

    arc = Arcade(
        operation_mode=OperationMode.OFFLINE,
        environments_dir=str(args.environments_dir),
        recordings_dir="/tmp/arc3-exp002-public-smoke",
    )
    for game in args.games:
        for agent_class in (direct, adaptive):
            try:
                print(json.dumps(run(agent_class, arc=arc, game=game, max_actions=args.max_actions)))
            except Exception as exc:
                print(json.dumps({"game": game, "agent": agent_class.__module__, "error": f"{type(exc).__name__}: {exc}"}))
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
