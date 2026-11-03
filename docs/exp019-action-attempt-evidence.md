# EXP-019 — bounded action-attempt evidence for persistent reasoning

**Status:** experimental prompt-only candidate. Baseline EXP-009 is unchanged.
This public simulated-model ablation is not itself an official competition submission.

## Evidence and bottleneck

Earlier experiments tested state novelty, click cooling, action balancing and
heuristic threshold changes. On actual offline Qwen3.8-27B FP8 public probes
(80 actions in each of the same four games), EXP-005 v4 completed 2 levels
with 147 calls and 700.78 seconds total; EXP-009 completed 2 levels with
100 calls and 502.36 seconds total. EXP-009 is the efficiency reference,
not an established score improvement. Earlier real public logs showed
exact visual frame differences at nearly every step. Therefore:
**pixel movement is not evidence of goal advancement** and exact-frame
no-op detection alone cannot teach the model which control hypotheses were
repeated or already investigated.

Public research suggests preserving useful working memory across turns,
rather than repeatedly losing historical context. Relevant source:
[OpenAI, July 29, 2026](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/).
Its effects on other models/harnesses are not evidence of gains for Qwen.

## Change

A new ActionEvidence module records only **actions actually executed**,
their counts, a short sequence of recent control IDs, and the most frequent
normalized 4×4 click sectors. No screenshots, prior game solutions, raw click
coordinates or persistent traces are retained. The ledger resets on
authoritative levels_completed changes and game restarts. The prompt
explicitly says attempt frequency is **not failure/success**, and that
**only an increase in levels_completed verifies level progress**.

This descriptive evidence is added to the model prompt only; legal actions,
validation, fallback, state fingerprints, exploration, safety rules, Qwen
model, dependencies, GPU and networking defaults are unchanged. It is
bounded and deterministic for replay.

## Public evaluation, deterministic fake model (NOT Qwen)

Both agents were tested against the **same 25 public games**, 3
independent *controller RNG* seeds per game, maximum 80 legal actions per
session, and an identical fake model that always returns the same JSON.
This is a transport and regression test; because the fake model ignores
the prompt, no model-quality improvement is expected. The 75 sessions
are repeated trials on just 25 games, not 75 new tasks.

| Metric | EXP-009 baseline | EXP-019 |
|---|---:|---:|
| Session/action count | 75 / 6,000 | 75 / 6,000 |
| Verified levels completed | 6 | 6 |
| Fake-model calls | 1,616 | 1,616 |
| Sum local wallclock | 129.35 s | 129.53 s |

All 75 paired public sessions tied in levels completed. Summed local
wallclock under concurrent CPU evaluations is noisy and cannot establish
Qwen GPU performance. Neither 6 levels nor fake calls are a leaderboard
score. The baseline remains the default submission candidate until a
real-model public probe demonstrates a robust improvement.

## Validation & next gate

Five new ledger unit tests and an integration prompt test verify bounds,
authoritative progress reset, spatial normalization, payload JSON safety,
and model-prompt propagation. Standalone Kaggle agent built
reproducibly. **140 local tests passed**.

Before any real-model test, check active Kaggle jobs and quota. If permitted,
use Kaggle **save-and-run only**, on a separate private/offline notebook with
RTX PRO 6000, pinned Python 3.12 image, the same FP8 model and wheelhouse.
Review public per-game levels, first-level action, Qwen inference count
and wallclock; do not infer gains from changed pixels. Never submit officially
unless matched real-model evidence supports promotion.

All artifacts here contain code and aggregate results of public games only:
no credentials, personal context, private evaluation, raw action traces or
generated submission files.
