# EXP-022 — Preserve validated plans after stagnation

Status: proposed public-only policy experiment, not validated for a competitive submission.

## Observed issue

EXP-019 forces model-free novelty on most stagnant turns. A fresh Qwen response may supply up to two validated follow-up keyboard actions, but the next novelty turn can immediately abort this plan, before any follow-up executes. The model refresh then has limited opportunity to complete its own strategy.

## Hypothesis

Prioritizing already validated short keyboard plans over scheduled novelty fallback should improve long-horizon action coherence without adding Qwen calls. Reset and no-op interruptions must remain intact; coordinate plans remain disallowed.

## Evidence and guards

EXP-019 public Qwen probe finished two levels out of four 80-action games, with 99 calls; the official v1 submission reported 0.34 public score. Neither establishes the proposed change improves score. Validate with regression tests, paired public games and identical controller seeds; test real Qwen in a separate private/offline save-and-run notebook before considering another official submission. Preserve RTX PRO 6000, pinned Qwen FP8 model and internet off. Do not conflate a provisional submission.parquet with competitive rerun.

Background: [OpenAI's reasoning retention study](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/) and [Tufa Labs Duck Harness](https://tufalabs.ai/research/duck-harness/).

## 2026-11-02: independent public CPU checkpoint — negative scoring evidence

**Do not promote EXP-022 to a final competitive candidate on the evidence below.** The change does increase execution of prevalidated keyboard plans, but the paired deterministic *fake-model* game protocol found one reproducible level regression and no level gains. This is **not** an inference test using Qwen, a Kaggle scoring run, or a measurement of hidden-game / RHAE performance.

### Reproducibility boundary

- Baseline is EXP-019 at commit `6c4224b`; candidate is the plan-priority change in this PR (`43afb66` at audit). Both use the same `src/arc_agent` code, except for the candidate's one-policy difference. The local candidate branch contains only explanatory comment changes relative to the PR patch.
- Official **public** `environment_files` set: **25 games**, environment/controller seeds **0, 1, 2**, **80 actions per session**. Thus **75 paired sessions / 6,000 actions per policy** (12,000 across both). SDK `arc-agi==0.9.8`, `arcengine==0.9.3`, Python 3.12.15, offline mode.
- Public-only `scripts/smoke_exp005_public_offline.py` was copied into a temporary test harness; **only the deterministic FakeModel output was altered** to emit `{"action":1,"data":{},"reason":"controlled planned-action fake model","next_actions":[{"action":2,"data":{}}]}`, with an extra `plan_actions_taken` counter in output. The original tracked script, competition notebook, real Qwen setup and submitted agent were **not changed**. Agent actions not offered by a given game's available-action contract still go through the existing validator/fallback.
- The local evaluation used `--vary-policy-seed` to vary the novelty explorer's RNG independently and ran `scripts/compare_public_controller_seeds.py` against both saved JSON result sets. That strict paired comparison returned **74 session ties, zero improvements, one regression**. These were not 75 independent games (25 games repeated with three controller seeds).

| Observed public-only metric | EXP-019 baseline | EXP-022 candidate |
| --- | ---: | ---: |
| Games / controller-seed sessions | 25 / 75 | 25 / 75 |
| Action attempts | 6,000 | 6,000 |
| Sessions reaching >=1 completed level | 7 | 6 |
| Sum of maximum `levels_completed` | **7** | **6** |
| Fake model calls | 1,308 | 1,313 |
| Heuristic actions | 4,349 | 4,017 |
| Planned keyboard actions executed | 315 | 639 |
| Resets | 28 | 31 |
| Sum measured CPU wallclock | 128.548 s | 127.187 s |

The only level regression was public game **`sp80`, seed 0**: baseline completed one level with 12 planned actions; candidate completed zero with 20 planned actions. Repeating that exact pair reproduced all action-count, reset, fake-model-call, heuristic and planned-action aggregate metrics for the affected session (**1 vs 0 levels**). The extra plan continuity is real; an improvement in outcomes is **not**.

### Source and safety verification

The PR's exact remote HEAD `43afb66` was independently checked out to a separate detached worktree; **141 Python unit tests passed**, `scripts/public_preflight.py --all` was clean for 81 tracked files. A private/offline EXP-022 Kaggle notebook was also **built locally**, with the existing pinned model source and public probe embedded. It was **not pushed, save-and-run, or submitted** because there is no positive scoring evidence; no Kaggle GPU quota or official submissions were consumed in this experiment. The Kaggle API confirmed the already scored EXP-019 official v1 public score of **0.34** on 2026-11-02, but that is a different run and cannot be attributed to EXP-022.

### Decision

Keep this PR as a **draft research artifact**. Do not fold the plan-continuity change into the official candidate. A real-Qwen paired test could still be informative, but must be explicitly labeled as a *new experiment*, preserve model/seed parity, and complete before any competitive promotion; do not consume a submission slot merely because a notebook builds. Further research on verified cross-level mechanics, game-over and UNDO belongs in a separately scoped hypothesis, **not** piled into this draft PR. Kaggle's [official timeline](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3) fixes the final deadline at 2026-11-02 23:59 UTC, and [Kaggle's announced cutoff policy](https://www.kaggle.com/product-announcements/744617) requires scoring to **finish** before that deadline.
