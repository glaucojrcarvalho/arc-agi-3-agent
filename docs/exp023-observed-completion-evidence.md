# EXP-023 — bounded observations of completed levels (2026-11-02)

Status: **isolated hypothesis; not score-qualified, not approved for promotion**.
Parent: EXP-019 source at `6c4224b`; separate from the negative EXP-022
plan-continuity trial (PR #27). The existing official EXP-019 v1 submission
`57915318` remains **COMPLETE, public 0.34**. This experiment was not submitted.

## Hypothesis and exact intervention

A model may reuse limited, **environment-confirmed level completion traces**
on subsequent levels, rather than forgetting all observations when
`levels_completed` increases. This is *not* evidence of causal mechanics.

Added `ObservedProgressMemory` under `src/arc_agent` and injected only its
bounded result into `agent_belief_state.observed_previous_level_progress`.
Each record contains a before/after level count and at most four sanitized
action/outcome summaries. Retain at most three recent completed levels,
discard unverified model claims, free-form strings, and frame payloads.
Only create records for an **observed level increment with matching
`levels_delta`**; mere pixel changes and no-ops never count as completion.
Clear on `GAME_OVER`, `NOT_PLAYED`, and unexpected level rollback.
Do not modify action selection, model configuration, reset actions, or limits.
No third-party implementation was copied.

## Reproducible tests (CPU, deterministic FAKE model only)

- Unit and agent-level tests: **147 passed**; six new module tests and one
  integration test verify evidence gating, bounds, sanitization, prompt
  handoff, game-over reset and rollback. Preflight clean on tracked files.
- Fake-model public A/B: the same **25 public games**, controller/environment
  seeds **0, 1, 2**, **80 actions per session** (75 paired sessions,
  6,000 actions per policy). Baseline = standalone EXP-019; candidate =
  standalone EXP-023. No private game data or GPU needed.
- **Levels:** EXP-019 **6** vs EXP-023 **6** total session maxima;
  sessions with progress **6 vs 6**, improvements **0**, regressions **0**,
  ties **75**; all 25 games net tied.
- **Actions:** 6,000 vs 6,000; **fake-model calls:** 1,616 vs 1,616;
  heuristic actions: 4,356 vs 4,356; resets: 28 vs 28.
- **Summed local CPU wallclock:** **131.233 s vs 135.339 s** (not paired
  GPU wallclock; do not infer throughput advantage).
- **Qwen real calls in this checkpoint: 0**. There is no GPU/vLLM serving
  on the remote host and the competition has no remaining submission quota
  before the deadline. No real-Qwen A/B or hidden RHAE scoring occurred.
- The offline Kaggle notebook was successfully built and Python cells
  checked (IPython magic cells intentionally excluded from `compile`);
  no Kaggle notebook push, save-and-run, or official submission.

Reproduce from a checkout with the offline public environment files and
`arc3-eval-venv` installed:

```bash
export PYTHONPATH=src:scripts:.
python scripts/build_standalone_agent.py --source agent/exp005_agent.py --output dist/exp023_agent.py
python -m unittest discover -s tests
python scripts/smoke_exp005_public_offline.py --environments-dir /path/to/public/environment_files --agent dist/exp023_agent.py --games ar25 bp35 cd82 cn04 dc22 ft09 g50t ka59 lf52 lp85 ls20 m0r0 r11l re86 s5i5 sb26 sc25 sk48 sp80 su15 tn36 tr87 tu93 vc33 wa30 --seeds 0 1 2 --max-actions 80 --vary-policy-seed --output /tmp/exp023.json
python scripts/compare_public_controller_seeds.py --baseline experiments/exp023-baseline-fake-public.json --candidate experiments/exp023-candidate-fake-public.json
```

Machine-readable experiment logs are committed under `experiments/exp023-*`.
The final generated standalone agent SHA-256 is
`86ae5c5f57b7c36d765ec5d1d1ff1f0bb2b9e636d52f36ececceea80fdf3103c`.

## Technical verdict and competition guard

**Non-regression in the FAKE-model public probe, not a demonstrated gain.**
The fake model ignores the new prompt context, so 75/75 ties are expected;
the test checks transport and action-policy invariants, not model reasoning.
Real Qwen responses could improve, regress, slow down or hit context limits.
A meaningful promotion requires paired real-Qwen seeds, first-completion
actions, actions per solved level, errors/timeouts, prompt/token cost and
wallclock, then a full competition-mode validation. None is feasible as a
new official submission before UTC **2026-11-02 23:59**: today's Kaggle
limit is 1 and `numToday=1`; the daily UTC reset comes after closure.
Kaggle requires scoring to finish before that limit. Preserve EXP-019.

High-scoring references are **external results, not ours**: Daniel Franzen's
public milestone notebook reports best **34.30**; Duck/TAAF and rellik13
describe persistent histories/REPL as research directions. Do not import
their code without checking the specific license and dependencies.
Participant reports document substantial scoring variance even for
identical notebooks, so neither a single public run nor an offline
fake-model tie estimates a new Kaggle score.

References:
- https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/27#issuecomment-6586012270
- https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution
- https://github.com/Tufalabs/duck-harness
- https://github.com/LohitSiriki/arc-agi-3-milestone2-solution/blob/main/WRITEUP.md
- https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/738762
- https://www.kaggle.com/product-announcements/744617
