# EXP-020 — independently seeded Kaggle public probe and validated level milestones

**Date:** 2026-11-01. **Status:** evaluation instrumentation; no production policy promotion.
This experiment operates on the public ARC-AGI-3 games only. It does not run
or submit official competition evaluations.

## Real Qwen evidence recovered before this change

All listed Kaggle notebook versions finished with status `COMPLETE`.
The EXP-005 source PR #10 remains draft. EXP-002 (2 x 15 actions),
EXP-003 (2 x 15), and EXP-004 (3 x 15) completed zero public levels;
their short budgets cannot be compared directly with the later probes.

On **exactly the same four public games**, with 80 actions per game and
the same fixed baseline controller seed, the previously saved real-model
results were:

| Probe | Public levels | Actions | Qwen calls | Sum measured wallclock |
| --- | ---: | ---: | ---: | ---: |
| EXP-005 v4 | 2 | 320 | 147 | 700.78 s |
| EXP-009 | 2 | 320 | 100 | 502.36 s |
| EXP-019 | 2 | 320 | 99 | 469.06 s |

The EXP-019 delta relative to EXP-009 was **one fewer call (1.0%)** and
**33.30 s less measured wallclock (6.63%)**. Both still completed exactly
two levels. In `r11l`, first level completion occurred after action 32
under both agents; in `tn36`, it occurred after action 36 for EXP-009
and action 25 for EXP-019. These are **observed single-run results**, not
an estimated RHAE gain or a statistically reliable score improvement.

The **most consequential failure** is that `ls20` and `vc33` each
completed zero levels after 80 actions in EXP-019, including 59 and 54
model-free exploration actions respectively. More randomized exploration
alone is not established as a way to discover objectives. A prompt-only
policy change cannot be validated by fake-model smoke tests.

## Corrected experimental protocol

Prior real-Qwen probes fixed the public game environment seed, and the
agent's exploration RNG was deterministically derived from the game ID.
Changing only the environment seed does **not** give independent controller
trials. The existing local fake-model evaluator supported independent RNG,
but Kaggle real-Qwen probes could not request it.

EXP-020 adds a **probe-only**, explicitly opt-in controller seed. Its
SHA-256 derivation matches the existing local evaluator and is independent
between each public game and trial. The competition agent is left unchanged:
no new game-specific rules, inference behavior, action heuristics or private
inputs. The default probe remains byte-for-byte equivalent in action
selection when the seed option is omitted.

Each public probe now records first completion as the **action index after
which `levels_completed` increases**. Pixel differences and animation
frames are never used to infer level advancement. A strict comparator checks
probe completion, game inventory, trial-level **and per-game** seed metadata,
official level counters and traces before emitting only **aggregated**
metrics; it refuses unpaired or internally mixed-seed comparisons. No raw trace, generated submission artifact or prior-game
solution is published with the report.

The Kaggle notebook generator exposes `--probe-controller-seed 101` for
EXP-020, while preserving the existing offline vLLM/Qwen3.8-27B FP8 model,
fixed Python 3.12 container digest, local wheelhouse, private notebook,
internet disabled and **RTX PRO 6000**. This uses Kaggle **save-and-run**
only; generating `submission.parquet` is not an official submission.

## Completed 25-game, three-seed local transport comparison

The independent EXP-009 baseline and EXP-020 agent were evaluated on the
**same 25 public games, with controller seeds 0, 1 and 2**, at 80 actions
per session. The two runs each executed **75 sessions / 6,000 actions**
(12,000 actions combined) with the same deterministic fake model.

| Transport metric | EXP-009 baseline | EXP-020 |
| --- | ---: | ---: |
| Verified public levels | 6 | 6 |
| Fake-model calls | 1,616 | 1,616 |
| Sessions with a level | 6 | 6 |
| Sum local CPU wallclock | 131.245 s | 134.184 s |

All **75 paired comparisons tied**, with zero improved/regressed sessions
and all 25 games showing no net change. This is expected: no production
policy changed, and the fake model ignores prompt content. The CPU time
difference is noise, not a speed claim. The experiment verifies
controller-seed control, repeatability and compatibility only.

The checked, **public-only aggregate reports** are
`experiments/exp020-fake-public-aggregate.json` and
`experiments/exp020-qwen-public-aggregate.json`. These contain no
action traces, screenshots or private evaluation results. The strict
Qwen comparator measured the unseeded EXP-009/EXP-019 runs only.

**Validation:** 147 unittest checks passed; source compiled;
`public_preflight.py --all` passed. The notebook source was regenerated
and metadata checked for private/offline RTX PRO 6000, pinned Python
3.12 image digest, FP8 Qwen model and fixed wheelhouse.

## Validity and promotion gate

- The fake-model 25-game/three-seed A/B screen is a compatibility test,
  not evidence of better Qwen reasoning.
- A seeded real-Qwen EXP-020 run must **not** be compared with the earlier
  unseeded EXP-009/EXP-019 runs; such a comparison would be confounded.
- To establish any performance delta at seed 101, first obtain a **paired**
  EXP-009 baseline at the same controller and environment seeds.
- Do not promote a scoring candidate without assessing completed levels,
  actions to first completion, Qwen calls, and wallclock per public game.
  No official competition submission before the user's Monday review.

Research motivation: [Tycho: Active Abstraction](https://arxiv.org/abs/2607.28287)
distinguishes actionable states from animation and emphasizes decisions about
when modeling is useful; [Kepler: Auditable World Models](https://arxiv.org/abs/2610.00834)
shows why verifiable transitions and first-attempt reporting matter. Neither
study establishes improvements for this FP8 Qwen configuration.
