#!/usr/bin/env python3
"""Generate isolated EXP-017 coverage-scheduling ablations for public tests.

No change to the competition source agent or any model/runtime settings.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from build_standalone_agent import build_standalone_source

ROOT = Path(__file__).resolve().parents[1]
LEVEL_ANCHOR = '        level = int(getattr(latest_frame, "levels_completed", 0) or 0)\n'
CHOOSE_ANCHOR = '            proposed = self._explorer.choose(\n                fingerprint=fingerprint,\n'
NOTE_ANCHOR = '        self._explorer.note_action(\n            fingerprint=fingerprint, action_id=action_id, data=data\n'

def replace_once(src: str, needle: str, replacement: str) -> str:
    if src.count(needle) != 1:
        raise ValueError("EXP-017 source anchor missing or ambiguous")
    return src.replace(needle, replacement, 1)

def build_variant(*, mode: str, window: int = 12) -> str:
    if mode not in {"level", "window"}:
        raise ValueError("mode must be level or window")
    if isinstance(window, bool) or not isinstance(window, int) or not 4 <= window <= 32:
        raise ValueError("window must be an integer 4..32")
    body = (ROOT / "agent/exp005_agent.py").read_text(encoding="utf-8")
    key = (
        '        exploration_key = f"level:{level}"\n'
        if mode == "level"
        else f'        exploration_key = f"level:{{level}}:window:{{self._feedback.turns // {window}}}"\n'
    )
    body = replace_once(body, LEVEL_ANCHOR, LEVEL_ANCHOR + key)
    body = replace_once(body, CHOOSE_ANCHOR,
                        CHOOSE_ANCHOR.replace("fingerprint=fingerprint", "fingerprint=exploration_key"))
    body = replace_once(body, NOTE_ANCHOR,
                        NOTE_ANCHOR.replace("fingerprint=fingerprint", "fingerprint=exploration_key"))
    with tempfile.TemporaryDirectory(prefix="arc3-exp017-public-") as scratch:
        package = Path(scratch) / "arc_agent"
        shutil.copytree(ROOT / "src/arc_agent", package)
        return build_standalone_source(body, package_root=package)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("level", "window"), required=True)
    parser.add_argument("--window", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = build_variant(mode=args.mode, window=args.window)
    compile(artifact, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(artifact, encoding="utf-8")
    print("EXP017_SHA256=" + hashlib.sha256(artifact.encode("utf-8")).hexdigest())

if __name__ == "__main__":
    main()
