# EXP-022 — Preserve validated plans after stagnation

Status: proposed public-only policy experiment, not validated for a competitive submission.

## Observed issue

EXP-019 forces model-free novelty on most stagnant turns. A fresh Qwen response may supply up to two validated follow-up keyboard actions, but the next novelty turn can immediately abort this plan, before any follow-up executes. The model refresh then has limited opportunity to complete its own strategy.

## Hypothesis

Prioritizing already validated short keyboard plans over scheduled novelty fallback should improve long-horizon action coherence without adding Qwen calls. Reset and no-op interruptions must remain intact; coordinate plans remain disallowed.

## Evidence and guards

EXP-019 public Qwen probe finished two levels out of four 80-action games, with 99 calls; the official v1 submission reported 0.34 public score. Neither establishes the proposed change improves score. Validate with regression tests, paired public games and identical controller seeds; test real Qwen in a separate private/offline save-and-run notebook before considering another official submission. Preserve RTX PRO 6000, pinned Qwen FP8 model and internet off. Do not conflate a provisional submission.parquet with competitive rerun.

Background: [OpenAI's reasoning retention study](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/) and [Tufa Labs Duck Harness](https://tufalabs.ai/research/duck-harness/).
