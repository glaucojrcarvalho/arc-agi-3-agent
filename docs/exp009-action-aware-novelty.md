# EXP-009 — action-aware early novelty exploration

Date: 2026-10-31. **Public games only.** Experimental branch layered on
EXP-008; no official competition submission or private evaluation.

## Evidence: first complete EXP-005 v4 real-Qwen public probe

Kaggle [EXP-005](https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-005-persistent-reasoning-policy)
v4 returned `KernelWorkerStatus.COMPLETE` (not merely `RUNNING`) after
Qwen3.8-27B FP8 booted on RTX PRO 6000. Its `exp005-public-probe.json`
has `probe_complete: true` and four checkpoints:

| Public game (seed 0) | Actions | Qwen calls | Max levels | Wallclock (s) |
|---|---:|---:|---:|---:|
| ls20 | 80 | 11 | 0 | 48.48 |
| vc33 | 80 | 36 | 0 | 179.35 |
| r11l | 80 | 64 | 1 | 300.40 |
| tn36 | 80 | 36 | 1 | 172.55 |
| **Total** | **320** | **147** | **2** | **700.78** |

Both observed level transitions (`r11l` step 21 and `tn36` step 42,
one-indexed) came **immediately after actions emitted by the model-free
novelty explorer**, not directly from a Qwen-proposed action.
This is trace-based attribution of the final action, **not** proof
that earlier Qwen actions did not contribute or that no Qwen is needed.

`vc33` used 36 Qwen calls with zero level completions and 10 action
redirects; `r11l` used 64 Qwen calls despite completing only one level.
The immediate bottleneck is costly *model-call allocation* when
coordinate/click controls are available. EXP-001 scored zero in its
previous official attempt; EXP-002..004 used only 15-action Qwen samples
without completed levels. Those earlier shorter samples are **not a
like-for-like comparison** to this 80-action probe.

## Hypothesis and implementation

Favor cheap state/action novelty exploration earlier for *complex
coordinate-control actions*, while retaining the longer Qwen planning
warm-up for keyboard-only environments. The trigger uses only current
legal action types and verified **level progression**, not game IDs,
hardcoded solutions, colors, or raw pixel-change counts.

| Setting | EXP-008 | EXP-009 |
|---|---:|---:|
| Enter novelty after stagnant moves | 16 | 8 if complex actions exist, else 16 |
| Refresh model every stagnant moves | 12 | 8 if complex actions exist, else 12 |
| Plans / hypothesis context | bounded | unchanged |
| Proven no-op / click cooldown | active | unchanged |
| Animation representation / settled frame | bounded | unchanged |

The action metadata now records the active novelty threshold and
model-refresh period for auditability. No altered default behavior for
EXP-001..004 is intended.

The motivation for preserving concise, testable long-horizon hypotheses
comes from public harness research, not an assertion that Qwen is
equivalent to GPT-5.6 Sol:
[OpenAI, July 29 2026](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/).

## Protocol, reproducibility and caveats

A same-seed **fake-model** A/B compares EXP-008 and EXP-009:
25 official PUBLIC ARC-AGI-3 games, seeds `0 1 2`, up to
80 legal actions per session. The fixed fake model always returns
`{"action":1,"data":{},"reason":"transport smoke only"}`.
The two standalone builds are made independently from their respective
sources. Use exactly the same installed public environment files.

```bash
PYTHONPATH=src:. python -m unittest discover -s tests -q
python scripts/build_standalone_agent.py \
  --source agent/exp005_agent.py --output dist/exp005_agent.py
python scripts/build_kaggle_exp005_notebook.py \
  --username OWNER \
  --kernel-slug arc-agi-3-exp-009-persistent-reasoning-policy \
  --experiment-label EXP-009 --output-dir dist/kaggle-exp009
PYTHONPATH=src:. python scripts/smoke_exp005_public_offline.py \
  --environments-dir /path/to/public/environment_files \
  --games $(ls -1 /path/to/public/environment_files | sort) \
  --seeds 0 1 2 --max-actions 80 \
  --agent dist/exp005_agent.py
```

**These tests use zero real-model inference and do not measure Kaggle
RHAE/leaderboard score.** Fewer fake calls may save GPU time but could
also remove helpful Qwen decisions. CPU wallclock variance is incidental;
the primary quality outcome is **completed levels**. Real-Qwen validation
must retain the pinned Docker digest, Qwen FP8 model, wheelhouse, private
notebook, no internet, and NVIDIA RTX PRO 6000. Use Kaggle *save-and-run*
only, and verify no other GPU kernel is running first.

## A/B public CPU results — seeds 0, 1, 2

Each variant completed **75 public sessions and exactly 6,000 actions**.
Independent fixed fake-model runs on identical games/seeds:

| Metric | EXP-008 | EXP-009 |
|---|---:|---:|
| Sessions / actions | 75 / 6,000 | 75 / 6,000 |
| Sessions with >=1 level | 3 | **6** |
| Sum max levels completed | 3 | **6** |
| Fake-model calls | 2,061 | **1,659** |
| Model-free actions | 3,903 | 4,308 |
| RESET actions | 36 | 33 |
| Sum session CPU wallclock (s) | 132.862 | 132.232 |

EXP-009 used **402 fewer fake-model calls (19.51% reduction)**,
with three additional completed public levels at the same action budget.
The additional completions were all in `tn36` at seeds 0, 1 and 2;
`r11l` remained one completed level at each seed. Of 75 paired
sessions, **3 improved, 0 regressed and 72 tied** in max levels.
Actual CPU time differed by only 0.63 s (<1%), so no CPU-speedup claim.

