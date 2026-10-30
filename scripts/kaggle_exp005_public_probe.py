"""Bounded real-Qwen smoke on two PUBLIC ARC games, used only in save-and-run."""
from __future__ import annotations

import json
import sys
import time
import types
from pathlib import Path

from arc_agi import Arcade, OperationMode
from arcengine import FrameData, GameAction


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


def load_probe_agent(standalone_source: str):
    """Load the standalone agent with the game-ID contract of the real base.

    Kaggle's public-game smoke runs outside the competition's agents
    package. Its stand-in base must still initialize game_id: EXP-005's
    novelty explorer requires this before its first action.
    """
    agents = types.ModuleType("agents")
    agent_module = types.ModuleType("agents.agent")

    class Base:
        def __init__(self, *args, **kwargs):
            game_id = kwargs.get("game_id", args[0] if args else None)
            if not isinstance(game_id, str) or not game_id:
                raise ValueError("public probe requires a nonempty game_id")
            self.game_id = game_id

    agent_module.Agent = Base
    agents.agent = agent_module
    sys.modules["agents"] = agents
    sys.modules["agents.agent"] = agent_module
    namespace: dict = {"__name__": "__exp005_probe__"}
    exec(compile(standalone_source, "exp005_standalone.py", "exec"), namespace, namespace)
    return namespace["MyAgent"]


def _action_reasoning(action) -> dict:
    """Normalize optional reasoning for the public-game transport.

    MyAgent returns GameAction.RESET directly for GAME_OVER/NOT_PLAYED;
    that enum value has no reasoning attribute. Enum instances are
    singletons, so never reuse reasoning accidentally attached to RESET.
    """
    if action is GameAction.RESET:
        return {}
    reasoning = getattr(action, "reasoning", None)
    if reasoning is None:
        return {}
    if not isinstance(reasoning, dict):
        raise TypeError("public probe expected dict action reasoning")
    return dict(reasoning)


def _save_public_probe(results: list[dict], *, complete: bool,
                       path: str = "/kaggle/working/exp005-public-probe.json") -> None:
    """Write a recoverable result after each public game, not just the last.

    If a later public game fails, earlier complete traces remain available
    without scraping noisy notebook logs.
    """
    Path(path).write_text(
        json.dumps({
            "model": "Qwen3.8-27B FP8",
            "probe_complete": complete,
            "completed_games": len(results),
            "results": results,
        }, indent=2),
        encoding="utf-8",
    )


def run_public_probe(standalone_source: str, environments_root: str):
    """Record observable game behavior; no claims about hidden-game score."""
    root = Path(environments_root)
    if not root.is_dir():
        raise RuntimeError(f"public environment input not mounted: {root}")
    agent_cls = load_probe_agent(standalone_source)
    from arc_agent.state import diff_frames
    arcade = Arcade(
        operation_mode=OperationMode.OFFLINE,
        environments_dir=str(root),
        recordings_dir="/kaggle/working/exp005-public-recordings",
    )
    results = []
    games = ("ls20", "vc33", "r11l", "tn36")
    for game in games:
        env = arcade.make(game, seed=0, save_recording=False)
        if env is None:
            raise RuntimeError(f"public game unavailable: {game}")
        raw = env.reset()
        if raw is None:
            raise RuntimeError(f"public game reset failed: {game}")
        current = _frame(raw)
        agent = agent_cls(game_id=game)
        actions = []
        trace = []
        resets = 0
        highest_level = int(current.levels_completed or 0)
        game_started = time.monotonic()
        for _ in range(80):
            if agent.is_done([], current):
                break
            action = agent.choose_action([], current)
            actions.append(action.value)
            # Terminal-state RESET is intentionally emitted without
            # per-turn metadata, unlike model/heuristic actions.
            reasoning = _action_reasoning(action)
            action_data = action.action_data.model_dump()
            if action is GameAction.RESET:
                resets += 1
            next_raw = env.step(action, data=action_data, reasoning=reasoning)
            if next_raw is None:
                raise RuntimeError(f"game returned null frame: {game}")
            after = _frame(next_raw)
            delta = diff_frames(current.frame, after.frame)
            highest_level = max(highest_level, int(after.levels_completed or 0))
            trace.append({
                "action_id": action.value,
                "is_reset": action is GameAction.RESET,
                "x": action_data.get("x"),
                "y": action_data.get("y"),
                "changed_cells": delta.changed_cells,
                "levels_completed": after.levels_completed,
                "redirected": bool(reasoning.get("redirected")),
                "spatial_candidates": int(reasoning.get("spatial_candidates", 0)),
                "planned_action": bool(reasoning.get("planned_action", False)),
                "heuristic_step": bool(reasoning.get("heuristic_step", False)),
                "steps_without_progress": int(reasoning.get("steps_without_progress", 0)),
                "belief_revisions": int(reasoning.get("belief_revisions", 0)),
                "recent_click_cooldown_count": int(reasoning.get("recent_click_cooldown_count", 0)),
                "model_reason": str(reasoning.get("reason", ""))[:90],
            })
            current = after
            if time.monotonic() - game_started > 720:
                print(f"EXP-005 public probe reached wallclock guard: {game}", flush=True)
                break
        row = {
            "game": game,
            "actions": len(actions),
            "distinct_actions": len(set(actions)),
            "levels_completed": current.levels_completed,
            "max_levels_completed": highest_level,
            "resets": resets,
            "state": current.state.name,
            "noops": agent._feedback.proven_noops,
            "redirects": agent._feedback.redirects,
            "model_calls": agent.model_calls,
            "planned_actions": agent._belief.plan_actions_taken,
            "heuristic_actions": agent._explorer.heuristic_calls,
            "belief_revisions": agent._belief.belief_revisions,
            "stagnation_events": agent._belief.stagnation_events,
            "elapsed_seconds": round(time.monotonic() - game_started, 2),
            "action_trace": trace,
        }
        print(
            "EXP-005 public probe result: "
            + json.dumps({k: v for k, v in row.items() if k != "action_trace"}, sort_keys=True),
            flush=True,
        )
        results.append(row)
        _save_public_probe(results, complete=len(results) == len(games))
    return results
