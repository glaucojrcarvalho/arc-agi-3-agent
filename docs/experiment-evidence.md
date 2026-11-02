# Experiment evidence and result provenance

**Snapshot date:** 2026-11-02. This is a **curated research index**, not a full reproduction of 25 draft PR discussions. The authoritative source for each candidate is its linked PR and immutable commit. The historical `main` [results.csv](../experiments/results.csv) presently records **EXP-000 only**; it must not be treated as an inventory of later scored Kaggle submissions.

## Evidence hierarchy

| Tier | Evidence | Permitted interpretation |
| --- | --- | --- |
| A — official Kaggle | Completed authenticated submission and displayed score | A score for that **specific uploaded version**; not causal proof of which code change helped |
| B — real-model public evaluation | Same public games, limits, model/runtime, and seeds with completed logs | Model behavior, model calls and level completions **on those public games** |
| C — deterministic fake-model public evaluation | Matched public games, seeds, actions and synthetic model behavior | Contract, control-flow and non-regression diagnostics; **not** model-reasoning quality |
| D — unit/offline checks | Tests, syntax, packaging, public-safety scan | Correctness of tested interfaces; not task-solving ability |

Repeated seeds on the same 25 public games are **not 75 independent games**. Timing totals across parallel CPU processes are not comparable to GPU notebook wallclock.

## Selected experiments

| Experiment | Status at snapshot | Protocol and actual measured result | Primary source |
| --- | --- | --- | --- |
| EXP-000 | Control on `main` | Local full baseline: score **0.08612196364871753**; exact revision, runtime and SHA-256 in CSV; **not official Kaggle** | [results.csv](../experiments/results.csv) |
| EXP-001 | Official completed | Kaggle displayed **0.00**; model-driven baseline, not successful hidden scoring | [PR #3](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/3) |
| EXP-005 v4 | Real Qwen public probe | Four public games × 80 actions; **2 levels**, **147 Qwen calls**, **700.78 s** summed game wallclock | [PR #15 comparison](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/15) |
| EXP-009 | Real Qwen public probe | Same four games, model and action budget; **2 levels**, **100 Qwen calls**, **502.36 s** summed game wallclock | [PR #15](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/15) |
| EXP-019 | Official completed + separate fake test | Kaggle submission **57915318** displayed public **0.34**. Separately, fake-model public paired test: 25 games × 3 seeds × 80 actions, baseline and candidate **6 levels / 6,000 actions** each | [PR #25](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/25), [public aggregate](https://github.com/glaucojrcarvalho/arc-agi-3-agent/blob/6c4224b514b6bd3e99ec8bf89c957ffaa092afd3/experiments/exp019-public-aggregate.json) |
| EXP-022 | Rejected; not promoted | Different deterministic fake-model protocol: **7 → 6** level completions; **74 ties, 1 regression** across 75 paired public sessions; no real-Qwen proof | [closed PR #27](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/27) |
| EXP-023 | Unvalidated hypothesis; not submitted | Deterministic fake-model public paired test: **6 vs 6** levels, **75/75 ties**, 1,616 calls per policy; **no Qwen real A/B** | [PR #28](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/28), [experiment report](https://github.com/glaucojrcarvalho/arc-agi-3-agent/blob/94932ccb00ba905519098f223034dca3d49e7728/docs/exp023-observed-completion-evidence.md) |

The two synthetic probe protocols differ (including fake-model behavior). Do **not** compare the 7 in EXP-022 directly with the 6 in EXP-023 as an unexplained fall in the underlying agent.

## What we can conclude

- The real-Qwen EXP-009 public probe reduced model calls and elapsed game time relative to EXP-005 v4 **without adding completed levels** on the matched four games.
- The EXP-019 score of **0.34** is the strongest completed owner Kaggle result recorded by this project as of the snapshot; it is **not a paired hidden-set causal comparison** and its exact submitted notebook hash is not established by the `main` CSV.
- EXP-022 provides a concrete negative test. EXP-023 provides non-regression only under a fake model that ignores its new prompt.
- No evidence establishes human-level performance, reliable unseen-game generalization, or a statistically significant gain from the pending memory change.

## Reproduce the public checks

A fresh `main` checkout reproduces the baseline code/tests, **not** the EXP-019 research snapshot or its Kaggle notebook:

```bash
python scripts/public_preflight.py --all
python -m compileall -q agent scripts src tests
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/build_standalone_agent.py
```

To reproduce a specific experimental probe, check out the **exact linked commit**, obtain the permitted **public ARC game environments** separately, match the recorded policy RNG seeds and per-game budget, and use that experiment's documented command. Fake-model results do not require Qwen. Real-Qwen comparison requires the relevant offline model, serving runtime and GPU resources. Official Kaggle scoring cannot be reconstructed from these public games.

For evaluated baseline provenance:

```bash
python scripts/capture_environment.py --starter ../ARC-AGI-3-Kaggle-Starter
```

## Reporting contract for future experiments

Record the **single change being tested**, parent SHA, standalone artifact SHA-256, upstream revisions, evaluation type, public game set, controller/environment seeds, policy/model version, action limit, completion counts, first-completion actions, legal/invalid actions, resets, model calls, errors and timeouts, total elapsed runtime, paired regressions, and limitations.

A completed notebook `save-and-run`, a local smoke test, a Kaggle submission, and a scored Kaggle submission are **four different states**. Never infer one from another. No secrets, account credentials, raw hidden traces, or model weight files should enter this repository.
