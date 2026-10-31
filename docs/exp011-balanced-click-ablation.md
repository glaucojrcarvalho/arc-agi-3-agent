# EXP-011 — balanced spatial click coverage (rejected ablation)

Date: 2026-10-31. **Official public ARC-AGI-3 games only.** This is a model-free,
local policy test and evaluation reproducibility audit; it is **not** a Kaggle
leaderboard/RHAE measurement and it does **not** access private competition
games. The competition agent remains **byte-for-byte unchanged** from the
EXP-010 parent at commit `7a49bcc0d835300115f97fdaf561585f6b3c021c`.

## Real-model release baseline

The known Kaggle EXP-005 v4 and EXP-009 notebooks are both **COMPLETE**, with
`probe_complete=true`. Both validated the same pinned Qwen3.8-27B FP8 model,
four public games at 80 actions/game (320 actions total), and offline RTX PRO
6000 settings:

| Public-only measure | EXP-005 v4 | EXP-009 |
|---|---:|---:|
| Completed levels | 2 | 2 |
| Real Qwen inference calls | 147 | 100 |
| Aggregate game wallclock | 700.78 s | 502.36 s |
| First level in r11l | action 21 | action 32 |
| First level in tn36 | action 42 | action 36 |

Thus EXP-009 saved 31.97% of model calls and 28.31% wallclock without a
demonstrated scoring gain. EXP-001 had an earlier 0.00 official score;
EXP-002..004 short probes completed no levels. Their 15-action budgets are not
comparable to the 80-action EXP-005/009 probes.

Public notebooks:
- https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-005-persistent-reasoning-policy
- https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-009-persistent-reasoning-policy

## Hypothesis and local-only implementation

The existing novelty explorer avoids the most recent 12 click points, but
randomizes the order of salient candidate pixels each turn. EXP-011 tested a
bounded, globally balanced *candidate-coordinate* count (per action/coordinate)
for steering exploration toward less frequently tried points, with a 20%
random escape probability. It clears on level progress, retains no more than
512 click observations, and never uses game IDs as a puzzle-solving rule,
level layouts, private datasets, or hardcoded solutions. It does **not**
interpret raw pixel change as a completed level.

In a synthetic 8×8 candidate field, after 300 selections under a fixed RNG:
the original policy covered 63 distinct coordinates with max frequency 14;
the balanced variant covered 64 distinct coordinates with max frequency 6.
This verifies more uniform spatial coverage, **not improved game performance**.

Implementation is isolated under `experiments/exp011_balanced_click_explorer.py`.
Generate the exact tested variant with
`python scripts/build_exp011_variant.py --output dist/exp011_candidate.py`,
which creates a temporary replacement support package and leaves
`agent/exp005_agent.py` and `src/arc_agent/novelty_explorer.py` unchanged.
The builder reproduced the original candidate byte-for-byte (SHA-256 below).
Do not promote it to the Kaggle agent: the public A/B rejects the hypothesis.

## Paired full-ID public evaluation (legacy raw-ID controller RNG)

25 public environments × 6 controller seeds (0..5) × 80 actions/policy,
with exactly the same game/seed keys and deterministic **fake model**.
The baseline and candidate each executed 12,000 actions (24,000 combined).
These particular runs passed full `xxxx-hhhhhhhh` public game IDs to the
legacy evaluation-only RNG function, *before* the alias canonicalization
fix described below.

| Local measure | EXP-010 baseline | EXP-011 balanced |
|---|---:|---:|
| Sessions | 150 | 150 |
| Total completed public levels | **9** | 6 |
| Sessions with any completed level | **9** | 6 |
| Fake-model calls | 3,251 | 3,236 |
| Sum of CPU session wallclocks | 260.714 s | 256.665 s |
| Actions | 12,000 | 12,000 |

Paired: **4 improved, 7 regressed, 139 tied** game-seed sessions; 2 of 25
public games had a net gain, 2 a net regression, and 21 no net change.
There is a three-level loss despite 0.46% fewer fake calls; the wallclock
difference is small and may contain CPU noise. A more evenly distributed click
pattern was not a useful proxy for completed levels. **Candidate rejected.**
Only sanitized aggregates (no action traces) are committed in
`experiments/exp011-local-paired-summary.json`.

Artifact checksums from the completed local evaluation:
- EXP-010 standalone baseline SHA-256:
  `b7708cd1f0de0539e93f4263998b25c527dce74870b612d1e61e9854ff87ae43`
- EXP-011 standalone balanced variant SHA-256:
  `2b8e0956fd61f4123df113a2c5271525ce6da67c19c75367a4eb3d43385f3268`

## Evaluation reproducibility correction: short vs full game IDs

The official public environment inventory exposes a four-character slug
(`abcd`) or full `abcd-0123abcd` form. Before this round,
`scripts/public_policy_rng.py` used the **literal input game string** to
derive the randomized-controller seed. Supplying the exact same game and
evaluation seed under those two names therefore changed agent behavior.
This explains why EXP-010's earlier 14/150 completed-level count, measured
with short slugs, must **not** be compared numerically to the full-ID
9/150 local baseline above. Neither is an official score.

The evaluation-only seed derivation now normalizes a valid full public ID to
its four-character slug before hashing, while preserving the historical
short-slug seed values and leaving the deployed competition policy unchanged.
The new regression test checks six seeds; an actual public offline smoke
confirmed matching levels, model calls, and actions for the short/full spelling
of a public game at seeds 0/1/2 for 50 actions each (3/3 paired comparisons).

### Alias-normalized follow-up

25 public short slugs × 3 independently seeded controllers (0, 1, 2) ×
80 actions, **6,000 actions per policy** (12,000 combined), now using the
canonicalized evaluation-only RNG:

| Local measure | EXP-010 baseline | EXP-011 balanced |
|---|---:|---:|
| Total completed public levels | **6** | 3 |
| Sessions with any completed level | **6/75** | 3/75 |
| Fake-model calls | **1,616** | 1,625 |
| Sum of CPU session wallclocks | 128.344 s | 127.386 s |
| Actions | 6,000 | 6,000 |

Paired: **1 improvement, 4 regressions, 70 ties**; no public game with a
net positive change, one net negative, 24 unchanged. Model calls rose 0.56%;
the small difference in CPU time is not reliable evidence of an improvement.
This is an independent naming/seed-protocol robustness check and **again
rejects** balanced clicks. Sanitized aggregates:
`experiments/exp011-canonical-paired-summary.json`.

The two controlled local A/B comparisons executed **36,000 actions total**
across repeated runs of the same 25 public environments, not 36,000 unique
games. Both used the deterministic fake model, not actual Qwen. These
repetitions are controller RNG trials; results do not estimate private
generalization or an official Kaggle score.

## Decision and provenance

The parent EXP-010 work was reviewed together with PR #10 and EXP-001..004.
Research on memory retention/compaction and the October 2026 human
think-aloud study supports hypothesis tracking, feedback and exploration,
but **neither is evidence that this specific balanced-click heuristic wins**:
- https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/
- https://arxiv.org/abs/2610.34523

The ablation was rejected on **actual public level completions**, not
synthetic click coverage, fake-model call reductions, or visual pixel changes.
No new GPU kernel was launched, because the candidate regressed locally and
the Kaggle CLI still cannot reveal the remaining GPU-hour allowance.
No concurrent GPU job was initiated; both known EXP-005 and EXP-009 notebooks
were COMPLETE at review. No official submission was performed.

All public outputs in this PR are aggregated and source-only. No credentials,
private evaluation data, raw Qwen traces, hidden game results, account details,
or personal conversation content were published.
