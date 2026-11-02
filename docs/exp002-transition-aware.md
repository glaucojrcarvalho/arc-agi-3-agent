# EXP-002 — Transition-Aware Qwen Agent

## Evidence and motivation (2026-10-30)

EXP-001 v15 passed a real Qwen/vLLM inference probe on RTX PRO 6000, but
Kaggle submission 57806512 returned a displayed public score of 0.00.
Successful model startup is not evidence that the agent solves levels.
EXP-001 has no action-outcome memory, and its invalid-output fallback
always chooses the numerically smallest available action.

Research sources (ideas, not copied game-specific solutions):

- ARC Prize official starter recommends running public games locally:
  https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter
- Kaggle thread about submissions failing or hanging without visible logs:
  https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/727119
- Kaggle thread on no-op guards, animation frames, and runtime costs:
  https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/734369
- BDR-Pro world-model experiment reports public/private overfitting risk:
  https://github.com/BDR-Pro/arc-prize-2026-arc-agi-3

## Experimental change

Retain Qwen3.8-27B-FP8, vLLM bootstrap, decoder settings and offline
execution from EXP-001. Add bounded per-game transition control:

1. Observe the actual frame and level count after each selected action.
2. Record the recent action, frame changes, state changes and progress.
3. Prove a no-op only if frame fingerprint, level and state are identical
   before and after that exact action.
4. In that exact state, redirect a repeated no-op to another legal action
   or another legal coordinate without an extra model request.
5. Rotate invalid-response fallbacks instead of always selecting ACTION1.
6. Provide up to six observed transitions and current no-ops to the model.

The monitor stores at most six transition summaries and 256 state entries.
It is per-agent/per-game and does not use game IDs or hidden test data.

## Local validation

The official 25 public game environments were downloaded separately from
Kaggle and installed in an isolated Python 3.12 virtual environment.
No user account credentials are part of the source tree.

The offline engine smoke test uses a deterministic dummy model choosing
the lowest legal action. This verifies action legality and feedback logic,
not real Qwen performance or official scoring.

- ls20, 40 actions: EXP-001 used 1 distinct action; EXP-002 used 2
  distinct actions and redirected 8 verified no-ops. No levels completed.
- vc33, 40 actions: both used 1 action type, no levels completed.

A Kaggle save-and-run experiment runs a real Qwen inference probe and then
up to 15 moves each on public ls20 and vc33, writing a public-only
exp002-public-probe.json file to the notebook output. This probe is skipped
during the hidden competition rerun.

## Build and release gates

1. Run full unit tests, including generated notebook compilation.
2. Build standalone agent from agent/exp002_agent.py.
3. Build the new EXP-002 notebook using scripts/build_kaggle_exp002_notebook.py.
4. Push the EXP-002 Kaggle notebook with RTX PRO 6000 accelerator explicitly.
5. Inspect public probe result and runtime logs before considering an
   official scored submission. Do not infer private performance from
   the public sample.

Never commit local paths, credentials, private conversation context, or
unreviewed downloaded artifacts. Keep Phase A and official submission
clearly distinct.

## Runtime compatibility (v1 failure)

EXP-002 Kaggle v1 unexpectedly used Python 3.13 (a newer Kaggle image),
while the offline vLLM wheelhouse expects Python 3.12. The dependency
aiohttp 3.13.5 was unavailable for Python 3.13, and Phase A ended
without loading the model. Version 2 pins the same Python 3.12-compatible
Kaggle container digest used by successful EXP-001 v15, and logs
the interpreter version before installation. No official submission was made.
