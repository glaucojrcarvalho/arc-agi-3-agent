# Case study: evidence-driven interactive agent engineering

**Role:** independent end-to-end research engineering, from agent contracts and experiment design to offline notebook packaging and failure analysis.

**Benchmark:** [ARC Prize 2026, ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3), which evaluates adaptation to previously unseen interactive games. The emphasis here is on the **engineering process**, not a claimed competition win.

## Problem and constraints

An agent enters games with no task-specific instructions, receives visual observations and legal actions, and must discover useful mechanics within action and runtime budgets. Generic model responses are expensive, may contain invalid commands, and may mistake animations for meaningful progress. Kaggle evaluation is offline, limited to a notebook and bounded compute. Realistic evaluation also requires keeping **public games separate from hidden scoring**.

The initial `main` branch intentionally keeps a reproducible random control, rather than replacing it with every experimental heuristic.

## The approach

1. **Establish a control and provenance.** EXP-000 stores exact source, upstream starter/framework revisions, runtime version, and built artifact hash in [results.csv](../experiments/results.csv).
2. **Build a contract-checked model loop.** Qwen-based experiments validate structured actions, legal action IDs and coordinate bounds. Offline notebook packaging is a separate operation from publishing source.
3. **Make observation accountable.** State fingerprints, after-action diffs and transition summaries isolate proven no-ops. Only authoritative level increases count as progress.
4. **Introduce bounded reasoning and exploration.** The agent retains provisional hypotheses and small validated plans; a generic novelty policy reduces expensive inference during stagnation.
5. **Test ideas independently.** Paired public-game ablations use explicit seeds and action budgets. Regressions, equal outcomes and fake-model limitations are documented rather than silently discarded.

## What the evidence actually shows

In one **real Qwen3.8-27B FP8** public four-game comparison, EXP-005 v4 and EXP-009 each completed two levels in 80 actions per game. Model calls fell **147 → 100**, while summed per-game wallclock fell **700.78 → 502.36 seconds**. That is a meaningful efficiency observation within this protocol, **not** evidence of higher accuracy or generalization.

Two official submissions completed. EXP-001 displayed public **0.00**; EXP-019 v1 displayed **0.34** in the owner's authenticated Kaggle history on 2 November 2026. The result is real, but neither a reproducible hidden-score test nor a proof that EXP-019's prompt ledger caused the change.

The experiment log also contains a **negative** result: EXP-022 produced one regression in 75 public paired fake-model sessions and was rejected. EXP-023, an isolated attempt to retain verified completion evidence across levels, tied all 75 fake-model pairs and was *not* promoted, because the fake model ignores its context. See the [evidence ledger](experiment-evidence.md) for exact protocol boundaries.

## Representative engineering problems solved

- **Probe contract mismatch:** a test stand-in omitted `game_id`; initialization was fixed and guarded ([PR #11](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/11)).
- **Reset contract mismatch:** an unexpected reset action field failed a public probe; repair was verified separately from score claims ([PR #13](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/13)).
- **Prompt overflow:** unbounded animation serialization overwhelmed inference context; observation summaries were bounded ([PR #14](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/14)).
- **False progress signals:** animated pixels kept changing even when levels did not advance; level-count evidence and after-action ledgers provide a stricter measure ([PR #25](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/25)).
- **Overfitting risk:** trial seeds and fake-model policies are labeled explicitly. New hypotheses require real-model tests before being called improvements.

## Lessons and next steps

**What worked:** strict contract checks, observable progress criteria, reproducible public experiments and model-call efficiency. **What remains unresolved:** robust level-solving, object-level perception, persistent causal mechanism transfer, feedback from game-over/undo and reproducible end-to-end scoring provenance. These are research directions, **not completed features**.

The reusable outcome for a software-engineering portfolio is an example of the full cycle: diagnose a production-like failure, isolate a hypothesis, define an observable metric, write regression tests, retain negative evidence, and make the release boundary explicit.

[Architecture](architecture.md) · [Evidence ledger](experiment-evidence.md) · [Research PR #25](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/25) · [Unpromoted EXP-023](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/28)
