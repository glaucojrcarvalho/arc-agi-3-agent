# EXP-008 — bounded animation observations and settled-state feedback

Date: 2026-10-31. Scope: public games, unit tests and Kaggle **save-and-run**
only. No official competition submission or private evaluation.

## Confirmed real-model failure (EXP-005 v3)

The private Kaggle notebook
[EXP-005](https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-005-persistent-reasoning-policy)
ended in `KernelWorkerStatus.ERROR` after Qwen3.8-27B FP8 loaded on
RTX PRO 6000 and began evaluating official **public** games. The checkpoint
`exp005-public-probe.json` reports two complete games before the failure:

| Game | Actions | Qwen calls | Max completed levels | Wallclock |
|---|---:|---:|---:|---:|
| ls20 | 80 | 11 | 0 | 51.32 s |
| vc33 | 80 | 36 | 0 | 172.84 s |

The vLLM server log reports HTTP 400 with `VLLMValidationError`:
requesting 320 output tokens plus at least 65,217 input tokens exceeded the
65,536-token context window. No Qwen level result from `r11l` or `tn36` was
checkpointed; do not infer a score from partial results.

### Root cause reproduced locally, without GPU or Qwen

ARC's `FrameData.frame` is a **sequence of animation grids**, not independent
image layers. One action can return multiple rendered frames; the **last**
frame is the settled board for the next action. The previous model prompt
printed every animation frame as a full 64x64 symbol grid. In a deterministic
local public `r11l` trace (seed 0, fake model), an action returned **23**
animation frames but only **four distinct grids**. Repeating all frames
produced a **110,884-character model prompt**. This trace reproduces
the *cause* of oversized context, not the exact real-Qwen trajectory.

References:
- [Public discussion on ARC animation access](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/734369).
- [ARC official agent contract](https://github.com/arcprize/ARC-AGI-3-Agents/blob/main/agents/agent.py).
- [Graph-based exploration paper](https://arxiv.org/abs/2512.24156).

## Changes

1. New opt-in `bounded_animation` observation for EXP-005 only; EXP-001 through
   EXP-004 retain their previous prompt representation.
2. If an animation contains at most four unique frames and at most
   48 consecutive frame runs, encode an **exact frame dictionary** and
   run-length sequence. Otherwise sample at most four marked keyframes,
   including the settled frame, with an omitted-frame count. The sampled
   path is **not lossless**, and the prompt states this.
3. Compute feedback fingerprints, proven no-ops, candidate clicks, bounds,
   and transition diffs using **only the final settled board**. A transient
   animation changing without a settled-state change is no longer falsely
   reported as a new state.
4. Public notebook probe also compares final settled boards, records
   animation frame counts and labels settled changed-cell counts.
   Only `levels_completed` measures level progress.

## Local tests and reproducibility

- `PYTHONPATH=src:. python -m unittest discover -s tests -q`
- `python scripts/build_standalone_agent.py --source agent/exp005_agent.py --output dist/exp005_agent.py`
- `python scripts/build_kaggle_exp005_notebook.py --username glaucojrcarvalho`
- `PYTHONPATH=src:. python scripts/smoke_exp005_public_offline.py --environments-dir /path/to/public/environment_files --seeds 0 1 2 --max-actions 80`

**123 tests pass**, including bounded animation encoding, click-target
selection and proven settled-state no-ops. Kaggle notebook code cells compile,
and metadata still pins offline/private RTX PRO 6000, a Python 3.12 image
by Docker SHA-256, the same Qwen FP8 model and wheelhouse.

### EXP-008 deterministic FAKE-model CPU screening (NOT Qwen)

Four public games x three environment seeds x 80 actions. 12 sessions,
**960 actions**, **3 sessions with one completed level each** (all `r11l`),
**459 fake-model calls**, 489 heuristic actions, 12 resets, summed CPU
wallclock **23.180 s**. This is a contract/behavior screen, not a
Kaggle score or a claim of real-Qwen improvement. The fake model always
proposes `ACTION1`.

## Same-seed local CPU A/B against EXP-007

Both variants used identical public environment versions, four game IDs,
seeds 0/1/2, 80 actions per session and the same fixed-response fake model.
EXP-007 was rebuilt from its original Git commit, independently of EXP-008.

| Metric | EXP-007 | EXP-008 |
|---|---:|---:|
| Sessions / actions | 12 / 960 | 12 / 960 |
| Sessions completing at least one level | 3 | 3 |
| Completed levels | 3 | 3 |
| Games with completed levels | r11l only | r11l only |
| Fake-model calls | 417 | 459 |
| Heuristic actions | 534 | 489 |
| Resets | 9 | 12 |
| Sum session CPU wallclock | 58.491 s | 23.180 s |

EXP-008 took approximately **60.4% less CPU wallclock** on this local
screen, mostly because it stopped hashing/serializing animation sequences
as state. This is **not a measured Qwen speedup**. EXP-008 made 42 *more*
fake-model calls, which could increase real GPU inference time. No
improvement in completed levels is observed in the paired public screen.

## Release gates

- [x] Same-seed model-free A/B recorded; **no level gain** demonstrated.
- Confirm no concurrent Kaggle GPU notebook before one EXP-005 v4
  save-and-run. The Kaggle CLI does not expose reliable GPU-hour balance.
- Verify the real-Qwen v4 checkpoint for four public games, inference calls,
  actual completed levels, wallclock, and runtime errors.
- Keep this PR draft and perform **no official competition submission**
  before the Monday 2026-11-02 review with the user.
