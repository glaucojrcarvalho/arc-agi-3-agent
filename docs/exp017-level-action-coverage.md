# EXP-017 — Global versus short-window action coverage: both regress

Date: 2026-11-01. **Public ARC-AGI-3 environments only**. This is not a
Kaggle competition submission, RHAE estimate, or Qwen inference benchmark.

## Verified starting evidence

PR #10 (EXP-005) added persistent hypotheses and model-free exploration after
stagnation. EXP-001 had an earlier official score of 0.00; the short
EXP-002–004 Qwen public probes solved no levels. They are not directly
comparable to later 80-action public-game tests. The Kaggle CLI reports
EXP-005 v4 and EXP-009 save-and-run probes as COMPLETE. For matching four
public games, 80 actions each, EXP-005 v4 and EXP-009 each solved **two
levels**, while EXP-009 used **100 vs 147 real Qwen calls** and **502.36
vs 700.78 seconds** of summed wallclock. First-level action indexes shifted
in opposite directions (r11l 21→32, tn36 42→36), so no score gain is proven.

EXP-016 tested coarse spatial keys and lost three levels in its independent
controller-seed holdout. A five-game key audit had 359 distinct exact states
in 400 observations, but only 33 coarse 4×4 keys. That is a strong reason
*not* to assume either exact state uniqueness or heavy abstraction
produces a good exploration policy.

A public OpenAI harness study emphasizes persistent, compact game history
[How enabling two settings tripled ARC-AGI-3 scores, July 29 2026](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/).
Those results use a different model/harness and do not establish that any
particular Qwen exploration heuristic will improve here.

## Hypothesis and isolation

The EXP-009 novelty explorer ranks actions by count per exact settled-frame
fingerprint. On a nearly always-new fingerprint it effectively chooses among
ties. We therefore tested a **separate exploration key** for
model-free action-ID balancing, without replacing the exact fingerprint
used for transition feedback, no-op validation, progress events, or prompt
construction.

- **Level coverage:** one bookkeeping key per observed level, balancing
  legal action IDs across the current level.
- **12-action window coverage:** one key per level and twelve observed
  transitions, retaining short-range movement flexibility.

Both are generated into isolated standalone variants; the competition
agent, persistent Qwen memory/prompt, GPU/runtime/model pins, and production
notebook remain unchanged. Key updates are not interpreted as game progress.
Neither variant has rules keyed to a specific public game or puzzle answer.

## Matched public fake-model experiment

25 public game identities × controller seeds 0, 1, 2 × 80 actions =
**75 game/seed sessions and 6,000 actions per policy**. The deterministic
fake model emits a fixed legal action to test the complete offline
environment/agent transport, *not* semantic game reasoning. Each game/seed
pair is identical across baseline and variants. Different controller seeds
produce policy variation, **not additional independent games**.

| Public-only metric | EXP-009 baseline | Level coverage | 12-action window |
|---|---:|---:|---:|
| Sessions | 75 | 75 | 75 |
| Actions | 6,000 | 6,000 | 6,000 |
| Completed levels | **6** | 5 | 4 |
| Fake-model calls | 1,620 | 1,620 | 1,608 |
| Summed local wallclock | 131.056 s | 130.426 s | 132.043 s |
| Paired improvements / regressions | — | 1 / 2 | 0 / 2 |
| Games with net improvement / regression | — | 0 / 1 | 0 / 2 |

Both policies **lose observed level completions**. A 12-call reduction
in fake-model requests with the window variant is not a Qwen latency
measurement and does not compensate for two fewer solved levels.
Summed local CPU time is a transport metric, not actual RTX PRO 6000
wallclock. The harness did not capture first-completion action indices
in this run, so no per-level action-efficiency improvement is claimed.

Do not conflate changed frame pixels or even greater action-type variety
with verified game progress. Only the environment's actual
`levels_completed` counter is a success signal.

## Reproduce without GPU

From the EXP-017 branch, with the project's documented public
environment installation available:

```bash
PYTHONPATH=src:scripts:. python scripts/build_standalone_agent.py --source agent/exp005_agent.py --output dist/exp017-baseline.py
PYTHONPATH=src:scripts:. python scripts/build_exp017_variant.py --mode level --output dist/exp017-level.py
PYTHONPATH=src:scripts:. python scripts/build_exp017_variant.py --mode window --window 12 --output dist/exp017-window12.py
PYTHONPATH=src:scripts:. python -m unittest discover -s tests -q
```

Run `scripts/smoke_exp005_public_offline.py` for each generated agent on
the **same 25 public game IDs**, with
`--vary-policy-seed --seeds 0 1 2 --max-actions 80`;
use `scripts/compare_public_controller_seeds.py` to verify paired
game/seed inventory. Reported aggregate metrics, source SHA-256 hashes,
and decision are in `experiments/exp017-public-aggregate.json`.
Do not commit game recordings, generated submissions, local logs or
model checkpoint files.

## Decision

**Reject both EXP-017 variants** for submission. The comparison was
negative on the initial paired screening cohort; spending additional
GPU hours or tuning variants to these same public games is not
justified. No new Kaggle notebook was pushed or executed; the EXP-009
real-Qwen candidate remains the least-regressive validated reference,
not a demonstrated leaderboard improvement.

No official competition submission was initiated. Final submission
requires a separate deliberate Monday, November 2 review.
