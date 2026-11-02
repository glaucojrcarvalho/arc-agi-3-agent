# EXP-003 — Lossless Symbol Grid and Salient Click Targets

Research iteration prepared 2026-10-30. This is a public-game
generalization experiment, not an official scored submission.

## Baseline evidence

EXP-001 v15 passed model serving but official submission 57806512
displayed 0.00. EXP-002 v2 completed with Python 3.12 and RTX PRO 6000,
ran 15 real-Qwen actions on each public game ls20 and vc33, and
completed zero levels in both. EXP-002 also detected no exact no-ops.

Relevant public research:
- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/727505
- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/734369
- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/716719

These are ideas, not copied game solutions or claims of private performance.

## Controlled change

Preserve EXP-002 transition history, Qwen3.8-27B FP8, offline
wheelhouse, the pinned Python 3.12 Kaggle image and RTX PRO 6000.

- Encode official color indices 0..15 as lossless hexadecimal
  pixel rows with explicit y-axis labels, layer IDs and dimensions.
- Preserve out-of-range integer color indices via decimal fallback.
- Detect connected same-color regions and propose pixels from
  visibly distinctive regions for click/drag actions.
- Use spatial targets as hints for Qwen and as fallback choices.
- Track bounding boxes and sampled color changes per transition.
- Keep all actions legal, frame-bound, and game-independent.

A visible pixel region is not guaranteed to be interactive.

## Local public-game diagnostics

Observed prompt character-count ratios versus raw arrays:
ls20 0.80, vc33 0.72, tn36 0.79, bp35 0.50.
These are character counts, not token or latency measurements.

Balanced one-action public click diagnostics reset the game with seed
zero for every click and use seven fixed-grid and seven salient-region
coordinates in each of six click-capable games: vc33, tn36, s5i5,
lp85, ft09, r11l. Across 42 clicks per strategy:
- Fixed-grid: 11 clicks changed more than one observed cell.
- Salient regions: 19 clicks changed more than one observed cell.
- Neither strategy completed any level. These are action effects,
  not ARC-AGI-3 scores or a statistical performance claim.
- In individual games, some salient clicks caused very large frame
  changes (including possible layer/dimension expansion), without
  corresponding level progress.

The two strategies are not randomly assigned and these are tiny
public-game samples; different state effects do not establish
superior hidden-game outcomes.

Local diagnostics can be reproduced with the bundled script
scripts/compare_public_click_targets.py against the official
public environment_files directory.

## Validation gate

Run the unit tests; build standalone source from agent/exp003_agent.py;
build scripts/build_kaggle_exp003_notebook.py for the account; save
and run with the RTX PRO 6000 accelerator.

EXP-003 Phase A runs a bounded real-model test on public ls20 and
vc33 and records a per-action trace with click coordinates and visual
changes in exp003-public-probe.json. Phase A is not an official
competition submission. Require actual public-game progress or
another evidence-based decision before spending an official attempt.
