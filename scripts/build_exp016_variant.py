#!/usr/bin/env python3
"""Generate isolated EXP-016 public-only coarse-novelty ablations."""
from __future__ import annotations
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from build_standalone_agent import build_standalone_source

ROOT = Path(__file__).resolve().parents[1]


def replace_once(body: str, before: str, after: str) -> str:
    if body.count(before) != 1:
        raise ValueError("EXP-016 injection anchor ambiguous or changed")
    return body.replace(before, after, 1)


def build_variant(*, bins: int = 4, quantum: int = 8) -> str:
    if isinstance(bins, bool) or not isinstance(bins, int) or not 1 <= bins <= 8:
        raise ValueError("bins must be integer 1..8")
    if isinstance(quantum, bool) or not isinstance(quantum, int) or not 2 <= quantum <= 32:
        raise ValueError("quantum must be integer 2..32")
    source = (ROOT / "agent/exp005_agent.py").read_text(encoding="utf-8")
    source = replace_once(
        source,
        "from arc_agent.novelty_explorer import NoveltyExplorer\n",
        "from arc_agent.novelty_explorer import NoveltyExplorer\n"
        "from arc_agent.coarse_exploration import coarse_state_key\n",
    )
    source = replace_once(
        source,
        "        settled_frame = frame[-1:] if frame else []\n",
        "        settled_frame = frame[-1:] if frame else []\n"
        f"        exploration_key = coarse_state_key(settled_frame, bins={bins}, quantum={quantum})\n",
    )
    source = replace_once(
        source,
        "            proposed = self._explorer.choose(\n                fingerprint=fingerprint,\n",
        "            proposed = self._explorer.choose(\n                fingerprint=exploration_key,\n",
    )
    source = replace_once(
        source,
        "        self._explorer.note_action(\n            fingerprint=fingerprint, action_id=action_id, data=data\n",
        "        self._explorer.note_action(\n            fingerprint=exploration_key, action_id=action_id, data=data\n",
    )
    with tempfile.TemporaryDirectory(prefix="arc3-exp016-public-") as scratch:
        package = Path(scratch) / "arc_agent"
        shutil.copytree(ROOT / "src/arc_agent", package)
        return build_standalone_source(source, package_root=package)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bins", type=int, default=4)
    parser.add_argument("--quantum", type=int, default=8)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/exp016-abstract.py")
    args = parser.parse_args()
    rendered = build_variant(bins=args.bins, quantum=args.quantum)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print("EXP016_SHA256=" + hashlib.sha256(rendered.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
