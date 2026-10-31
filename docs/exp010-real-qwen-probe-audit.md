# EXP-010 — public real-Qwen probe audit and inference-budget ablations

Date: 2026-10-31. All data below are from **public ARC-AGI-3 games only**.
There is no hidden/private evaluation, official competition submission,
or leaderboard-score estimate in this work.

## Evidence checkpoint: EXP-005 v4 versus EXP-009

I downloaded the COMPLETE Kaggle output for [EXP-009](https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-009-persistent-reasoning-policy)
and compared the `exp005-public-probe.json` against the COMPLETE
[EXP-005 v4](https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-005-persistent-reasoning-policy).
Both used identical Qwen3.8-27B FP8 model, four matching **public** games,
seed 0 and 80 executed actions per game; `probe_complete=true` for both.

| Public game | Levels 005/009 | Qwen calls 005/009 | Elapsed seconds 005/009 | First level at step 005/009 |
|---|---|---|---|---|
| ls20 | 0/0 | 11/11 | 48.48/47.77 | none/none |
| vc33 | 0/0 | 36/25 | 179.35/131.54 | none/none |
| r11l | 1/1 | 64/39 | 300.40/203.87 | 21/32 |
| tn36 | 1/1 | 36/25 | 172.55/119.18 | 42/36 |
| **Total** | **2/2** | **147/100** | **700.78/502.36** | — |

EXP-009's Qwen calls decreased **31.97%**, and cumulative four-game
wallclock decreased **28.31%**. Level completion was unchanged. But
`r11l`'s first completion was 11 actions later, whereas `tn36`'s was
six actions earlier. These differences may matter for human-relative
action efficiency: **do not report EXP-009 as an official score gain**.
Only four games and one model trajectory were evaluated, without an
independent uncertainty estimate. Earlier EXP-001 score was 0.00, while
EXP-002..004 had shorter 15-action public runs, which are not directly
comparable to this 80-action protocol.

The new `scripts/compare_real_public_probes.py` independently validates
checkpoint completeness, model identity, game inventory, action budget,
trace lengths, and achieved-level consistency before computing calls,
wallclock, completed levels and first progression steps. Its unit tests
reject mismatched runs, duplicates, fake models, incomplete runs, corrupt
traces and invalid metrics. Raw logs and traces stay untracked locally.

## Controlled negative ablations: do not promote yet

Hypothesis: with coordinate actions available, the Qwen refresh interval
could be increased from 8 to 12 or 16 verified nonprogress actions while
preserving EXP-009's 8-action novelty warm-up and keyboard behavior.
Tested isolated standalone variants against EXP-009 with the **same
25 public games × 6 independently seeded novelty controllers × 80 actions**
per variant, fixed **FAKE** model. These 150 trajectories per variant
sample only 25 distinct public games; no Qwen or GPU was used in these
ablations.

| Refresh in coordinate puzzles | Completed levels | Fake-model calls | Local summed CPU wallclock |
|---|---:|---:|---:|
| EXP-009: every 8 (baseline) | **14** | 3,258 | 261.419 s |
| Candidate every 12 | 7 | 2,895 | 253.696 s |
| Candidate every 16 | 8 | 2,678 | 261.246 s |
| Candidate: every 8 until >=32 stagnant moves, then every 16 | 13 | 3,013 | 256.182 s |

The 12-step candidate had **1 improvement, 8 regressions, 141 ties**;
the 16-step candidate had **0 improvements, 6 regressions, 144 ties**.
A third, less aggressive option preserved the EXP-009 eight-step Qwen
refresh for the first 32 verified stagnant moves, then refreshed every
16. It achieved 13 levels (vs 14), with **3 paired improvements,
4 regressions and 143 ties**, despite 7.52% fewer fake calls.
At the game level, one public game improved, two regressed, and 22 tied.
That one-level net loss means it too was rejected. Compared with EXP-009,
**none of the three candidates improved net completed levels**.
Reduced fake-model calls are **not** a valid reason to sacrifice completed
levels. All three variants were tested in isolation on the same public
protocol and **none was pushed to Kaggle**.

The EXP-010 audit PR intentionally **does not change the production
agent's behavior**. Follow-up inference-allocation experiments need a
non-regressive, same-budget multi-seed public signal before using limited
GPU time. Even a non-regressive fake-model signal would require actual
Qwen checkpoint comparisons prior to promotion.

Public background: [OpenAI, 2026-07-29, retained reasoning/compaction](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/)
illustrates why discarding memory is risky; [Explore Before You Solve,
arXiv:2605.25931](https://arxiv.org/abs/2605.25931) warns that public
games permit trivial overfitting. Neither result licenses extrapolation
to this offline Qwen harness or hidden ARC scoring.

## Reproduce the real-Qwen audit

After obtaining existing complete public-only probe JSON files locally:

```bash
PYTHONPATH=src:. python -m unittest discover -s tests -q
python scripts/compare_real_public_probes.py \
  --baseline /path/to/exp005-v4/exp005-public-probe.json \
  --candidate /path/to/exp009/exp005-public-probe.json
```

No competition API submission is invoked by this script; it is strictly
a read-only checkpoint comparator. Do not commit logs, credentials,
private game data, raw trace files, or anything from user conversations.
