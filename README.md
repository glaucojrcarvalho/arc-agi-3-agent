# ARC-AGI-3 Agent

Experimental open-source agent research for **ARC-AGI-3**, focused on online adaptation, environment understanding, transition learning, and efficient action selection in previously unseen interactive tasks.

> Status: early research and baseline implementation.

## Goals

This repository explores a small set of questions:

- Can explicit state-transition memory improve adaptation to unseen tasks?
- Can an agent distinguish useful exploration from goal-directed actions?
- How much environment representation should be deterministic versus delegated to a multimodal model?
- Can learned hypotheses reduce unnecessary actions while preserving task success?

## Initial approach

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

Additional components such as planning, reflection, object-centric representations, and explicit world models will only be added when experiments justify them.

## Experiment philosophy

Changes should be evaluated incrementally. Each meaningful experiment should record:

- experiment identifier;
- model and configuration;
- code revision;
- evaluation score;
- action efficiency when available;
- runtime / resource notes;
- concise technical observations.

The objective is to understand *why* a component helps or hurts rather than accumulate agent complexity.

## Repository structure

The repository will evolve toward the following structure as the implementation grows:

```text
src/arc_agent/      Agent implementation
experiments/        Reproducible experiment definitions and results
tests/              Automated tests
scripts/            Local evaluation and utility scripts
docs/               Architecture and research notes
notebooks/           Deliberately published research notebooks
```

Competition datasets, credentials, generated submission artifacts, local recordings, model checkpoints, and other non-source artifacts are intentionally excluded from version control.

## Reproducibility

The project will prefer reproducible configurations and documented experiments over unpublished one-off tuning. Public results should include enough technical context to understand the evaluated approach without exposing credentials or redistributing competition artifacts unnecessarily.

## References

- ARC Prize: https://arcprize.org/
- ARC-AGI-3 Kaggle competition: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3
- Official ARC-AGI-3 Kaggle starter: https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).

## Disclaimer

This is an independent research project and is not affiliated with or endorsed by the ARC Prize Foundation or Kaggle.
