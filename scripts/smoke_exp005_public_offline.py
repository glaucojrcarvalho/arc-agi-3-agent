"""Offline public-game transport smoke using a deterministic FAKE model.

This verifies the Kaggle EXP-005 agent/probe interface, not model quality.
No GPU, hidden evaluation, competition submission, or Qwen inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from arc_agi import Arcade, OperationMode
from arcengine import GameAction

from kaggle_exp005_public_probe import _action_reasoning, _frame, load_probe_agent


class FakeModel:
    model = "fake-deterministic-public-smoke"

    def complete(self, prompt: str) -> str:
        return '{"action":1,"data":{},"reason":"transport smoke only"}'


def _policy_rng_seed(game: str, evaluation_seed: int) -> int:
    """Independent deterministic controller randomness for public A/B tests.

    This seed never changes the competition agent or inserts a puzzle rule.
    ARC offline environment seeds can leave the same starting board unchanged.
    """
    if not isinstance(evaluation_seed, int) or isinstance(evaluation_seed, bool) or evaluation_seed < 0:
        raise ValueError("evaluation seed must be a nonnegative integer")
    payload = f"public-policy-evaluation-v1:{game}:{evaluation_seed}"
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def screen(*, agent_source: str, environments_dir: Path, games: list[str],
           seeds: list[int], max_actions: int = 80,
           vary_policy_seed: bool = False) -> dict:
    """Exercise legal actions, no-op feedback, and RESET without real inference."""
    if max_actions <= 0:
        raise ValueError("max_actions must be positive")
    if not environments_dir.is_dir():
        raise FileNotFoundError(environments_dir)
    assert _action_reasoning(GameAction.RESET) == {}
    agent_cls = load_probe_agent(agent_source)
    arcade = Arcade(
        operation_mode=OperationMode.OFFLINE,
        environments_dir=str(environments_dir),
        recordings_dir="/tmp/arc-exp005-public-smoke-recordings",
    )
    results: list[dict] = []
    for game in games:
        for seed in seeds:
            env = arcade.make(game, seed=seed, save_recording=False)
            if env is None:
                raise RuntimeError(f"public game unavailable: {game}")
            raw = env.reset()
            if raw is None:
                raise RuntimeError(f"public game reset failed: {game}")
            frame = _frame(raw)
            agent = agent_cls(game_id=game)
            agent._model = FakeModel()
            if vary_policy_seed:
                # Evaluation harness only: reseed the model-free exploration
                # RNG with the requested controller seed. The production
                # agent, game rules, and previous benchmarks are unchanged.
                agent._explorer._rng.seed(_policy_rng_seed(game, seed))
            resets = 0
            levels_max = int(frame.levels_completed or 0)
            actions = 0
            start = time.monotonic()
            for _ in range(max_actions):
                if agent.is_done([], frame):
                    break
                action = agent.choose_action([], frame)
                reasoning = _action_reasoning(action)
                if action is GameAction.RESET:
                    resets += 1
                    if reasoning:
                        raise AssertionError("reset must not reuse old metadata")
                raw = env.step(
                    action,
                    data=action.action_data.model_dump(),
                    reasoning=reasoning,
                )
                if raw is None:
                    raise RuntimeError(
                        f"public game returned null frame: {game}/{seed}"
                    )
                frame = _frame(raw)
                levels_max = max(levels_max, int(frame.levels_completed or 0))
                actions += 1
            item = {
                "game": game, "seed": seed, "actions": actions,
                "controller_seed_varied": vary_policy_seed,
                "resets": resets, "max_levels": levels_max,
                "final_levels": int(frame.levels_completed or 0),
                "model_calls": agent.model_calls,
                "heuristic_actions": agent._explorer.heuristic_calls,
                "wallclock_seconds": round(time.monotonic() - start, 3),
            }
            print(json.dumps(item, sort_keys=True), flush=True)
            results.append(item)
    summary = {
        "controller_seed_varied": vary_policy_seed,
        "sessions": len(results),
        "actions": sum(item["actions"] for item in results),
        "resets": sum(item["resets"] for item in results),
        "sessions_with_levels": sum(item["max_levels"] > 0 for item in results),
        "total_max_levels": sum(item["max_levels"] for item in results),
        "model_calls": sum(item["model_calls"] for item in results),
        "heuristic_actions": sum(item["heuristic_actions"] for item in results),
        "sum_wallclock_seconds": round(
            sum(item["wallclock_seconds"] for item in results), 3
        ),
    }
    print("SUMMARY " + json.dumps(summary, sort_keys=True), flush=True)
    return {"summary": summary, "games": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environments-dir", type=Path, required=True)
    parser.add_argument("--agent", type=Path, default=Path("dist/exp005_agent.py"))
    parser.add_argument("--games", nargs="+", default=["ls20", "vc33", "r11l", "tn36"])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--max-actions", type=int, default=80)
    parser.add_argument(
        "--vary-policy-seed", action="store_true",
        help="independently reseed the fake agent's novelty RNG per evaluation seed",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = screen(
        agent_source=args.agent.read_text(encoding="utf-8"),
        environments_dir=args.environments_dir, games=args.games,
        seeds=args.seeds, max_actions=args.max_actions,
        vary_policy_seed=args.vary_policy_seed,
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
