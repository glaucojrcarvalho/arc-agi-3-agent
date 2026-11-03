# ARC-AGI-3 Agent

**Research engineering for interactive, unfamiliar environments** — an independent exploration of state-aware agents, local multimodal inference, persistent hypotheses, adaptive exploration, and reproducible evaluation for [ARC Prize 2026 — ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3).

> **Portfolio baseline · 3 November 2026.** Engineering integration [#30](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/30) was merged after the competition deadline. The default `agent/my_agent.py` remains the reproducible EXP-000 control. The repository additionally includes **separate opt-in Qwen research policies** and tested EXP-019-lineage engineering. Consolidating code for a portfolio is not a new competition submission. The best completed owner submission on Kaggle is **EXP-019 v1, public score 0.34** (displayed value, not a percentage conversion). This is not a claim of a winning solution, reproducible hidden-set improvement, or final leaderboard result.

[**Engineering case study**](docs/portfolio-case-study.md) · [**Architecture and boundaries**](docs/architecture.md) · [**Experiment evidence**](docs/experiment-evidence.md) · [**Run locally**](docs/setup.md) · [**Post-deadline handoff**](docs/portfolio-handoff-20261103.md) · [**Seed-aware public Qwen validation**](docs/seeded-probe-validation.md)

## The engineering problem

ARC-AGI-3 asks an agent to infer unfamiliar game mechanics from observations and actions, rather than retrieve known answers. This work tests three practical engineering questions:

1. How can the agent retain useful evidence across turns without confusing pixel movement with progress?
2. When should it use expensive model reasoning, execute a validated short plan, or explore cheaply?
3. How do we distinguish a successful offline run, a simulated public-game ablation, a real-Qwen probe, and an **official Kaggle score**?

The distinctive contribution is the **experimental discipline**: bounded state and action ledgers, contract-validated moves, explicit failure analysis, paired seeds, offline packaging, and results labeled by what was actually measured.

## Selected evidence

| Milestone | Evidence | What it establishes |
| --- | --- | --- |
| **EXP-000** | Local control score `0.08612196364871753`; environment and artifact hash in [results.csv](experiments/results.csv) | Reproducible random baseline; **not** a Kaggle leaderboard score |
| **EXP-001** | Completed Kaggle submission; displayed public score **0.00** | Model-driven baseline reached official evaluation, without a scored improvement |
| **EXP-005 v4 → EXP-009** | Matched **real Qwen** probes on four public games: **2 levels each**; 147 → 100 model calls; 700.78 → 502.36 s summed game wallclock | Lower inference cost in this probe; **not** higher level completion or a hidden-set score gain |
| **EXP-019 v1** | Completed official Kaggle submission **57915318**; displayed public score **0.34** | The strongest completed official result recorded by the project owner as of this snapshot |
| **EXP-022 / EXP-023** | Public, paired **fake-model** ablations: EXP-022 regressed in one session; EXP-023 tied all 75 | Useful regression/transport evidence; **not** a Qwen reasoning improvement |

These rows use **different evaluation protocols** and must not be compared as if they were one leaderboard. Source links, sample sizes, negative results, and verification limits are in the [evidence ledger](docs/experiment-evidence.md). The Kaggle result is from authenticated owner submission history; the official hidden evaluation cannot be reproduced using the public-only harness.

## Architecture at a glance

```text
Game observation / legal actions / level count
            |
   Perception + state/transition differencing
            |
   Bounded evidence + provisional beliefs
            |
 Qwen reasoning  <-->  short validated plans
            |                    |
            +--- adaptive exploration / fallback
                         |
                 Legal-action validation
                         |
                    Game action
                         |
                  Observed outcome
```

This diagram describes the **experimental Qwen source in `agent/exp005_agent.py`**, not the active EXP-000 default control. See [architecture](docs/architecture.md) for exact source snapshots and contract boundaries.

## Navigate the source

- **Stable, runnable control:** [`agent/my_agent.py`](agent/my_agent.py) and independent [EXP-000 tests](tests/test_exp000_agent.py).
- **Opt-in research policies:** [EXP-001 direct Qwen](agent/exp001_agent.py) and [EXP-005/019 Qwen line](agent/exp005_agent.py), with shared [state, perception, planning and model modules](src/arc_agent/).
- **EXP-019 research provenance:** [immutable snapshot `6c4224b`](https://github.com/glaucojrcarvalho/arc-agi-3-agent/tree/6c4224b514b6bd3e99ec8bf89c957ffaa092afd3), [historical PR #25](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/25). Consolidated code is **not proof of the exact notebook submitted to Kaggle**.
- **EXP-023 isolated memory hypothesis:** [snapshot at `94932cc`](https://github.com/glaucojrcarvalho/arc-agi-3-agent/tree/94932ccb00ba905519098f223034dca3d49e7728), [archived PR #28](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/28); closed without merge, not promoted or scored with real Qwen.
- **Read-only real-Qwen public probe audit (EXP-010):** [comparator](scripts/compare_real_public_probes.py), [regression tests](tests/test_compare_real_public_probes.py), and [negative-results report](docs/exp010-real-qwen-probe-audit.md), merged in [#16](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/16). This historical comparison checks the same games, model identity and action budgets; **it does not prove matched controller seeds, improved level completion or an official score gain**. Historical EXP-020/021 public experiments are preserved in [archived PR #26](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/26). [PR #32](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/32) independently added seed/milestone validation to the existing comparator, **not** a competitive policy improvement.
- **Research trail:** earlier experiments are linked through the [evidence ledger](docs/experiment-evidence.md). A draft PR is an experiment record, **not evidence of improved score**. See the [opt-in research quickstart](docs/research-quickstart.md).
- **Portfolio branch lifecycle:** [read-only branch ancestry/unique-commit reporter](scripts/report_branch_lifecycle.py), [four regression tests](tests/test_branch_lifecycle_report.py) and [branch retention decision matrix](docs/branch-retention-20261103.md). Reachability is not permission to delete evidence; run on freshly fetched refs, with no automatic branch removal.

## Run the stable baseline locally

Requires Python 3.12. Running the tests does **not** require Kaggle credentials, Qwen weights, GPUs, or downloaded competition environments.

```bash
git clone https://github.com/glaucojrcarvalho/arc-agi-3-agent.git
cd arc-agi-3-agent
python scripts/public_preflight.py --all
python -m compileall -q agent scripts src tests
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/build_standalone_agent.py
```

The standalone build writes ignored `dist/my_agent.py`. For full local-game execution use the **external** official [Kaggle starter](https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter) and follow [setup](docs/setup.md). The default `main` checkout runs EXP-000; checking out a linked experimental commit changes both capabilities and validation obligations.

## Reproducibility and responsible publication

A verified improvement requires a documented hypothesis, a fixed project revision, identical public games/seeds/limits, a compatible model/runtime, error and wallclock reporting, and a **level-completion** metric. Pixel changes, plan count, simulated-model wins, successful `save-and-run`, and official competition submission are different signals.

Source may be published, but **credentials, hidden game data, competition submissions, checkpoints, and raw private traces do not belong in Git**. Use [publication policy](docs/publication-policy.md) and [development workflow](docs/development.md). License for the current `main` source: [Apache-2.0](LICENSE); competition prize eligibility and third-party code licenses require separate review.

## References and attribution

[ARC Prize](https://arcprize.org/) · [ARC-AGI-3 competition and rules](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules) · [Official ARC agent framework](https://github.com/arcprize/ARC-AGI-3-Agents) · [Official Kaggle starter](https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter)

Independent research repository; not affiliated with or endorsed by ARC Prize, Kaggle, or the authors of external reference agents.
