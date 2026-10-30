# EXP-006 — Three-seed public exploration screen

**Date:** 2026-10-30. **Scope:** public ARC-AGI-3 environments only; model-free CPU screening, **not** real-Qwen inference, Kaggle leaderboard scoring, or hidden evaluation.

## Reproducible protocol

- Public games: all 25 official public environments.
- Environment seeds: `0 1 2`; deterministic policy randomness is keyed by game and seed. Seed 0 preserves the existing single-seed random sequence.
- Actions: up to 80 executed per (game, seed, policy) session.
- Policies: deterministic pseudorandom legal-action selection (`random`) versus least-visited (exact visible frame, legal action), with salient click candidates (`novelty`).
- Number of sessions: 25 games × 3 seeds × 2 policies = **150**, 75 per policy.
- Runtime: offline public `Arcade` with CPU; no game-specific solution rules, privileged observations, competition submit, or GPU.
- Invoke in a Python environment containing the public ARC dependencies:

```bash
PYTHONPATH=src:. python scripts/evaluate_public_exploration.py \
  --environments-dir /path/to/public/environment_files \
  --actions 80 --seeds 0 1 2 --policies random novelty \
  --output /tmp/arc3-exp006-public-seeds.json
```

The evaluator now counts **actual executed moves**, even if a game terminates before the first move, and reports elapsed wallclock by session. Its wallclock figures cover environment CPU execution, **not** model-loading, vLLM token generation, or Kaggle GPU utilization.

## Observations (all public)

| Measure | Random | Visitation novelty |
|---|---:|---:|
| Public game-seed sessions | 75 | 75 |
| Executed actions | 6,000 | 6,000 |
| Sessions completing at least one level | **0** | **6** |
| Total completed levels across sessions | **0** | **6** |
| Distinct public games with any level progress | 0 | **4** |
| Unique visible frame counts, summed | 4,803 | 4,969 |
| Observed identical-frame transitions | 980 | 927 |
| Sum of per-session CPU wallclock (seconds) | 159.304 | 214.643 |

Novelty's six one-level successes were:

- Seed **0**: `r11l` (1 level).
- Seed **1**: `cd82`, `r11l`, `sp80` (one each).
- Seed **2**: `r11l`, `tn36` (one each).

All successful sessions used 80 actions. The game `r11l` showed progress on all three seeds; the other three successful games each appeared on one seed. **This is not a Kaggle score.** The sample is small and exploratory; the policy may perform differently with other public-game seeds, the real Qwen controller, or unseen games. More unique frames or fewer no-ops are *diagnostic*, not proof of goal achievement. Only the explicitly recorded level counter supports a progress claim.

## Implication for EXP-005

This evidence strengthens the justification for EXP-005's model-free novelty *fallback* once Qwen reasoning becomes unproductive: some previously unsolved public games exhibit verified level progress under model-free exploration. **It does not establish that EXP-005 actually invokes the fallback correctly, improves scores, reduces Qwen calls, or stays within Kaggle wallclock limits.** Those require the real-model Kaggle Phase A probe and paired evidence.

Existing EXP-004 Qwen Phase A played 15 actions on each of `ls20`, `vc33`, and `tn36` with 0 levels completed. It is not an equivalent-budget, equivalent-seed comparison to these 80-action, 25-game model-free CPU trials.

## Reproducibility, privacy and release gates

- Local tests: **112 passing** on EXP-006 branch (base 109 + three multi-seed/action-count regression tests).
- Raw per-session public JSON is a local experiment artifact; no private evaluation data, account credentials, local machine information, or personal context is committed.
- Before a release decision, obtain EXP-005 **real Qwen** results with levels per game/seed, actual model calls, planned/heuristic actions, action validation failures, and CPU/GPU wallclock.
- Preserve the RTX PRO 6000, offline internet-disabled, pinned Python image and fixed model/wheelhouse input contract.
- Never spend an official competition submission in a save-and-run probe.
