# EXP-015 — bounded keyboard momentum; public-only controlled ablation

Date: 2026-11-01. Draft experiment based on EXP-009 (commit d2a8a17).
No official Kaggle submission, hidden evaluation, or real-Qwen inference occurred.

## Evidence-based starting point

EXP-001 earlier scored 0.00 in an official attempt; EXP-002–004 completed
no levels in shorter, nonmatched public probes. PR #10 introduced
persistent unverified goals and hypotheses with cheap novelty exploration.
Kaggle's EXP-005 v4 and EXP-009 both finished COMPLETE. In four *matched*
real-Qwen public probes (80 actions/game), each completed two levels.
EXP-005 v4: 147 Qwen calls, 700.78 s total wallclock; EXP-009:
100 calls, 502.36 s. First-level r11l worsened from action 21 to 32;
tn36 improved from 42 to 36. This is no proof of RHAE improvement.

We inspected the saved real-Qwen EXP-009 checkpoints again. Across all
320 actions there were zero **exact** proven no-ops, and every settled
frame changed at least one cell. Thus exact-frame novelty is a weak
signal for success. The only two observed first-level transitions
followed heuristic coordinate actions; this keyboard-only EXP-015
cannot be presumed to reproduce those gains.

## Hypothesis

For keyboard-like actions, a single new settled state may indicate a
movement direction worth continuing for a few moves. EXP-015 builds
a model-free *momentum* ablation: if the immediately previous keyboard
action led to a previously unseen settled fingerprint, it may be
repeated with probability 0.55 or 0.80, limited to three successive
identical actions. Stop on identical frames, recent six-state cycles,
coordinate actions, or observed level-completion reset. Every choice
remains subject to the baseline legal-action and feedback guards.
Changed pixels are **not** a level-completion or score proxy.

This is an ablation, not a hard-coded public-game solution. The
EXP-009 production agent and accepted Kaggle metadata stay unchanged.

## Paired 25-public-game experiment

Every policy was separately built from the same EXP-009 tree. The
controller RNG was independently reseeded for each public game and
evaluation seed (0, 1, 2); environment starting states may still be
identical. Each session permits at most 80 actions. All runs use the
same constant deterministic FAKE model, not Qwen. Exactly 225 public
sessions / 18,000 attempted actions were evaluated.

| Metric | EXP-009 baseline | EXP-015 p=0.55 | EXP-015 p=0.80 |
|---|---:|---:|---:|
| Sessions / attempted actions | 75 / 6,000 | 75 / 6,000 | 75 / 6,000 |
| Completed levels | 6 | 6 | 7 |
| Sessions with a completion | 6 | 6 | 7 |
| Fake-model calls | 1616 | 1613 | 1616 |
| Local summed wallclock, s | 135.061 | 136.489 | 135.028 |
| Paired improvements / regressions | — | 0 / 0 | 1 / 0 |

p=0.55 changed fake calls by -0.19% and
local wallclock by +1.06%.
p=0.80 changed fake calls by +0.00% and
local wallclock by -0.02%.
Wallclock was measured on CPU against a fake model, not an RTX PRO 6000.
Paired units are game/controller-seed trials, NOT 75 independent games.

## Direct first-level action-index diagnostic

Independently replayed the predeclared public subset r11l/sp80/tn36, three controller seeds, 80 actions, using the EXP-014 harness with explicit completion milestones. These are first-completion action indices, NOT official RHAE.

- m55: 6 paired first-level completions, candidate faster 1, slower 0, equal 5; action-index sums 229 vs 215.
- m80: 6 paired first-level completions, candidate faster 1, slower 0, equal 5; action-index sums 229 vs 215.

## Independent controller RNG holdout (seeds 3, 4, 5)

Predeclared the p=0.80 candidate after inspecting the first cohort. Repeated the same 25 public tasks under three **new controller RNG** seeds, 80 actions each, with the same FAKE model. This is not independent task generalization.

Baseline: 8 levels, 1642 fake calls, 137.941s CPU. Candidate: 7 levels, 1644 fake calls, 139.790s CPU. Paired improvements: 1, regressions: 2, ties: 72.

## Decision and controls

The p=0.80 signal did not generalize cleanly across randomized controller holdout trials. Reject as a submission candidate; preserve EXP-009. No speculative GPU run.
Model-call savings alone are insufficient; the objective is scored level
completion and human-relative action efficiency. No GPU quota was
consumed, no offline Kaggle dependency or pinned model image changed,
and no competition submission was made. EXP-009 remains the provisional
submission candidate pending the user's Monday 2026-11-02 decision.

142 automated tests passed locally, including EXP-015 source and
standalone-compilation regressions. Public preflight and GitHub Actions
results must be checked separately before merge. This repository
contains only the generator, unit tests and sanitized aggregate data.
Raw action traces, frames, local runtime paths and credentials were
excluded from publication.

Public context:
- https://arxiv.org/abs/2607.28287 (Tycho, active abstraction)
- https://arxiv.org/abs/2610.00834 (Kepler, testable world models)
- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview
