# ARC-AGI-3 portfolio handoff — 2026-11-03

## Subsequent portfolio gate — 2026-11-03 04:05 UTC

[PR #33](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/33)
merged as `24c9cecbb8283aa1965b167dfe7de4de22dc04b8` without modifying the
agent policies. It adds a **read-only** remote-branch reachability/unique-commit
report (`scripts/report_branch_lifecycle.py`), four disposable-local-repository
regression tests and the [retention decision matrix](branch-retention-20261103.md).
As of the post-merge fetched remote snapshot, **33 refs including main**,
**17 additional reachable heads** and **15 unmerged heads** were present.
**No remote branches were deleted** because deletion also requires verified
evidence references and write authorization; remote Git credentials were
unavailable to the isolated Remote Workbench clone. The remaining open
PR is #5 (legal/attribution hold); no issues were open at the audit.

Fresh head `96846229bec66fa94499120160bbf2fee65948ea` and post-merge
worktrees passed **168/168 unit tests**, clean preflight (**97 tracked
files**), `compileall`, standalone EXP-000 packaging and `py_compile`,
and `git diff --check`. Public-only offline smoke ran the unchanged
EXP-001 and EXP-002 policies on `ls20` and `vc33` with a dummy model:
**4 sessions / 20 actions / 0 completed levels**, with no contract
errors. This is **not** real-Qwen or Kaggle score evidence. The EXP-000
agent blob remains `9695133008db25b63f042ea6371c34a57308a710`.
The documented official EXP-019 v1 public score **0.34** and its
historical submission are unchanged; no post-deadline Kaggle activity.

This is a **post-deadline engineering report**, not a new ARC-AGI-3
submission or a statement of final leaderboard position.

## Latest portfolio checkpoint — 2026-11-03 03:xx UTC

**Current engineering merge:** [PR #32](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/32)
merged into `main` as
[`5826438d48f30898f36745f513e8177104a083f8`](https://github.com/glaucojrcarvalho/arc-agi-3-agent/commit/5826438d48f30898f36745f513e8177104a083f8).
A narrowly scoped extraction from EXP-020/021 enhanced the existing
`scripts/compare_real_public_probes.py` rather than overwriting it with
the conflicting branch version. Three paths changed: comparator, regression
tests, [seed contract](seeded-probe-validation.md). This verifies explicit
probe/row controller and environment seeds, authoritative milestone counters
and public-only provenance; legacy unseeded output is explicitly labeled.
**Neither new agent policy nor score improvement was introduced.**

The branch exact HEAD `63e587ae8e51c8bca03ba0e6412b1515564a90b5`
was tested in a fresh Remote Workbench worktree: Python 3.12.15,
**164/164 unittests**, clean public preflight (**94 tracked files**),
`compileall`, standalone build/`py_compile`, `git diff --check`.
The prospective merge tree matched the tested tree at
`35ebb2a5d8cf8a30fbc5cc9d94f18f9fa4b8a522`; post-merge
independent verification reproduced the same results. The default
EXP-000 agent blob remained `9695133008db25b63f042ea6371c34a57308a710`.
No GitHub Actions were requested. The external `arc_agi` package was
absent in this isolated environment: **no new live public-game smoke or
Qwen-real probe was run**; standalone build is not gameplay validation.

[PR #26](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/26)
was **closed as archived experimental history**, with the original
EXP-020/021 notebook changes and evidence retained in its branch and
PR discussion. The seed-101 real-Qwen pair completed 1 vs 1 levels;
the single completion was later by 13 actions in the candidate.
[PR #28](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/28)
was **closed without merge**; EXP-023 remains an unvalidated
fake-model tie (6 vs 6), not a scoring promotion. Both experimental
branches were retained. **One PR remains open: #5**, held on
authorship/third-party attribution and the ARC Prize author-code
licensing distinction; **zero GitHub issues open**.

Read-only remote branch inventory: **32 actual remote branch refs**,
**17 whose heads are reachable from `main`** and **15 with distinct
unmerged commits** after #32; a local scratch tracking alias
(`origin/exp020`) was excluded from this remote count.
No branches were deleted or force-pushed. Competition artifact
EXP-019 v1 `57915318`, public **0.34**, was not touched.
No post-deadline Kaggle submission or quota use took place.

The next competition should begin from the verified engineering main
with a **separate** hypothesis branch, not from unvalidated EXP-022/023
or an inference that the historical result predicts a new score.
Review the new competition's own scoring, runtime, licenses, submission
quota, data provenance and public vs hidden evaluation contract before
any submission.

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

## Finalized multi-seed evaluator — PR #12 (2026-11-03 UTC)

[PR #12](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/12)
was retargeted from the obsolete EXP-005 feature base to `main` and merged
with history-preserving commit
[`f340b8e86e8130ae3cebba1ea79ac981e10c5741`](https://github.com/glaucojrcarvalho/arc-agi-3-agent/commit/f340b8e86e8130ae3cebba1ea79ac981e10c5741).
The exact dry-run merge and real merge had matching Git tree
`680783649b9484ee3a00cae7295bc4ee11a68571`. Three paths changed:
`scripts/evaluate_public_exploration.py`,
`tests/test_public_exploration_multiseed.py`, and
`docs/exp006-multiseed-public-screen.md`.

An isolated Python 3.12.15 worktree passed `public_preflight --all` (**93
tracked files**), `compileall`, **157/157 unittests**, standalone building,
`py_compile` and `git diff --check` before merge, and the same gates after.
Default EXP-000 agent Git blob remained `9695133008db25b63f042ea6371c34a57308a710`.

Unlike the earlier smoke blocker, the public-only `arc_agi` package and
environment files were available in this dedicated validation environment.
The merged seed-aware evaluator completed **8 deterministic offline sessions,
120 actions, 0 level completions** on public `r11l`/`tn36` (seeds 0,1,
random/novelty, 15 moves each). The correct EXP-005 FAKE-model standalone
then completed **2 public sessions, 10 moves, 10 simulated calls, 0 levels**
without contract failures. An initial misconfigured invocation tried the
EXP-005 smoke with an EXP-000 standalone and failed because EXP-000 lacks
`model_calls`; using the intended EXP-005 source resolved the invocation.
Neither run is real-Qwen validation, an EXP-019 replay, or new scoring evidence.

Now **three open PRs remain**: #5 (relicensing blocked), #26 (seeded
comparison/evaluation still isolated), #28 (unvalidated EXP-023 memory).
An isolated dry-run of #26 after the #12 merge produced an add/add merge
conflict in `scripts/compare_real_public_probes.py` against merged #16.
It was aborted without touching other agents' worktrees or updating #26.
The correct follow-up is a separately reviewed extraction of compatible
strict-seed/per-level completion validation and tests; preserve EXP-021's
non-improved real-Qwen 1-versus-1-level comparison in its PR history.
There was **no new Kaggle submission** or change to EXP-019 v1 0.34.

## PR disposition after integration

**2026-11-03 portfolio checkpoint:** [PR #16](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/16) merged into `main` as [`d7eb2bb`](https://github.com/glaucojrcarvalho/arc-agi-3-agent/commit/d7eb2bb653b626f85b1d6cc2e188d3ac0fe1aa23). Only `scripts/compare_real_public_probes.py`, `tests/test_compare_real_public_probes.py` and `docs/exp010-real-qwen-probe-audit.md` were added. The exact prospective merge tree and post-merge tree matched (`b9e8c99becb976b3a2ca4f3928b65b0aae8068b5`); the default EXP-000, EXP-005 policy and Kaggle builder retained their original Git blobs. A fresh detached post-merge checkout passed **154/154** unit tests, clean public preflight (**91 tracked files**), `compileall`, standalone packaging and `py_compile`. The external `arc_agi` package was absent; **no live public-game smoke** or new real-Qwen comparison was performed. The EXP-010 audit is read-only, historical, and not a score promotion.

- **Integrated/superseded**, with reachable source commits preserved: #3, #7, #8, #9, #10, #11, #13, #14, #15, #25; [#30](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/30) is merged. Closed PRs retain their links, review conversations, test results, and negative evidence.
- **Archived negative study:** [#17](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/17). Do not merge its regressive balanced-click policy. Only the independent public game-ID/RNG alias correction merits a new narrowly scoped evaluation PR.
- **Integrated audit-only utility:** [#16](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/16) real-Qwen historical public-probe comparison (not a scoring improvement).
- **Integrated after validation:** [#12](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/12) multi-seed public evaluator; see the post-merge gate above.
- **Keep isolated for selective, reviewed extraction:** [#26](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/26) strict seeded comparisons (merge conflict with #16); [#28](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/28) unvalidated observed-completion memory.
- **Licensing hold:** [#5](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/5) proposes relicensing. Maintain existing Apache-2.0 until authorship, external-code attributions, and competition requirements have been reviewed. Do not present a code license as automatic award eligibility.

At the consolidation snapshot, there were **30 remote branches**. Their reachability from `main` was checked before any cleanup; branches with unique unmerged commits have been retained. **No force pushes, history rewrites or remote branch deletions** were performed. Repository description/topics are not asserted changed.

## Handoff for the next competition

Start from this tested baseline, create one isolated experiment per hypothesis, and preserve a stable model-free control. Add the external public environment only when its license and dependencies are known. Re-run offline preflight, compilation, tests, standalone packaging and a bounded contract smoke; then compare paired public games with exact game identifiers, controller seeds, action limits, real model/runtime revisions, level completions, action counts, Qwen calls, failures and wallclock. Record negative outcomes alongside positive ones. Check the **new competition's** rules, approved models, runtime budget, distribution rights, and submission quota from its own authoritative sources; do not transplant the ARC-AGI-3 scoring artifact, Kaggle notebook or assumptions about the previous quota.

See [evidence hierarchy](experiment-evidence.md), [architecture](architecture.md), [research quickstart](research-quickstart.md), and [consolidation decision matrix](portfolio-consolidation-matrix.md).
