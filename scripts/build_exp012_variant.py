#!/usr/bin/env python3
"""Generate an isolated, model-free complex-affordance ablation (not deployed)."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path

from build_standalone_agent import build_standalone_source

ROOT = Path(__file__).resolve().parents[1]


def build_explorer_source(*, complex_action_probability: float = 0.65) -> str:
    if not (0.0 <= complex_action_probability <= 1.0):
        raise ValueError("complex_action_probability out of range")
    support = (ROOT / "src/arc_agent/novelty_explorer.py").read_text(encoding="utf-8")
    before = "        action = min(ranked)[2]\n        data: dict[str, int] = {}\n"
    after = (
        "        action = min(ranked)[2]\n"
        "        # EXP-012 local A/B only: treat multiple salient click targets as\n"
        "        # evidence for exploring mouse-like controls, never level progress.\n"
        "        supported_complex = [a for a in actions if a in complex_action_ids]\n"
        f"        if supported_complex and len(candidates) >= 4 and self._rng.random() < {complex_action_probability!r}:\n"
        "            action = supported_complex[self._rng.randrange(len(supported_complex))]\n"
        "        data: dict[str, int] = {}\n"
    )
    if support.count(before) != 1:
        raise ValueError("source injection point changed; do not silently patch")
    return support.replace(before, after, 1)


def build_variant(*, complex_action_probability: float = 0.65) -> str:
    source = (ROOT / "agent/exp005_agent.py").read_text(encoding="utf-8")
    support = build_explorer_source(complex_action_probability=complex_action_probability)
    with tempfile.TemporaryDirectory(prefix="exp012-public-") as scratch:
        package = Path(scratch) / "arc_agent"
        shutil.copytree(ROOT / "src/arc_agent", package)
        (package / "novelty_explorer.py").write_text(support, encoding="utf-8")
        return build_standalone_source(source, package_root=package)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probability", type=float, default=0.65)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/exp012_candidate.py")
    args = parser.parse_args()
    rendered = build_variant(complex_action_probability=args.probability)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print("EXP012_SHA256=" + hashlib.sha256(rendered.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
