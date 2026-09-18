# ARC-AGI-3 Agent

Experimental open-source agent research for **ARC-AGI-3**, focused on online adaptation, environment understanding, transition learning, and efficient action selection in previously unseen interactive tasks.

> Status: Phase 0 local baseline completed. EXP-000 provides a reproducible control for model-driven and transition-aware experiments; competition submission remains separately gated by the documented public-code requirements.

## Research questions

This repository explores a deliberately small set of questions:

- Can explicit state-transition memory improve adaptation to unseen tasks?
- Can an agent distinguish useful exploration from goal-directed actions?
- How much environment representation should be deterministic versus delegated to a multimodal model?
- Can learned hypotheses reduce unnecessary actions while preserving task success?

## Experimental approach

The first iterations intentionally keep the architecture small:

```text
Observation
    ↓
State / Difference Detection
    ↓
Agent Reasoning
    ↓
Action
    ↓
Transition Memory
    └──────────────→ next observation
```

Planning, reflection, object-centric representations, and explicit world models are only introduced when measured failure modes justify them.

## Current baseline

`agent/my_agent.py` contains `EXP-000`, a reproducible random policy used as the control for the research program. It does not contain game-specific heuristics or a learned policy.

The full local baseline completed successfully with an aggregate score of `0.08612196364871753`. The evaluated artifact hash and exact project/starter/framework/runtime provenance are recorded in `experiments/results.csv`. This is a local baseline result, not a Kaggle leaderboard score.

The next research milestone is `EXP-001`: a direct model policy with minimal scaffolding, evaluated against this control before adding persistent memory or planning.

Reusable state differencing, transition memory, and structured-action validation primitives are implemented under `src/arc_agent/` and covered by unit tests. They are intentionally not enabled in `EXP-000`, preserving a clean control for later ablations.

Transition metrics distinguish **effect** from **progress**. A state-changing action may be effectful without being beneficial; level-count increases are tracked separately as explicit progress.

## Submission packaging

The official ARC-AGI-3 starter packages only `agent/my_agent.py` into its generated notebook. It does not automatically include this repository's `src/arc_agent/` package.

Build the standalone artifact before copying the agent into the starter:

```bash
python scripts/build_standalone_agent.py
```

The generated `dist/my_agent.py` embeds `src/arc_agent/` only when the active agent imports it. For `EXP-000`, the output remains byte-for-byte identical to the source baseline.

See [`docs/setup.md`](docs/setup.md) for the complete workflow.

## Reproducibility

Evaluated experiments record the project revision, exact upstream starter/framework revisions, the **starter runtime's** Python and `arc-agi` versions, whether the project working tree was dirty, and the SHA-256 of the standalone agent artifact actually evaluated.

Capture that provenance immediately before an evaluated run:

```bash
python scripts/capture_environment.py \
  --starter ../ARC-AGI-3-Kaggle-Starter
```

The command fails with incomplete provenance if the starter runtime, framework checkout, or standalone agent artifact cannot be identified. Results are recorded in [`experiments/results.csv`](experiments/results.csv); scores are only added after an actual run.

## Public competition code

Kaggle's competition rules permit public Competition Code, but require code shared publicly during the competition to also be shared on the competition's Kaggle discussion forum or associated notebooks. This repository therefore needs a corresponding ARC-AGI-3 Kaggle disclosure; once posted, that reference will be linked here.

## Development workflow

`main` is the stable research line. Normal implementation happens on short-lived branches and enters through pull requests. Local Git worktrees are recommended when multiple experiments or infrastructure tasks are active in parallel.

See [`docs/development.md`](docs/development.md) for the branch/worktree conventions and PR checklist.

## Repository structure

```text
agent/
└── my_agent.py                 Current EXP-000 agent

src/arc_agent/
├── actions.py                  Structured model-output validation
├── memory.py                   Bounded transition memory
└── state.py                    Frame fingerprints and state differencing

tests/
├── test_actions.py
├── test_agent_contract.py      Active agent behavior against ARC-like stubs
├── test_capture_environment.py Environment provenance validation
├── test_memory.py
├── test_packaging.py           Standalone bundle/import validation
└── test_state.py

experiments/
└── results.csv                 Experiment registry and provenance

docs/
├── development.md              PR/worktree workflow
├── model-baseline.md           Planned EXP-001 model baseline
├── publication-policy.md       Public-repository rules
├── research-plan.md            Incremental research program
└── setup.md                    Local starter integration

scripts/
├── build_standalone_agent.py   One-file Kaggle-compatible packager
├── capture_environment.py      Public-safe experiment provenance capture
└── public_preflight.py         Staged/all-file safety scanner

.github/workflows/
└── ci.yml                      Safety, syntax, and unit-test checks
```

Competition datasets, credentials, generated submission artifacts, standalone build outputs, local recordings, model checkpoints, and other non-source artifacts are intentionally excluded from version control.

Before publishing changes, follow [`docs/publication-policy.md`](docs/publication-policy.md) and run:

```bash
python scripts/public_preflight.py
```

CI additionally scans all tracked files, compiles Python sources, and runs unit tests on every push and pull request.

## Research plan

The planned progression is documented in [`docs/research-plan.md`](docs/research-plan.md):

1. pipeline baseline;
2. direct model policy;
3. transition awareness;
4. hypothesis-driven exploration;
5. structured planning only when supported by measured failure modes.

The current model-baseline candidate and promotion gates are documented separately in [`docs/model-baseline.md`](docs/model-baseline.md).

## References

- ARC Prize: https://arcprize.org/
- ARC-AGI-3 Kaggle competition: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3
- ARC-AGI-3 competition rules: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules
- ARC-AGI-3 agent framework: https://github.com/arcprize/ARC-AGI-3-Agents
- Official ARC-AGI-3 Kaggle starter: https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).

## Disclaimer

This is an independent research project and is not affiliated with or endorsed by the ARC Prize Foundation or Kaggle.