This is a useful *offline action-policy signal*, **not** a guaranteed
improvement in Qwen behavior, Kaggle scoring, real GPU latency or unseen
games. The fake model is deliberately constant and cannot simulate
Qwen's learned action selection. A holdout on seeds 3/4/5 and a
real-Qwen Kaggle public probe are separate validation gates.

## Evaluation seed audit (important limitation)

The first two A/B cohorts used environment seeds `0..2` and `3..5`,
but **environment seeds alone are not independent policy trials**.
For all **25** official public environments checked, the serialized
initial observation and action availability hashed identically under
seeds `0..5`. The two complete fake-model A/B cohorts reproduced the
same action/level/call totals exactly, confirming that in those traces,
the agent's novelty RNG (seeded solely by game ID) followed the same
actions. Calling these six observations independent would exaggerate
the strength of the evidence.

A new *evaluation-only* `--vary-policy-seed` option independently
reseeds the fake agent's novelty RNG using a SHA-256 digest of the
public game ID and controller evaluation seed. This changes no
competition agent behavior, game rules, private data or model prompt.
Report randomized-controller outcomes separately; level completion
rather than changed pixels remains the only quality outcome.

The public ARC-AGI-3 benchmark measures *relative human action
efficiency* and incomplete levels receive zero; completing a single
level in 80 actions must not be translated into a Kaggle score.
Reference: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview

## Independent controller RNG audit — 25 public games × 6 trials

The original nominal environment seeds 0..5 did not produce different
initial observations in the 25 public games checked; the deterministic
novelty explorer also seeded itself only by game ID. Re-running unchanged
environment seeds therefore **does not establish six independent policy
samples**. To test whether the policy advantage is sensitive to the
controller's stochastic choices, the *evaluation harness only* now uses
SHA-256 over the public game ID and evaluation seed to reseed the
explorer before each session. Production agent code and real-Qwen
notebooks are unchanged. These are controller-randomness trials on the
same 25 public tasks, **not 150 different games**.

Two standalone agents from independent EXP-008 and EXP-009 source trees
were compared with the **same game/controller-seed pairs**: 25 public
games × controller seeds 0..5 × up to 80 legal actions. The model was
the same fixed deterministic **fake** response in both conditions.
Exact source and JSON protocols are in
[offline smoke](../scripts/smoke_exp005_public_offline.py),
[controller RNG](../scripts/public_policy_rng.py), and
[paired comparison](../scripts/compare_public_controller_seeds.py).
Generated result JSON stays in untracked local temporary storage.

| Public-only metric | EXP-008 | EXP-009 |
|---|---:|---:|
| Controller-randomized sessions | 150 | 150 |
| Actions | 12,000 | 12,000 |
| Sessions with >=1 completed level | 11 | **14** |
| Sum of maximum verified level counts | 11 | **14** |
| Fake-model calls | 4,055 | **3,258** |
| Sum local wallclock (s) | 271.884 | 263.379 |

**Paired outcomes:** EXP-009 improved 6 session pairs, regressed 3,
and tied 141. At the **game level**, 3 of 25 public games had positive
net differences (cd82, lp85, r11l), none had a negative net
difference, and 22 were tied. Other games (sp80, tn36) had both
gains and losses that canceled out. Net gain: 3 completed levels;
the fake-call reduction was **19.65%** (797 fewer calls). The 8.505 s
difference in local CPU-only wallclock is not a measured GPU speedup
and is small relative to normal runtime variability.

This strengthens the *model-free action-policy* signal, but the effect
is narrow: only 9/150 pairs changed their level outcome. It does **not**
establish an ARC-AGI-3 leaderboard/RHAE improvement, independent task
generalization, or better real-Qwen reasoning; the model is fixed and
fake, and the environment initial states do not vary across these
seeds. A completed level at 80 actions may still score poorly under the
action-efficiency metric. Favor real-model levels_completed, Qwen call
count and wallclock over raw pixel changes.

Reproduce the paired comparison after running both standalone versions
of the public-only smoke command with flags
--vary-policy-seed --seeds 0 1 2 3 4 5 and identical games/action budgets:

    python scripts/compare_public_controller_seeds.py       --baseline /tmp/exp008-public-controller.json       --candidate /tmp/exp009-public-controller.json

The CI suite contains 134 tests after isolating the evaluation seed
helper from the ARC runtime, which is intentionally absent from the
GitHub unit-test runner. **Real-model EXP-009 Kaggle kernel remains a
separate validation gate**; do not promote this policy on fake-model
data alone.

## Outstanding release gates

- [x] Complete EXP-005 v4 public real-model probe and inspect checkpoint.
- [x] Implement action-aware policy in an isolated EXP-009 branch.
- [x] Unit/integration regression tests; syntax/metadata preflight.
- [x] Complete same-seed 25-game × three-seed A/B (3 → 6 levels).
- [x] Validate on additional *environment* seeds 3, 4, 5
  (same totals, **not independent stochastic tests**).
- [x] Compare EXP-008/009 on six independently randomized controller
  RNG seeds; 11 to 14 public levels, 6 paired wins/3 losses, 19.65% fewer
  fake-model calls (NOT a Qwen or RHAE score).
- [x] Check all known Kaggle GPU notebooks: EXP-000..005 were COMPLETE
  before the private EXP-009 save-and-run was initiated.
- [x] Initiate the private offline EXP-009 Kaggle notebook with
  **save-and-run** (not a competition submission). Kaggle derived the
  actual URL slug from the title despite initially mismatched metadata;
  this builder now rejects mismatches before subsequent pushes.
  Notebook: https://www.kaggle.com/code/glaucojrcarvalho/arc-agi-3-exp-009-persistent-reasoning-policy .
- [ ] Record real-model completed levels, Qwen calls, wallclock and
  limitations. Do not claim a leaderboard improvement without a scored
  evaluation. Keep all PRs in draft until review.
