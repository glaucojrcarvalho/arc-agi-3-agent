# Research Plan

This document defines the initial experimental program for the ARC-AGI-3 agent. The plan is intentionally incremental: establish a valid baseline first, then add one capability at a time and measure whether it improves generalization or action efficiency.

## Principles

1. **Baseline before complexity.** Every architectural addition should be compared with a simpler system.
2. **One primary variable per experiment.** Avoid changing model, prompting, memory, and action policy at the same time.
3. **Record failures.** Negative results are useful when they eliminate unproductive directions.
4. **Prefer reproducibility.** Important results should be tied to configuration, code revision, upstream revisions, runtime versions, and the exact evaluated agent artifact.
5. **Optimize for unseen tasks.** Avoid strategies that depend on manually encoding solutions to individual evaluation environments.
6. **Respect the submission environment.** Final approaches must fit the competition's runtime, hardware, offline-execution, licensing, and code-sharing constraints.

## Phase 0 — Environment and submission baseline

Goal: prove the full pipeline works before changing agent behavior.

Deliverables:

- run the official starter locally;
- understand the observation and action interfaces;
- capture exact project, starter, framework, Python, and `arc-agi` versions;
- hash the standalone agent artifact actually evaluated;
- produce a valid competition submission only after the local pipeline is verified;
- record the first baseline score and runtime;
- add a minimal local evaluation workflow.

Candidate experiment:

```text
EXP-000  Reproducible random baseline
```

## Phase 1 — Direct policy baseline

Goal: establish a simple model-driven agent with minimal scaffolding.

Flow:

```text
observation → model reasoning → validated action
```

Questions:

- How well does the model act from the current observation alone?
- Which failures are perception failures versus planning failures?
- How frequently does it repeat ineffective actions?
- How expensive is the context required for acceptable behavior?

Candidate experiments:

```text
EXP-001  Direct model policy
EXP-002  Direct model policy + compact state history
```

## Phase 2 — Transition awareness

Goal: make the agent reason explicitly about how actions change the environment.

Introduce:

- observation differencing;
- action → state-change records;
- compact transition memory;
- repeated-action detection.

Candidate experiments:

```text
EXP-003  Observation diff
EXP-004  Transition memory
EXP-005  Repeated / ineffective action guard
```

Primary hypothesis:

> Explicit transition information can reduce redundant exploration and help the agent infer environment mechanics faster than raw frame history alone.

Transition measurements distinguish an **effect** from **progress**. A transition can change the environment without being beneficial; level-count increases are tracked separately as explicit progress.

## Phase 3 — Hypothesis-driven exploration

Goal: distinguish exploration actions from goal-directed actions.

Possible components:

- explicit hypotheses about environment mechanics;
- confidence or uncertainty attached to hypotheses;
- exploration actions selected for information gain;
- hypothesis confirmation / rejection after observing transitions.

Candidate experiments:

```text
EXP-006  Persistent hypothesis memory
EXP-007  Hypothesis validation loop
EXP-008  Uncertainty-guided exploration
```

Primary hypothesis:

> An agent that tracks what it is trying to learn can use fewer exploratory actions than an agent relying only on free-form reasoning history.

## Phase 4 — Planning and structured representations

Only enter this phase when earlier experiments show a measurable bottleneck that planning or structure can address.

Possible directions:

- object-centric state representation;
- short-horizon action planning;
- explicit world-model summaries;
- reflection after failed plans;
- search over candidate action sequences.

These should not be added merely because they are common agent components. Each addition needs an observed failure mode and an ablation against the simpler system.

## Experiment record

The machine-readable registry lives at `experiments/results.csv`. Each experiment should capture at least:

| Field | Description |
|---|---|
| `id` | Stable identifier such as `EXP-004` |
| `revision` | This repository's Git commit used for evaluation |
| `project_dirty` | Whether uncommitted project changes existed at capture time |
| `starter_revision` | Exact ARC-AGI-3 Kaggle starter revision |
| `framework_revision` | Exact ARC-AGI-3-Agents framework revision |
| `arc_agi_version` | `arc-agi` version from the starter runtime |
| `python_version` | Python version from the starter runtime |
| `agent_sha256` | SHA-256 of the standalone agent artifact actually evaluated |
| `model` | Model / checkpoint |
| `configuration` | Relevant inference and agent parameters |
| `score` | Evaluation result |
| `actions` | Action count or efficiency metric when available |
| `runtime` | Runtime / resource use |
| `notes` | Concise technical observations |

Use `python scripts/capture_environment.py --starter <path>` immediately before an evaluated run and copy the reported identifiers into the experiment record.

## Near-term definition of success

The initial milestone is not a particular leaderboard position. It is a reproducible pipeline that can answer the following questions with evidence:

1. What does the simplest valid agent score?
2. What changes when a capable model is used as a direct policy?
3. Does compact state history help?
4. Does explicit state-transition memory improve performance or action efficiency?
5. Can we identify at least one agent component whose effect survives an ablation test?

Once those questions can be answered reliably, the architecture can expand based on evidence rather than speculation.
