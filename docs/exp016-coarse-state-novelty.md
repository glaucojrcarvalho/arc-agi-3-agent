# EXP-016 — Coarse-state novelty: positive screen, failed controller-seed holdout

Research date: 2026-11-01. Public ARC-AGI-3 games only. This is **not**
a competition submission, RHAE calculation or real-Qwen experiment.

## Evidence and hypothesis

The earlier EXP-001 official attempt displayed 0.00. The short real-Qwen
EXP-002–004 public probes did not complete levels. EXP-005 (#10)
introduced retained, explicitly unverified hypotheses and bounded action
plans. Its successful v4 public probe and the later EXP-009 Qwen probe
both completed two levels in the same four public games and 320 actions.
EXP-005 used 147 model calls / 700.78 s; EXP-009 used 100 / 502.36 s.
First-level action indices changed from 21 to 32 in r11l and from 42
to 36 in tn36; therefore a score improvement is **not** established.

Across these saved real-Qwen traces there were zero consecutive exact
settled-frame no-ops. Exact SHA-256 frame identities are appropriate for
strict feedback validation but may be too brittle as exploration-memory
keys when most actions produce visually distinct boards.

The testable hypothesis was that a *separate* coarse palette/foreground
occupancy signature might group similar visual states, allowing the
novelty explorer to balance actions across repeated situations.

Relevant public harness evidence on maintaining compact memory:
[OpenAI, July 29 2026](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/).
Those measured improvements used a different model and infrastructure;
we do not extrapolate them to Qwen or this heuristic.

## Isolation and implementation

Both variants are generated from the unchanged EXP-009 agent. The
generator injects a separate coarse exploration key only into the
model-free novelty explorer's choice/visit bookkeeping. Existing
exact-frame action feedback, no-op checks, level counters, legal actions,
bounded prompt, animation settlement, CUDA/Qwen configuration and
submission agent remain untouched.

The key includes frame shape, most frequent palette value, a quantized
global color histogram and quantized foreground density in either
2×2 or 4×4 spatial regions (quantum 8). It deliberately merges some
different frames, which is both its intended mechanism and its risk.
A changed key or changed pixel is never counted as level progress.

## Primary public-game screen

Twenty-five public game identities × three controller RNG seeds (0–2)
× up to 80 actions, matched across all three policies. Environment
start states may not vary across seeds. A deterministic **FAKE** model
returns a fixed legal action request for transport testing, not
semantic reasoning. All 225 sessions completed 80 actions.

| Metric | EXP-009 baseline | Coarse 2×2 | Coarse 4×4 |
|---|---:|---:|---:|
| Sessions / actions | 75 / 6,000 | 75 / 6,000 | 75 / 6,000 |
| Completed levels | 6 | 7 | **8** |
| Fake-model calls | 1,616 | 1,614 | 1,622 |
| Summed local wallclock (s) | 129.802 | 136.494 | 135.686 |
| Paired gains / regressions | — | 1 / 0 | 2 / 0 |

All apparent gains occurred in public game `sp80`, under different
controller RNG seeds. The 4×4 variant was preselected for a new-seed
holdout. This is not evidence of generalization to independent games.

## Controller-seed holdout — **failure**

The preselected 4×4 variant and unchanged baseline were re-run against
the same 25 public games with three additional controller seeds (3–5).

| Metric | Baseline | 4×4 candidate |
|---|---:|---:|
| Sessions / actions | 75 / 6,000 | 75 / 6,000 |
| Completed levels | **8** | 5 |
| Fake-model calls | 1,642 | 1,611 |
| Summed local wallclock (s) | **129.416** | 135.479 |
| Paired gains / regressions | — | **0 / 3** |

The regressions were two public `cd82` trials and one `sp80`
trial. The reduction of 31 fake-model calls did not compensate for
three fewer completed levels or the increased local wallclock.
The 150 holdout sessions are repeated trials on 25 problems, not 150
independent games.

## Diagnostic: the key was too coarse

In a separate five-public-game diagnostic with 80 baseline fake-model
actions per game, the sum of within-game distinct exact keys was **359**
of 400 observations. The 2×2 key yielded **15** and the 4×4 key **33**
distinct keys, a severe collapse of state distinctions. For example,
`ls20` produced 76 exact state keys but only one 4×4 key; `sp80`
produced 56 exact keys but five 4×4 keys.

An additional *unsupervised diagnostic only*, not a scored ablation,
found that 8×8 regions with quantum 32 still yielded just 98
distinct keys over these same five games. Simply adding a few coarse
bins does not solve the loss of game-relevant state information.
The audit uses only public environment replay and publishes aggregate
counts, not raw action traces or frame data.

## Reproducibility and release decision

Use a public ARC environment installation and Python with the
repository's documented dependencies. The following generates exactly
the evaluated policies without modifying the EXP-009 baseline:

```bash
PYTHONPATH=src:. python scripts/build_standalone_agent.py --source agent/exp005_agent.py --output dist/exp016-baseline.py
PYTHONPATH=src:scripts:. python scripts/build_exp016_variant.py --bins 2 --quantum 8 --output dist/exp016-b2.py
PYTHONPATH=src:scripts:. python scripts/build_exp016_variant.py --bins 4 --quantum 8 --output dist/exp016-b4.py
PYTHONPATH=src:. python -m unittest discover -s tests -q
```

Evaluate each generated source using
`scripts/smoke_exp005_public_offline.py` with all 25 **public** games,
`--vary-policy-seed --seeds 0 1 2 --max-actions 80` for screening and
`--seeds 3 4 5` for holdout. The original comparison utility
`scripts/compare_public_controller_seeds.py` verifies matching
game/seed pairs. Generated standalone SHA-256 digests, sanitized
aggregate summaries and the decision are stored in
`experiments/exp016-public-aggregate.json`.

**Decision: reject both EXP-016 variants as submission candidates.**
The 4×4 candidate was harmful in held-out controller RNG trials.
Do not spend GPU time on this version, do not promote the apparent
screening gain, and retain EXP-009 as the provisional real-Qwen
reference pending an explicit competition submission decision.

The EXP-016 Kaggle notebook was generated *locally* for offline
metadata preflight only; it was **not** pushed, executed or submitted.
It preserves the existing private notebook, no-internet mode, pinned
Python 3.12 image digest, RTX PRO 6000 and Qwen3.8-27B FP8 configuration.
No official Kaggle competition submission was made.
