# EXP-013: outcome-gated novelty and first-level action accounting

Date: 2026-10-31. **Public ARC-AGI-3 games only.** This is an isolated
fake-model experiment and a local evaluation instrumentation fix, *not* a
validated Qwen improvement, RHAE score, or official Kaggle submission.

## Prior real-Qwen release gate

The original EXP-005 / PR #10 followed EXP-001 (earlier official 0.00
score), then EXP-002 through EXP-004 (no levels in their shorter 15-action
public Qwen samples). Those different action limits are not directly
comparable. As rechecked using the Kaggle CLI, the private EXP-005 v4
save-and-run notebook and the private EXP-009 notebook both show COMPLETE.

On four matching **public** games with 80 actions/game, Qwen3.8-27B FP8
on pinned Python 3.12 / NVIDIA RTX PRO 6000 / internet disabled:
- EXP-005 v4: 2 completed levels, 147 real Qwen calls, 700.78 s summed
  game wallclock.
- EXP-009: 2 completed levels, 100 real calls, 502.36 s summed game wallclock.
- First level actions: r11l 21 versus 32 (worse in EXP-009);
  tn36 42 versus 36 (better in EXP-009).

EXP-009 is a compute-efficiency reference, **not** an established RHAE
or leaderboard improvement. Evidence: GitHub PRs #10, #15, #16 and their
links to the private public-only Kaggle probes.

## Hypothesis and isolated implementation

The main obstacle remains completing more levels efficiently, not just
reducing Qwen inference. A game-agnostic policy may respond sooner to
**exact visible self-transitions**: after at least N such observations
in the last four outcomes, switch coordinate-capable controls to model-free
novelty after four stagnant moves instead of the baseline eight. We tested
N=2 and N=3. Non-coordinate controls retain the exact baseline policy.

The filter is deliberately conservative: a transition with an observed
level increase or game-state change ends the recent evidence window.
Identical visible frames do not prove the absence of hidden-state changes;
the existing `proven_noop` flag is only a *visible* state proxy. Raw pixel
changes are never counted as level progress. No game-specific IDs, solutions,
private test data, or untrusted calls are used.

`scripts/build_exp013_variant.py` builds standalone ablation candidates by
injecting a bounded gate into a temporary source string, leaving the
competition agent and existing Kaggle notebooks untouched. The two
variants and baseline used the same deterministic fake JSON model.

## Public paired protocol and results

25 official public games x 3 independently seeded novelty controllers x 80
actions x 3 policies = **225 sessions and 18,000 actions**. Seeds vary the
controller RNG, not the underlying set of 25 puzzles. Full summary
aggregates, with no raw traces, are in
`experiments/exp013-paired-public-aggregates.json`.

| Public local fake-model metric | EXP-009 reference | N=2 gate | N=3 gate |
| --- | ---: | ---: | ---: |
| Sessions | 75 | 75 | 75 |
| Actions | 6,000 | 6,000 | 6,000 |
| Completed levels | **6** | 6 | 6 |
| Sessions completing a level | 6 | 6 | 6 |
| Fake model calls | 1,616 | 1,520 | 1,565 |
| Summed local CPU wallclock, s | 129.500 | 128.657 | 129.050 |
| Paired level improvements / regressions | -- | 0 / 0 | 0 / 0 |

N=2 reduced fake-model calls by 96 (5.94%); N=3 reduced them by 51
(3.16%). Neither completed an additional level, and **all 75 pairs tied
on completed levels for both variants**. Small differences in CPU time
are not evidence of real-Qwen throughput gains.

### Correcting a measurement blind spot

Equal numbers of completed levels **do not establish equal RHAE**:
the action index of each first completion is also relevant. We added
`scripts/public_level_milestones.py`, extended the public offline harness
to record earliest observed level-completion action indices (not raw
traces), and extended the paired comparator to reject invalid/mismatched
evidence and compare first-level efficiency when both arms provide it.

The supplemental, matched public four-game x three-controller-seed
audit (ls20, vc33, r11l, tn36; 960 actions/arm) found five sessions
completing at least one level in both baseline and N=2. All five reached
their first completion at **the same action index** (sum 201 in each
arm). This does **not** constitute RHAE scoring, but provides no positive
action-efficiency evidence in that selected cohort.

## Safety and interpretation

The deterministic standalone artifacts passed compilation; 158
automated tests passed after the milestone accounting changes.
The public repository preflight and diff validation passed before
publication. No GPU run was started and no official submission consumed.
The Kaggle CLI does not disclose remaining GPU-hour quota.

The hypotheses are consistent with general research on active
abstraction and graph-based interactive exploration, but these results
do not validate a scoring improvement:

- https://arxiv.org/abs/2607.28287
- https://shocklab.net/publications/graph-based-exploration-for-arc-agi-3-interactive-reasoning-tasks/
- https://github.com/arcprize/docs/blob/main/methodology.mdx

**Decision: reject both variants as scoring candidates.** Preserve
EXP-009 as provisional real-Qwen reference. Future work should test
goal-directed transitions and useful exploration frontiers, using both
level completion and per-level action indices. Keep the official Monday,
2026-11-02 submission behind explicit review and approval.
