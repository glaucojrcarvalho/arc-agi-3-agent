# EXP-021 — Matched seed-101 real-Qwen ablation (Nov 2, 2026)

**Decision: no observed level-completion improvement.** This is a public-only,
completed Kaggle **save-and-run** diagnostic, not a competitive submission.
The tested hypothesis is singular: adding bounded per-level attempted-action
history to Qwen's prompt (EXP-019 policy) improves completion over EXP-009
without changing control selection. The seed-101 result does **not** support
that hypothesis. Keep the scoring decision separate from code/transport checks.

## Provenance and experimental control

On November 2, 2026, the Kaggle CLI reported both kernels `COMPLETE`:

- EXP-020: `glaucojrcarvalho/arc-agi-3-exp-020-persistent-reasoning-policy`,
  standalone agent source SHA-256 `de11e0aa1ccc411a498f801550302c98b2c8d0a5286d64ac81b8d445f4915a66`
  (**EXP-009 policy without ActionEvidence**).
- EXP-021: `glaucojrcarvalho/arc-agi-3-exp-021-persistent-reasoning-policy`,
  standalone agent source SHA-256 `5a46af43c3c2b9913050245dade4409c780e52daa2fceae19642517432752241`
  (**EXP-019 policy with ActionEvidence**). This matches the exact EXP-019
  notebook's extracted standalone agent source hash.

The source hashes above are of the embedded standalone **agent source**, not
of a whole notebook or weights. A source-level comparison confirms the added
`ActionEvidence` ledger and the corresponding prompt/context/reset/record
wiring. Same four public games, 80 actions/game, Qwen3.8-27B FP8, seeded
controller **101** and environment **0**, with probe completion confirmed.
Official competition submissions were **not** made by these probes.

## Verified results (same paired seed, real Qwen)

| Metric | EXP-020: EXP-009 baseline | EXP-021: EXP-019 candidate |
| --- | ---: | ---: |
| Games / action budget | 4 / 320 | 4 / 320 |
| Verified levels completed | **1** | **1** |
| Qwen calls | 88 | 86 |
| Measured sum wallclock | 426.56 s | 410.58 s |
| First completion, public `r11l` | **action 46** | action 59 |
| Public `ls20`, `tn36`, `vc33` | 0 levels each | 0 levels each |

Calls decreased 2/88 (2.27%); recorded wallclock decreased 15.98 s
(3.75%). The **only** paired first-level milestone was **13 actions later**
under EXP-021, despite unchanged total levels. Four games and one controller
seed cannot establish a reliable change in performance, RHAE or competitive
score. Sum wallclock is not an end-to-end Kaggle scoring runtime.

`python scripts/compare_real_public_probes.py` re-read **all 640 public
per-action records** solely to check authoritative `levels_completed` traces,
seed provenance, game inventories and first-completion action positions. Its
output is the sanitized aggregate
[`experiments/exp021-seed101-qwen-public-aggregate.json`](../experiments/exp021-seed101-qwen-public-aggregate.json).
The mismatched EXP-019 (unseeded) vs EXP-021 (seed 101) comparison was
explicitly **rejected** by the comparator. Raw per-action traces, GPU logs,
model outputs, credentials and generated artifacts were **not** committed.

## Interpretation and next candidate gate

The earlier **unseeded** EXP-019 probe completed 2/4 levels and used 99
Qwen calls / 469.06 seconds. It must **not** be ranked against either
seed-101 probe as a controlled A/B result. An externally reported competitive
EXP-019 v1 score of `0.34` is a user report, not independently established by
this public diagnostic. The EXP-021 result is insufficient to promote it for
competitive submission.

EXP-021 and EXP-020 both failed to complete `ls20`, `tn36`, and `vc33` in
80 actions. A lower model-call count is not a substitute for finishing more
levels or finishing earlier. EXP-022's plan-continuity proposal remains a
**separate unvalidated hypothesis**; neither the current evidence nor a
fake-model regression justifies spending the last competition slot.

Kaggle's ARC-AGI-3 deadline is **2026-11-02 23:59 UTC** (Kyiv **2026-11-03
01:59**). Both CPU and GPU submission notebooks have a **nine-hour maximum**;
a new full nine-hour run begun after 14:59 UTC on Nov 2 cannot finish before
this deadline. This is a scheduling-risk warning, not a measured run-time.
No official submission was made or authorized by this work. User review and
explicit approval of a specific notebook/version are mandatory before any
competitive submission.
