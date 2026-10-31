# EXP-014: state-conditioned click novelty in ARC-AGI-3

Date: 2026-11-01. Public-only, deterministic FAKE-model study.
This is not a Kaggle score, a Qwen run, RHAE, or hidden-set validation.

## Rechecked starting point

PR #10 (EXP-005) developed persistent goals, hypotheses and transition-aware
novelty. EXP-001 scored 0.00 in its earlier official submission;
EXP-002 through EXP-004 showed zero completions in shorter public probes.
Those runs are not matched comparisons to later 80-action probes.

The Kaggle CLI rechecked EXP-005 v4 and EXP-009; both were COMPLETE.
In four matched public games of 80 actions each, actual Qwen3.8-27B FP8
on NVIDIA RTX PRO 6000 completed 2 levels in both:
EXP-005 v4 used 147 Qwen calls, 700.78 s accumulated wallclock;
EXP-009 used 100 calls, 502.36 s. The first-level action count worsened
on r11l (21 vs 32) and improved on tn36 (42 vs 36), respectively.
EXP-009 is a compute-efficiency baseline, not an established RHAE gain.

## Hypothesis and change

The novelty controller counted visits only by (visible-state, action-ID).
For click actions that conflates different coordinates, even when one
coordinate was repeatedly attempted in the same visible state.
This experiment adds a bounded 256-entry FIFO of exact
(state fingerprint, action ID, x, y) attempts, prioritizes least-attempted
salient coordinates for the current state, and keeps the existing 20%
uniform spatial exploration. State click memory is cleared on observed
level completion; raw pixel changes never count as score progress.

Only this EXP-014 branch changes the agent's helper module. The accepted
Kaggle notebook, GPU configuration, offline dependency pins, and official
submission state remain unchanged.

## Paired local test

25 official public games, 3 independently seeded controller RNG states
(0, 1, 2), at most 80 actions per session, two policies.
150 sessions; a total of 12,000 attempted actions.
Same game/seed pairs in both policies. Model = deterministic FAKE JSON
response; no GPU or internet required.

| Metric | EXP-009-policy baseline | EXP-014 state-click |
| --- | ---: | ---: |
| Sessions | 75 | 75 |
| Actions | 6000 | 6000 |
| Completed levels | 6 | 6 |
| Sessions with level completion | 6 | 6 |
| Fake-model calls | 1616 | 1614 |
| Redirected action proposals | 881 | 864 |
| Sum of local CPU wallclock (seconds) | 130.048 | 130.374 |

Paired session level-count changes: 0 improved,
0 regressed, 75 tied.
Of 25 distinct public games, 0
had net improvement and 0 net regression.
Redirected action counts changed by +1.93% (positive means
fewer redirects); this is an action-selection diagnostic, NOT RHAE.

For 6 sessions in which both
policies completed the first level, EXP-014 was faster on
0, slower on 0, and
equal on 6; first-level completion action-index
sums were 229 vs
229. This is not an
official action-efficiency score and does not imply hidden-set transfer.

## Reproduction and safety

Build a one-file baseline from the unchanged EXP-013 parent, a candidate
from this branch, and run scripts/smoke_exp005_public_offline.py against
the 25 official public environments using --seeds 0 1 2,
--max-actions 80 and --vary-policy-seed. Compare with
scripts/compare_public_controller_seeds.py. Generated standalone files
and raw session recordings are NOT published.

162 automated Python tests passed locally. The public preflight and
diff checks passed. Only sanitized aggregates and source changes are
committed, with no credentials, hidden evaluations, private conversation,
raw action traces, or local environment paths.

Decision: No validated score improvement; reject as submission candidate and preserve EXP-009 provisional.

No new Kaggle GPU execution or official competition submission was made.
The Monday 2026-11-02 user-reviewed submission gate remains in effect.

## Relevant public research

- https://arxiv.org/abs/2607.28287 (Tycho: active abstraction and
  conditional model building for interactive game reasoning).
- https://arxiv.org/abs/2610.00834 (Kepler: audit world models,
  avoid overinterpreting public-set performance).
- https://arcprize.org/competitions/2026/arc-agi-3
