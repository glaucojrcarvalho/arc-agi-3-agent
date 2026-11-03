# ARC-AGI-3 Agent

Experimental agent research for **ARC-AGI-3**, focusing on unfamiliar interactive environments, persistent hypotheses, transition-based feedback, and efficient use of local language-model inference.

This repository contains a reproducible baseline, several independent research policies, evaluation utilities, and a record of both positive and negative experiments. It is an **independent research implementation**, not an official ARC Prize project.

## Research questions

An agent entering an unfamiliar game must infer which actions matter and determine whether an observed change represents meaningful progress.

This project investigates:

- Whether bounded reasoning memory helps an agent form and revise hypotheses about game mechanics.
- How state transitions, action validation, and adaptive exploration affect reliability.
- When a deterministic controller can reduce expensive model calls without reducing task success.
- How to evaluate agent behavior without confusing activity, visual effects, or simulated tests with verified level completion.

## Agent implementations

| Component | Role |
| --- | --- |
| [`agent/my_agent.py`](agent/my_agent.py) | Reproducible, model-free EXP-000 baseline (default) |
| [`agent/exp001_agent.py`](agent/exp001_agent.py) | Direct local-model policy with strict structured-action validation |
| [`agent/exp005_agent.py`](agent/exp005_agent.py) | Experimental Qwen policy with bounded hypotheses, short plans, action feedback, and novelty exploration |
| [`src/arc_agent/`](src/arc_agent/) | Shared perception, state, memory, inference, and action-contract modules |
| [`scripts/`](scripts/) | Reproducible packaging, provenance capture, public-game evaluation, and safety checks |

The default agent is the EXP-000 control. Model-driven policies are **opt-in** and require their own offline runtime and evaluation setup.

## Measured results and limitations

Different evaluation environments answer different questions. The figures below are **not interchangeable scores**.

| Evaluation | Observed result | Interpretation |
| --- | --- | --- |
| EXP-000 local baseline | Aggregate local score **0.08612196364871753** | Recorded with runtime revisions and artifact SHA-256 in [`experiments/results.csv`](experiments/results.csv); not a Kaggle score |
| EXP-001 official Kaggle submission | Public score **0.00** | Baseline submission completed; no hidden-task improvement demonstrated |
| EXP-019 v1 official Kaggle submission | Public score **0.34** | Historical public leaderboard result; not proof that any one code change caused the score |
| EXP-005 v4 vs EXP-009 | **147 → 100** real-Qwen calls, **700.78 → 502.36 s** cumulative game wallclock, **2 → 2** completed levels | Matched four-public-game probe showed greater efficiency, not more solved levels |
| EXP-022 / EXP-023 | Negative regression / unchanged outcomes in public fake-model tests | Not promoted as competitive improvements; fake-model results do not establish Qwen reasoning quality |

Full protocols, source revisions, sample sizes, and caveats are recorded in the [experiment evidence ledger](docs/experiment-evidence.md). A successful unit test, public simulation, real-model probe, notebook execution, and official competition submission are distinct kinds of evidence.

## Architecture

```text
Observation + legal actions + completed-level count
                     |
           State / perception
                     |
      Verified transitions and bounded memory
                     |
        Reasoning / validated short plans
                     |
       Adaptive exploration or safe fallback
                     |
             Action validation
                     |
              Environment step
                     |
           Observe actual outcome
```

Only an authoritative increase in the environment's completed-level count establishes level progress. Pixel changes alone can reflect animation, movement, or reset events.

See [architecture](docs/architecture.md) and the [engineering case study](docs/portfolio-case-study.md) for design decisions and representative failures.

## Reproduce the code checks

**Requirements:** Python 3.12 and Git. No GPU, API key, Kaggle login, or model weights are required to run the unit tests.

```bash
git clone https://github.com/glaucojrcarvalho/arc-agi-3-agent.git
cd arc-agi-3-agent

python scripts/public_preflight.py --all
python -m compileall -q agent scripts src tests
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/build_standalone_agent.py
```

To build an experimental policy explicitly:

```bash
python scripts/build_standalone_agent.py \
  --source agent/exp005_agent.py \
  --output dist/exp005_agent.py
```

These commands only build and test code. They do not run Qwen or submit to Kaggle. For the official starter integration and public-environment probes, follow [local setup](docs/setup.md) and the [research policy quickstart](docs/research-quickstart.md).

## Research documentation

- [Experiment evidence and reproducibility](docs/experiment-evidence.md)
- [Architecture and agent contracts](docs/architecture.md)
- [Research methodology and milestones](docs/research-plan.md)
- [Case study: evidence-driven agent engineering](docs/portfolio-case-study.md)
- [Seed-aware public-model comparison](docs/seeded-probe-validation.md)
- [Development workflow](docs/development.md)
- [Public-source publication policy](docs/publication-policy.md)

Experiment-specific reports in [`docs/`](docs/) explain failed hypotheses, regressions, and fixes. Research PRs and immutable commits preserve additional historical context. Their existence does not imply that every proposed policy was accepted or independently scored.

## Licensing and external resources

Original repository source is distributed under [Apache-2.0](LICENSE). Third-party tools, datasets, model weights, and game environments retain their respective licenses and usage requirements. Competition prize-eligibility rules are separate from permission to publish this source code.

- [ARC Prize](https://arcprize.org/)
- [ARC-AGI-3 competition and rules](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules)
- [Official ARC-AGI-3 agent framework](https://github.com/arcprize/ARC-AGI-3-Agents)
- [Official Kaggle starter](https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter)

The repository does not distribute competition credentials, private game traces, model checkpoints, or generated submission artifacts. It is not affiliated with or endorsed by ARC Prize or Kaggle.
