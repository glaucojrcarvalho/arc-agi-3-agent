# Model Baseline Plan

This document defines the intended first model-driven ARC-AGI-3 experiment. It is a planning artifact, not a claim that the configuration has already been evaluated.

## Objective

`EXP-001` should answer one narrow question:

> How much performance does a capable local model provide when it selects actions directly from the current environment state, before adding persistent memory, transition heuristics, or planning?

Keeping this baseline small gives later experiments a useful control.

## Current candidate

As of 2026-09-18, the leading practical candidate for the first model baseline is a publicly available **Qwen3.8 27B FP8** checkpoint running locally on Kaggle's ARC-AGI-3 RTX Pro 6000 environment.

Reasons for treating it as the initial candidate:

- recent public ARC-AGI-3 notebooks use Qwen3.8 27B FP8 successfully;
- a recent public notebook reports a successful runtime of roughly 2 hours 20 minutes on RTX Pro 6000, below the competition's 9-hour GPU limit;
- public Duck-derived notebooks using the model provide a useful external reference point;
- the competition explicitly permits freely and publicly available pretrained models, while evaluation runs without internet access;
- the official `Qwen/Qwen3.8-27B` model repository is Apache-2.0 licensed and exposes image-text-to-text inference, leaving both textual-grid and image observations available for later controlled experiments.

The official full-precision model is large, so the initial Kaggle candidate is an FP8 packaging suitable for the available accelerator rather than an assumption that the full checkpoint should be loaded directly.

This does **not** make the model a fixed dependency. We will only adopt it after confirming that the exact public checkpoint, inference stack, model license, and Kaggle attachment workflow are reproducible.

## EXP-001 constraints

The first model experiment should intentionally exclude:

- persistent transition memory;
- explicit world models;
- game-specific rules;
- manually encoded solutions;
- long-horizon search;
- reflection loops;
- RAG or external retrieval;
- online APIs.

Target flow:

```text
current observation
        ↓
compact model input
        ↓
local model inference
        ↓
structured action proposal
        ↓
action validation
        ↓
ARC environment
```

The action validator is infrastructure, not additional reasoning. It should reject malformed or unavailable actions and provide a deterministic fallback.

## Input representation

Start with the smallest representation that preserves the environment state sufficiently for the model:

1. current raw grid / textual representation;
2. current game state and level progress;
3. currently available actions;
4. coordinate bounds for complex actions.

Image rendering, segmentation tools, state history, and observation diffs should be separate experiments rather than silently included in `EXP-001`.

Because the candidate model is multimodal, image observations can be tested later as an explicit ablation rather than being mixed into the first model baseline.

## Output contract

The model should emit a small structured object conceptually equivalent to:

```json
{
  "action": 1,
  "data": {},
  "reason": "short explanation"
}
```

For complex coordinate actions, `data` may contain `x` and `y` values. The runtime must validate the proposal against the environment's available actions and coordinate bounds before execution.

`src/arc_agent/actions.py` implements strict JSON parsing, action availability checks, coordinate validation, and a deterministic fallback primitive independently from the model runtime.

## Submission packaging

The official starter injects only one Python agent file into its generated notebook. Any EXP-001 implementation that imports `src/arc_agent/` must therefore be built through:

```bash
python scripts/build_standalone_agent.py
```

The resulting `dist/my_agent.py` is the file that should be copied into the external starter. This packaging step is part of reproducibility and must be validated before an experiment is submitted.

## Metrics

In addition to the competition score, record where available:

- total runtime;
- number of actions;
- invalid model outputs;
- validation fallbacks;
- repeated actions;
- no-op transitions;
- level completions.

These measurements will help distinguish model capability from harness quality.

## External references

- ARC Prize Milestone 1 write-up: https://arcprize.org/blog/arc-prize-2026-milestone-1
- ARC-AGI-3 competition: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3
- ARC-AGI-3 public code page: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/code
- Example Qwen3.8 27B FP8 public notebook: https://www.kaggle.com/code/mikedan7/arc-agi-3-qwen3-8-27b-fp8-submit
- Official Qwen3.8 27B model: https://huggingface.co/Qwen/Qwen3.8-27B

## Promotion gate

Do not replace `agent/my_agent.py` with the model policy until:

1. `EXP-000` has run successfully end-to-end;
2. the selected model loads offline in the Kaggle environment;
3. a minimal inference call completes within the available memory/runtime budget;
4. the exact model source and license are documented;
5. malformed action output is handled deterministically;
6. `scripts/build_standalone_agent.py` produces a standalone agent that imports and runs successfully without the source tree present.

Until those conditions are met, `EXP-000` remains the active submission agent.
