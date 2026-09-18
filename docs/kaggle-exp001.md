# EXP-001 Kaggle Deployment

EXP-001 is intentionally not expected to run the 27B FP8 model on a developer laptop. The deployment target is Kaggle's ARC-AGI-3 RTX Pro 6000 runtime.

## Inputs

The generated notebook pins these public Kaggle inputs:

- competition: `arc-prize-2026-arc-agi-3`;
- offline vLLM wheelhouse: `driessmit1/arc3-vllm-h100-wheelhouse-v3`;
- model: `mikedan7/qwen3-8-27b-fp8-official/PyTorch/hf-fp8/1`.

The Kaggle model mirror states that it is an unmodified mirror of `Qwen/Qwen3.8-27B-FP8` pinned to upstream revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`.

Kaggle model inputs are mounted under `/kaggle/input/models`. EXP-001 prefers `/kaggle/input/models/mikedan7/qwen3-8-27b-fp8-official/pytorch/hf-fp8/1` and falls back to guarded discovery within the models mount by locating a unique directory for the pinned model slug that contains a Hugging Face `config.json` and safetensor shards.

## Build

Build the standalone agent first:

```bash
python3 scripts/build_standalone_agent.py
```

Then generate the Kaggle deployment files:

```bash
python3 scripts/build_kaggle_exp001_notebook.py \
  --username YOUR_KAGGLE_USERNAME
```

Generated files are intentionally placed under:

```text
dist/kaggle-exp001/
├── kernel-metadata.json
└── submission.ipynb
```

`dist/` is ignored by Git. Do not commit generated notebook metadata containing an account username.

## Push

Use the Kaggle CLI from the external starter environment so credentials remain outside this repository:

```bash
cd /path/to/ARC-AGI-3-Kaggle-Starter

.venv/bin/kaggle kernels push \
  -p /path/to/arc-agi-3-exp-001/dist/kaggle-exp001
```

This starts Kaggle's save-and-run phase. It does not itself spend a competition submission.

## Execution behavior

During ordinary save-and-run, the notebook boots the pinned Qwen/vLLM runtime and performs one OpenAI-compatible chat-completion probe before writing the placeholder submission. This makes a successful notebook version meaningful evidence that the model deployment path works.

During the competition rerun, it reuses the same model boot path and then:

1. installs ARC runtime packages from the competition wheel directory;
2. installs the wheelhouse's pinned `requirements.lock` into an isolated `/kaggle/temp/vllm-site-packages` target rather than mutating Kaggle's system Python or persisting thousands of dependency files as notebook output;
3. verifies through the isolated PyTorch stack that CUDA is available, exactly one GPU is visible, and the device name identifies an RTX Pro 6000;
4. launches Qwen3.8-27B FP8 on `127.0.0.1:8000`;
5. waits for the OpenAI-compatible server to become healthy;
6. configures the agent to call only that loopback endpoint;
7. registers the standalone EXP-001 agent with the ARC framework;
8. runs the ARC agent framework against the competition gateway.

The notebook records the vLLM server log in `/kaggle/working/vllm-openai-server.log` for deployment debugging.

## Validation gate

Keep PR #3 in draft until:

- the Kaggle notebook version completes successfully;
- the vLLM server starts on RTX Pro 6000;
- the agent reaches the ARC gateway without model transport errors;
- the exact generated standalone-agent SHA-256 is captured;
- the model input/version is confirmed in the Kaggle run;
- an evaluated score is available.

The full competition submission is a separate deliberate step after the notebook run has been inspected.
