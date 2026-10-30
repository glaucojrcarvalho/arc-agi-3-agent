# EXP-005 — Persistent Hypotheses, Short Plans, and Novelty Escape

Research iteration: 2026-10-30. Not an official scored submission.

## Motivation and evidence

- EXP-001 v15 was the only scored Kaggle submission; displayed public score 0.00.
- EXP-002 v2, EXP-003 v1, and EXP-004 v1 passed real Qwen Phase A
  probes but did not complete levels in 15-action public samples.
- EXP-004's cooldown reduced repeated clicks without increasing level
  progress; raw pixel changes are not goal progress.
- A model-free local screen ran all 25 official public games for up to
  80 actions at seed zero. Deterministic random and salient-click
  policies each completed zero levels. State/action novelty completed
  one level in one public game (r11l). This is a single-seed result,
  not a statistical estimate or Kaggle score.

## Public research underpinning

- Interactive goal inference and adaptation:
  https://arcprize.org/blog/arc-agi-3-launch
- Maintaining model reasoning and compacting history improved public
  ARC-AGI-3 scores for a different model and evaluation harness.
  Do not transfer those measured gains directly to Qwen:
  https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/
- Kaggle participants report that a full inference call per action can
  remain wallclock-bound even with proven no-op filters:
  https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/734369

## Implementation

Keep EXP-004's Qwen3.8-27B-FP8, symbolic spatial grid, salient
click coordinates, transition feedback, eight-action click cooldown,
pinned Python 3.12, and local offline vLLM runtime.

The new mode is opt-in only for EXP-005:

1. Return three optional fields with an action: a concise goal guess,
   a falsifiable hypothesis about dynamics, and up to two follow-up
   keyboard actions.
2. Retain beliefs across turns with 200-character upper limits.
   Explicitly label all beliefs as unverified.
3. Validate any plan against current legal action IDs. Never queue
   coordinate-based actions from an outdated visual observation.
   Clear plans on no-op, level progress, or state change.
4. After 16 actions without level progress, switch to a generic
   low-latency novelty explorer, prioritizing low-visit
   (exact-frame, action) combinations and new click coordinates.
   Refresh Qwen reasoning every 12 actions while stagnant.
5. Never mask model transport failures. Keep game-local bounded memory.
6. Increase response budget from 128 to 320 tokens for EXP-005 only.
   Qwen thinking remains disabled; this is explicit belief memory,
   not hidden chain-of-thought retention or an online API.

No puzzle answers, private game state, or game-specific rules are used.

## Testing and publication boundaries

The local experiment consumes only official public environment_files,
fixed seed zero and 80 actions/game (framework maximum).
Run scripts/evaluate_public_exploration.py against the public
environment_files directory and inspect level counts and unique frames.

The EXP-005 private Kaggle Phase A notebook is independent of official
competition submissions. It boots and validates the real Qwen model,
then runs up to 80 actions on four public games (ls20, vc33, r11l, tn36),
capturing action traces, level progress, model calls, plan actions and
low-latency heuristic actions. Compare against EXP-004 before using
any official submission quota.

Source code can be public. Never commit Kaggle credentials, private
environment files, account secrets, local machine details, personal
conversation context, or raw private evaluation results.
