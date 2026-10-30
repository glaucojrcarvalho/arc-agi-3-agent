# Model Baseline Plan

This document defines the first model-driven ARC-AGI-3 experiment.

## Objective

`EXP-001` asks one narrow question:

> How much performance does a capable local model provide when it selects actions directly from the current environment state, before adding persistent memory, transition heuristics, reflection, or planning?

The measured `EXP-000` local random-policy score (`0.08612196364871753`) is the control.

## Selected candidate

As of 2026-09-18, the selected candidate family is **Qwen3.8 27B FP8** served locally on Kaggle's RTX Pro 6000 environment.

Current public ARC-AGI-3 notebooks demonstrate successful Qwen3.8 27B FP8 runs at roughly 2 hours 20 minutes on RTX Pro 6000. The official `Qwen/Qwen3.8-27B` model is Apache-2.0 licensed, supports OpenAI-compatible serving through vLLM/SGLang, and allows thinking mode to be disabled per request.

The exact Kaggle-attached FP8 artifact used for an evaluated run must be recorded with the experiment provenance. A public repack or mirror is not treated as interchangeable until its source/provenance has been checked.

## EXP-001 constraints

The first model experiment intentionally excludes:

- persistent transition memory;
- explicit world models;
- game-specific rules;
- manually encoded solutions;
- long-horizon search;
- reflection loops;
- RAG or external retrieval;
- online model APIs;
- image input.

Target flow:

```text
current observation
        ↓
compact text serialization
        ↓
localhost OpenAI-compatible model server
        ↓
strict JSON action proposal
        ↓
action validation
        ↓
ARC environment
```

Transport failures fail the run rather than silently degrading into a non-model policy. Invalid or unavailable model action proposals use a deterministic legal fallback and increment a fallback counter.

## Runtime contract

The agent expects a local OpenAI-compatible endpoint:

```bash
export ARC_MODEL_NAME="Qwen/Qwen3.8-27B"
export ARC_MODEL_ENDPOINT="http://127.0.0.1:8000/v1/chat/completions"
```

`ARC_MODEL_ENDPOINT` is deliberately restricted to localhost/loopback HTTP. This prevents EXP-001 from accidentally depending on an online inference API.

Optional:

```bash
export ARC_MODEL_TIMEOUT_SECONDS="120"
```

The request is deterministic for this baseline:

- `temperature=0.0`;
- maximum response budget 128 tokens;
- Qwen thinking disabled;
- no preserved thinking;
- one model request per non-reset action.

## Input representation

The model receives only:

1. current raw frame;
2. current game state;
3. completed-level count;
4. currently available action ids;
5. which available actions require coordinates;
6. valid coordinate bounds.

No previous frames or transition records are included.

## Output contract

The model must return exactly one JSON object:

```json
{
  "action": 1,
  "data": {},
  "reason": "short explanation"
}
```

For a complex action, `data` contains integer `x` and `y` values within the supplied bounds.

`src/arc_agent/actions.py` remains the execution gate. Malformed JSON, unavailable actions, or invalid coordinates cannot be executed directly.

## Submission packaging

EXP-001 imports code from `src/arc_agent/`, so the official starter must receive the generated standalone artifact:

```bash
python scripts/build_standalone_agent.py
```

The packaging test executes the generated file in an isolated Python subprocess without the repository source tree on `PYTHONPATH`. This ensures a green test actually proves the embedded package is sufficient.

## Metrics

Record where available:

- aggregate score;
- total runtime;
- number of actions;
- model calls;
- invalid model outputs;
- validation fallbacks;
- level completions.

The primary comparison is EXP-001 versus EXP-000. Later memory/planning experiments should use EXP-001, not the random policy, as their model-policy control.

## External references

- ARC-AGI-3 competition: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3
- ARC-AGI-3 public code page: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/code
- Public Qwen3.8 27B FP8 ARC-AGI-3 notebook: https://www.kaggle.com/code/mikedan7/arc-agi-3-qwen3-8-27b-fp8-submit
- Official Qwen3.8 27B model: https://huggingface.co/Qwen/Qwen3.8-27B

## Promotion gate

Do not mark EXP-001 complete until:

1. the exact FP8 model artifact and provenance are documented;
2. the model loads offline in the Kaggle runtime;
3. a minimal localhost inference call succeeds;
4. the standalone agent runs without access to this repository's source tree;
5. local ARC smoke tests succeed with the model server active;
6. full-run provenance and artifact SHA-256 are captured;
7. the measured result is recorded without mixing in later memory/planning changes.
