# EXP-004 — Bounded Coordinate Cooldown for Spatial Exploration

Research iteration prepared 2026-10-30. Not an official scored submission.

## Evidence

EXP-003 Kaggle v1 completed with real Qwen3.8-27B FP8.
- Public game ls20: 15 model actions, zero levels completed.
- Public game vc33: 15 clicks, eight unique coordinates, seven
  coordinate repetitions, eight clicks that changed more than one
  cell, five clicks that changed more than eight cells, zero
  levels completed.
- The model repeatedly selected some of the same candidate
  locations after observing large frame changes but no score progress.

This supports evaluating a temporary exploration cooldown. A
frame change is not itself proof of progress.

The approach is informed by publicly documented verified-action
memory and single-step recovery, without copying task solutions:
https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/739938

## Controlled change

Retain EXP-003 model, symbolic pixel grid, connected-component
candidate selection, verified transition history, offline runtime,
and the pinned Python 3.12 RTX PRO 6000 Kaggle environment.

Add an eight-action FIFO coordinate cooldown within a game and level:
- After clicking coordinate (x,y) with a complex action, remember
  the action ID and coordinate for the next eight actions.
- If the model proposes a recently used click and no level
  completion has occurred, redirect to another legal candidate.
- Tell the model which clicks are on temporary cooldown.
- Cooldown is not a proven no-op, nor a permanent blacklist.
- Clear cooldown on level progress and reset.
- If all legal coordinates are cooled, allow reuse rather
  than deadlocking or forcibly resetting.
- Keyboard actions do not participate in coordinate cooldowns.

This policy can suppress repetitions required by certain puzzles,
so it is an experiment rather than a universal improvement claim.
It is bounded, game-independent and reversible.

## Validation protocol

Unit tests prove that a valid click is redirected even if the
frame changed, that non-coordinate actions remain usable, and that
cooldown expires or clears on progress/reset.

Kaggle Phase A will run real Qwen on public ls20, vc33 and tn36,
up to 15 steps each. Each trace captures coordinates, frame-change
counts, agent redirections, and level completions in
exp004-public-probe.json. No hidden competition rerun is triggered.

Before official submission, compare actual progress and action
efficiency with EXP-002 and EXP-003, and inspect whether newly
explored regions help or merely consume more inference time.
