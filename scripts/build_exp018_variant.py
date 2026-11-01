#!/usr/bin/env python3
"""Build isolated public-only EXP-018 stagnation-threshold ablations.

The competition source, Qwen configuration, and Kaggle notebook are unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path

from build_standalone_agent import build_standalone_source

ROOT = Path(__file__).resolve().parents[1]
COMPLEX_ANCHOR = "    COMPLEX_NOVELTY_AFTER = 8\n"
KEYBOARD_ANCHOR = "    KEYBOARD_NOVELTY_AFTER = 16\n"


def build_variant(*, complex_after: int, keyboard_after: int) -> str:
    """Change only the onset of model-free exploration, not its action policy."""
    for name, value in (("complex_after", complex_after), ("keyboard_after", keyboard_after)):
        if isinstance(value, bool) or not isinstance(value, int) or not 2 <= value <= 48:
            raise ValueError(f"{name} must be an integer 2..48")
    source = (ROOT / "agent/exp005_agent.py").read_text(encoding="utf-8")
    for original, new in (
        (COMPLEX_ANCHOR, f"    COMPLEX_NOVELTY_AFTER = {complex_after}\n"),
        (KEYBOARD_ANCHOR, f"    KEYBOARD_NOVELTY_AFTER = {keyboard_after}\n"),
    ):
        if source.count(original) != 1:
            raise ValueError("EXP-018 class constant anchor missing/ambiguous")
        source = source.replace(original, new, 1)
    with tempfile.TemporaryDirectory(prefix="arc3-exp018-public-") as tmp:
        package = Path(tmp) / "arc_agent"
        shutil.copytree(ROOT / "src/arc_agent", package)
        return build_standalone_source(source, package_root=package)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complex-after", type=int, required=True)
    parser.add_argument("--keyboard-after", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = build_variant(complex_after=args.complex_after, keyboard_after=args.keyboard_after)
    compile(artifact, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(artifact, encoding="utf-8")
    print("EXP018_SHA256=" + hashlib.sha256(artifact.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
