# ARC-AGI-3 portfolio handoff — 2026-11-03

This is a **post-deadline engineering report**, not a new ARC-AGI-3
submission or a statement of final leaderboard position.

## Published engineering baseline

- `main` merge: [`feb4f6e3672f1f76467e8e72d97f1eb322a44a29`](https://github.com/glaucojrcarvalho/arc-agi-3-agent/commit/feb4f6e3672f1f76467e8e72d97f1eb322a44a29), integrating reviewed [PR #30](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/30) with merge ancestry rather than a squash.
- The default `agent/my_agent.py` **remains the EXP-000 control**: its Git blob SHA `9695133008db25b63f042ea6371c34a57308a710` is identical before and after integration.
- The model-driven EXP-001 and EXP-005/019 lineage are **opt-in** source files, not the default policy. Source availability, successful packaging, and competition score are different claims.
- Official historical EXP-019 v1 submission `57915318`, displayed public score **0.34**, is external competition evidence and has not been edited, rebuilt as an asserted identical notebook, or resubmitted. Neither 0.34 nor a public fake-model result demonstrates a new score gain from the merge.
- EXP-022 remains a **rejected** fake-model ablation (7→6 completed levels under its protocol); EXP-023 remains **unvalidated** (75 paired fake-model ties, 6→6 levels, without paired real-Qwen inference). Both histories are retained and neither was promoted to the default agent.

## Independent post-deadline gate

A fresh, detached clone at PR #30 head `da341261d088aa40ac133a0464ec5c04a036a996`, never the dirty working tree of another agent, produced:

| Gate | Observed result |
| --- | --- |
| `scripts/public_preflight.py --all` | Clean; **87 tracked files** checked |
| `python3 -m compileall -q agent scripts src tests` | Passed |
| `PYTHONPATH=src python3 -m unittest discover -s tests -q` | **150/150 tests passed** |
| `scripts/build_standalone_agent.py` | Built EXP-000, EXP-001, EXP-005 as three separate sources |
| `python3 -m py_compile` for each generated standalone | Passed all three |
| `git diff --check origin/main...HEAD` and clean checkout | Passed |
| GitHub status checks / Actions | No associated status or PR workflow runs; **not** a CI pass |

A public-game smoke via `scripts/smoke_exp005_public_offline.py` was **not completed** in the isolated clone: the optional external `arc_agi` package was absent. This is not equivalent to a failed agent benchmark, nor should build/syntax checks be described as a game-playing evaluation. The intended local test command **requires** `PYTHONPATH=src`; omitting that environment variable reproduced an import failure, which disappeared with the documented command.

## PR disposition after integration

- **Integrated/superseded**, with reachable source commits preserved: #3, #7, #8, #9, #10, #11, #13, #14, #15, #25; [#30](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/30) is merged. Closed PRs retain their links, review conversations, test results, and negative evidence.
- **Archived negative study:** [#17](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/17). Do not merge its regressive balanced-click policy. Only the independent public game-ID/RNG alias correction merits a new narrowly scoped evaluation PR.
- **Keep isolated for selective, reviewed extraction:** [#12](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/12) multi-seed evaluator; [#16](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/16) real-Qwen audit tooling; [#26](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/26) seeded comparisons; [#28](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/28) unvalidated observed-completion memory.
- **Licensing hold:** [#5](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/5) proposes relicensing. Maintain existing Apache-2.0 until authorship, external-code attributions, and competition requirements have been reviewed. Do not present a code license as automatic award eligibility.

At the consolidation snapshot, there were **30 remote branches**. Their reachability from `main` was checked before any cleanup; branches with unique unmerged commits have been retained. **No force pushes, history rewrites or remote branch deletions** were performed. Repository description/topics are not asserted changed.

## Handoff for the next competition

Start from this tested baseline, create one isolated experiment per hypothesis, and preserve a stable model-free control. Add the external public environment only when its license and dependencies are known. Re-run offline preflight, compilation, tests, standalone packaging and a bounded contract smoke; then compare paired public games with exact game identifiers, controller seeds, action limits, real model/runtime revisions, level completions, action counts, Qwen calls, failures and wallclock. Record negative outcomes alongside positive ones. Check the **new competition's** rules, approved models, runtime budget, distribution rights, and submission quota from its own authoritative sources; do not transplant the ARC-AGI-3 scoring artifact, Kaggle notebook or assumptions about the previous quota.

See [evidence hierarchy](experiment-evidence.md), [architecture](architecture.md), [research quickstart](research-quickstart.md), and [consolidation decision matrix](portfolio-consolidation-matrix.md).
