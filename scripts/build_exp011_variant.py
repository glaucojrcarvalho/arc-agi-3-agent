#!/usr/bin/env python3
"""Build isolated EXP-011 ablation without modifying competition agent sources.

The rejected click-balancing controller lives only under experiments/.
This builder reproduces its standalone artifact by replacing the explorer
within a temporary support package and enabling a separate agent flag.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path

from build_standalone_agent import build_standalone_source

ROOT = Path(__file__).resolve().parents[1]


def build_variant() -> str:
    source = (ROOT / "agent" / "exp005_agent.py").read_text(encoding="utf-8")
    replacements = {
        "    KEYBOARD_MODEL_REFRESH_EVERY = 12\n":
            "    KEYBOARD_MODEL_REFRESH_EVERY = 12\n"
            "    BALANCED_CLICK_EXPLORATION = True  # EXP-011: evaluate before promotion.\n",
        "self._explorer = NoveltyExplorer(self.game_id)":
            "self._explorer = NoveltyExplorer(\n"
            "            self.game_id, balanced_clicks=self.BALANCED_CLICK_EXPLORATION\n"
            "        )",
        '            "heuristic_calls": self._explorer.heuristic_calls,\n':
            '            "heuristic_calls": self._explorer.heuristic_calls,\n'
            '            "balanced_click_exploration": self._explorer.balanced_clicks,\n',
    }
    for before, after in replacements.items():
        if source.count(before) != 1:
            raise ValueError("EXP-011 source injection point changed")
        source = source.replace(before, after, 1)

    with tempfile.TemporaryDirectory(prefix="exp011-public-") as root:
        package = Path(root) / "arc_agent"
        shutil.copytree(ROOT / "src" / "arc_agent", package)
        shutil.copyfile(
            ROOT / "experiments" / "exp011_balanced_click_explorer.py",
            package / "novelty_explorer.py",
        )
        return build_standalone_source(source, package_root=package)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "dist" / "exp011_candidate.py"
    )
    args = parser.parse_args()
    rendered = build_variant()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print("EXP-011 candidate SHA-256:", hashlib.sha256(rendered.encode()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
