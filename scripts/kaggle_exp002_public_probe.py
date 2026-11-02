"""Bounded real-Qwen smoke on two PUBLIC ARC games, used only in save-and-run."""
from __future__ import annotations

import json
import sys
import time
import types
from pathlib import Path

from arc_agi import Arcade, OperationMode
from arcengine import FrameData


def _frame(raw):
    return FrameData(
        game_id=raw.game_id,
        frame=[a.tolist() for a in raw.frame],
        state=raw.state,
        levels_completed=raw.levels_completed,
        win_levels=raw.win_levels,
        guid=raw.guid,
        full_reset=raw.full_reset,
        available_actions=raw.available_actions,
    )


def run_public_probe(standalone_source: str, environments_root: str):
    """Record observable game behavior; no claims about hidden-game score."""
    root = Path(environments_root)
    if not root.is_dir():
        raise RuntimeError(f"public environment input not mounted: {root}")
    agents = types.ModuleType("agents")
    agent_module = types.ModuleType("agents.agent")

    class Base:
        def __init__(self, *args, **kwargs):
            pass

    agent_module.Agent = Base
    agents.agent = agent_module
    sys.modules["agents"] = agents
    sys.modules["agents.agent"] = agent_module
    namespace: dict = {"__name__": "__exp002_probe__"}
    exec(compile(standalone_source, "exp002_standalone.py", "exec"), namespace, namespace)
    agent_cls = namespace["MyAgent"]
    arcade = Arcade(
        operation_mode=OperationMode.OFFLINE,
        environments_dir=str(root),
        recordings_dir="/kaggle/working/exp002-public-recordings",
    )
    results = []
    for game in ("ls20", "vc33"):
        env = arcade.make(game, seed=0, save_recording=False)
        if env is None:
            raise RuntimeError(f"public game unavailable: {game}")
        raw = env.reset()
        if raw is None:
            raise RuntimeError(f"public game reset failed: {game}")
        current = _frame(raw)
        agent = agent_cls(game_id=game)
        actions = []
        game_started = time.monotonic()
        for _ in range(15):
            if agent.is_done([], current):
                break
            action = agent.choose_action([], current)
            actions.append(action.value)
            next_raw = env.step(
                action,
                data=action.action_data.model_dump(),
                reasoning=action.reasoning,
            )
            if next_raw is None:
                raise RuntimeError(f"game returned null frame: {game}")
            current = _frame(next_raw)
            if time.monotonic() - game_started > 360:
                print(f"EXP-002 public probe reached wallclock guard: {game}", flush=True)
                break
        row = {
            "game": game,
            "actions": len(actions),
            "distinct_actions": len(set(actions)),
            "levels_completed": current.levels_completed,
            "state": current.state.name,
            "noops": agent._feedback.proven_noops,
            "redirects": agent._feedback.redirects,
            "model_calls": agent.model_calls,
        }
        print("EXP-002 public probe result: " + json.dumps(row, sort_keys=True), flush=True)
        results.append(row)
    Path("/kaggle/working/exp002-public-probe.json").write_text(
        json.dumps({"model": "Qwen3.8-27B FP8", "results": results}, indent=2),
        encoding="utf-8",
    )
    return results
