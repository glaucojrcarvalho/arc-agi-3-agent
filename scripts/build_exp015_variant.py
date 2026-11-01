#!/usr/bin/env python3
"""EXP-015 public-only ablation: bounded inertia after settled-state changes.

Changed pixels are merely a transition observation, never scored progress.
No game IDs, hidden data, official submissions or external model calls.
"""
from __future__ import annotations
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from build_standalone_agent import build_standalone_source

ROOT = Path(__file__).resolve().parents[1]


def replace_once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError("EXP-015 source anchor changed; refusing ambiguous patch")
    return source.replace(before, after, 1)


def build_explorer_source(*, probability: float, max_chain: int = 3) -> str:
    if not (0.0 <= probability <= 1.0):
        raise ValueError("probability must be 0..1")
    if isinstance(max_chain, bool) or not isinstance(max_chain, int) or not 2 <= max_chain <= 6:
        raise ValueError("max_chain must be 2..6")
    support = (ROOT / "src/arc_agent/novelty_explorer.py").read_text(encoding="utf-8")
    support = replace_once(
        support, "        self.heuristic_calls = 0\n",
        """        self._previous_frame: str | None = None
        self._previous_keyboard_action: int | None = None
        self._recent_frames: deque[str] = deque(maxlen=6)
        self._consecutive_action: int | None = None
        self._consecutive_length = 0
        self.momentum_actions = 0
        self.heuristic_calls = 0
""")
    support = replace_once(
        support, "        self._visits[(fingerprint, action_id)] += 1\n",
        """        if self._consecutive_action == action_id:
            self._consecutive_length += 1
        else:
            self._consecutive_action = action_id
            self._consecutive_length = 1
        self._previous_frame = fingerprint
        self._previous_keyboard_action = action_id if not data else None
        self._recent_frames.append(fingerprint)
        self._visits[(fingerprint, action_id)] += 1
""")
    support = replace_once(
        support, "        self._visits.clear()\n",
        """        self._visits.clear()
        self._previous_frame = None
        self._previous_keyboard_action = None
        self._recent_frames.clear()
        self._consecutive_action = None
        self._consecutive_length = 0
""")
    support = replace_once(
        support, "        action = min(ranked)[2]\n        data: dict[str, int] = {}\n",
        f"""        action = min(ranked)[2]
        # Test motion persistence, but reject recent loops, same-state
        # transitions, coordinate actions and long repetitive streaks.
        # No pixel change is ever treated as an actual level completion.
        previous = self._previous_keyboard_action
        can_continue = (
            previous is not None
            and previous in actions
            and previous not in complex_action_ids
            and self._previous_frame != fingerprint
            and fingerprint not in self._recent_frames
            and self._consecutive_length < {max_chain}
        )
        if can_continue and self._rng.random() < {probability!r}:
            action = previous
            self.momentum_actions += 1
        data: dict[str, int] = {{}}
""")
    return support


def build_variant(*, probability: float = 0.55, max_chain: int = 3) -> str:
    source = (ROOT / "agent/exp005_agent.py").read_text(encoding="utf-8")
    support = build_explorer_source(probability=probability, max_chain=max_chain)
    with tempfile.TemporaryDirectory(prefix="arc3-exp015-public-") as scratch:
        package = Path(scratch) / "arc_agent"
        shutil.copytree(ROOT / "src/arc_agent", package)
        (package / "novelty_explorer.py").write_text(support, encoding="utf-8")
        return build_standalone_source(source, package_root=package)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probability", type=float, default=0.55)
    parser.add_argument("--max-chain", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/exp015_candidate.py")
    args = parser.parse_args()
    rendered = build_variant(probability=args.probability, max_chain=args.max_chain)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print("EXP015_SHA256=" + hashlib.sha256(rendered.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
