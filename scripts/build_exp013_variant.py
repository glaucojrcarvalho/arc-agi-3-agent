#!/usr/bin/env python3
"""Build isolated EXP-013 outcome-gated novelty candidates.

Only the standalone generated agent is patched. The candidate accelerates the
switch to model-free exploration when recent *exact* no-effect observations
suggest that the current LLM action proposals are not changing the world.
Never interpret pixel differences as level progress; require observed
levels_completed to measure progress. This is not a deployed agent.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_standalone_agent import build_standalone_source

ROOT = Path(__file__).resolve().parents[1]

HELPER = '''
def _exp013_recent_exact_noops(transitions):
    """Count exact visible self-transitions in the last four outcomes.

    Explicit level progress or a state transition ends the evidence window.
    Visual change alone is NOT treated as a solved level.
    """
    count = 0
    considered = 0
    for event in reversed(transitions):
        if event.get("levels_delta", 0) != 0 or event.get("state_changed") is True:
            break
        if considered >= 4:
            break
        considered += 1
        if event.get("proven_noop") is True:
            count += 1
    return count

'''


def build_variant(*, min_noops: int = 2, fast_after: int = 4) -> str:
    if min_noops not in (2, 3, 4):
        raise ValueError("min_noops must be 2, 3 or 4")
    if fast_after not in (3, 4, 6):
        raise ValueError("fast_after must be 3, 4 or 6")
    source = (ROOT / "agent/exp005_agent.py").read_text(encoding="utf-8")
    marker = "\nclass MyAgent(Agent):"
    if source.count(marker) != 1:
        raise ValueError("EXP-013 insertion point changed: class")
    source = source.replace(marker, "\n" + HELPER + marker, 1)
    before = """        self._belief.max_stagnation = (
            self.COMPLEX_NOVELTY_AFTER if complex_ids else self.KEYBOARD_NOVELTY_AFTER
        )
"""
    after = f"""        self._exp013_noop_evidence = _exp013_recent_exact_noops(recent_transitions)
        self._belief.max_stagnation = (
            {fast_after} if (complex_ids and self._exp013_noop_evidence >= {min_noops})
            else self.COMPLEX_NOVELTY_AFTER if complex_ids
            else self.KEYBOARD_NOVELTY_AFTER
        )
"""
    if source.count(before) != 1:
        raise ValueError("EXP-013 insertion point changed: stagnation gate")
    source = source.replace(before, after, 1)
    before_reasoning = '            "novelty_after_steps": self._belief.max_stagnation,\n'
    after_reasoning = (before_reasoning
        + '            "exact_noop_evidence": self._exp013_noop_evidence,\n')
    if source.count(before_reasoning) != 1:
        raise ValueError("EXP-013 insertion point changed: diagnostics")
    source = source.replace(before_reasoning, after_reasoning, 1)
    return build_standalone_source(source, package_root=ROOT / "src/arc_agent")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-noops", type=int, default=2, choices=[2, 3, 4])
    parser.add_argument("--fast-after", type=int, default=4, choices=[3, 4, 6])
    parser.add_argument("--output", type=Path, default=ROOT / "dist/exp013_candidate.py")
    args = parser.parse_args()
    rendered = build_variant(min_noops=args.min_noops, fast_after=args.fast_after)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print("EXP013_SHA256=" + hashlib.sha256(rendered.encode()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
