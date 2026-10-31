# EXP-012 — bounded coordinate-affordance action prior (rejected)

Date: 2026-10-31. **Official public ARC-AGI-3 games only**. This is a
controlled, local **fake-model** ablation. It does not constitute a Qwen
improvement, RHAE score, or Kaggle leaderboard result.

## Actual Kaggle evidence reviewed before the experiment

Both private *save-and-run* notebooks were checked through the Kaggle CLI and
remain `COMPLETE`, with `probe_complete=true` in their retrieved public-only
checkpoints. EXP-005 v4 and EXP-009 used the same Qwen3.8-27B FP8 model, pinned
Python 3.12 image, offline RTX PRO 6000, and four public games × 80 actions:

| Observed public probe | EXP-005 v4 | EXP-009 |
| --- | ---: | ---: |
| Completed levels | 2 | 2 |
| Real Qwen calls | 147 | 100 |
| Summed game wallclock | 700.78 s | 502.36 s |
| First level in `r11l` | action 21 | action 32 |
| First level in `tn36` | action 42 | action 36 |

Thus EXP-009 used 31.97% fewer Qwen calls and 28.31% less game wallclock,
but **no level-count gain and no established scoring improvement**. EXP-001
previously reported a 0.00 official score; EXP-002 through EXP-004 short
real-Qwen public probes completed no levels. Their shorter action budgets
are not comparable with the EXP-005/009 probes. PR #10 introduced the
original belief, bounded plan, and novelty strategy.

Evidence links: [EXP-005 v4 Kaggle](https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-005-persistent-reasoning-policy),
[EXP-009 Kaggle](https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-009-persistent-reasoning-policy),
[PR #10](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/10).

## Hypothesis and exact isolation

The model-free novelty explorer picks the least-visited (settled-frame,
action-ID) pair, randomized on ties. If several salient pixel targets exist,
EXP-012 hypothesized that favoring the legal complex/click action would
help the agent discover actionable visual objects rather than spending
moves on generic keyboard controls. This is *only an affordance prior*, not
a level-progress signal; pixel changes are never scored as goal completion.

`scripts/build_exp012_variant.py` renders an isolated standalone candidate
by patching the *temporary build-time copy* of
`src/arc_agent/novelty_explorer.py`, leaving the actual competition agent,
Qwen policy and default explorer **unchanged**. The probability is applied
only when a legal complex action and >=4 salient targets are available;
keyboard-only environments follow the original path. It does not learn
from public game identifiers, use game-specific solutions, or depend on
hidden evaluation data.

Rendered standalone SHA-256 checksums:

- Complex action prior 0.65: `7fd66e7cdc2fde7cfd9a06ade5c7f6d6d980c3e1dedf8c51682766f768b18253`
- Complex action prior 0.25: `6cf5b11c3aac0319bf2cca1fd814b1ba642341ac0ca3b1ca542727043af94839`

A synthetic stable-board control generated 67 complex actions out of 200
for the baseline, 67 for 0.25, and 138 for 0.65. Thus 0.65 genuinely
changed complex-action frequency, while 0.25 primarily perturbed action
order and RNG. Synthetic click frequency is **not** puzzle progress.

## Paired, canonicalized public evaluation

Each arm was independently run on the **same 25 public games × 3 independently
seeded controllers × 80 actions = 6,000 executed actions/arm**, with
`--vary-policy-seed`, canonical short/full public ID aliases, and the same
fixed deterministic fake model. The baseline was reused for both comparisons.
A total of **18,000 public-game actions** were executed across the three
arms. The 75 sessions/arm repeat 25 public environments; they are not
75 distinct unseen games.

| Metric | Baseline EXP-011 | 0.25 prior | 0.65 prior |
| --- | ---: | ---: | ---: |
| Completed public levels | **6** | 4 | 3 |
| Sessions with a level | **6/75** | 4/75 | 3/75 |
| Fake-model calls | **1,616** | 1,626 | 1,622 |
| Executed actions | 6,000 | 6,000 | 6,000 |
| Sum of local CPU wallclock | 135.169 s | 131.774 s | 132.337 s |
| Paired improvements | — | 1 | 1 |
| Paired regressions | — | 3 | 4 |
| Paired ties | — | 71 | 70 |
| Games with net positive delta | — | 0 | 0 |
| Games with net negative delta | — | 2 | 2 |

Both priors regressed relative to baseline. 0.25 produced one fewer lost
level than 0.65 but still lost two levels net; neither candidate improved
a public game in aggregate. The modest local CPU timing differences are
not proof of GPU speedups, particularly with added fake-model calls and
potential machine contention. The paired comparator and aggregate-only
per-game deltas are in `experiments/exp012-paired-public-aggregates.json`;
no raw action trajectories were stored in the repository.

## Decision and next candidate criteria

**Reject both action priors. Do not promote either to Kaggle.** More
clicking did not translate into more levels. An evidence-informed future
policy should condition action selection on **observed transition outcomes**
and testable world-model predictions, with strict reward based on actual
`levels_completed` and first-level action counts rather than raw pixel
change or synthetic click coverage. This direction is motivated by the
public research on programmatic world models and verification, not a claim
of demonstrated gains for this specific agent:

- https://arxiv.org/abs/2607.28287 (Tycho, active abstraction, July 2026)
- https://arxiv.org/abs/2610.00834 (Kepler, auditable world models, Sept 2026)
- https://arcprize.org/blog/arc-agi-3-human-dataset (human action efficiency, April 2026)

**Validation:** 148 automated tests passed locally, including new explicit
keyboard-only invariance, determinism, bounds, probability validation, and
high-bias manipulation checks. All source changes are confined to the
experiment builder and tests. Kaggle reported EXP-005 and EXP-009 COMPLETE;
no new GPU notebook or official competition submission was started. The
Kaggle CLI does not expose remaining GPU-hour quota. Keep this PR in draft
until the scheduled 2026-11-02 candidate review.

**Public-only boundary:** no personal context, credentials, environment
secrets, private game state, hidden evaluation logs, replay traces, or
raw Qwen outputs are committed. The offline/RTX/Qwen notebook artifact
and dependency pinning remain untouched.
