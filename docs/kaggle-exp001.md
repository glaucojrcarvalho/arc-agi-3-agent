# EXP-001 Kaggle Deployment

EXP-001 is intentionally not expected to run the 27B FP8 model on a developer laptop. The deployment target is Kaggle's ARC-AGI-3 RTX Pro 6000 runtime.

## Inputs

The generated notebook pins these public Kaggle inputs:

- competition: `arc-prize-2026-arc-agi-3`;
- offline vLLM wheelhouse: `driessmit1/arc3-vllm-h100-wheelhouse-v3`;
- model: `mikedan7/qwen3-8-27b-fp8-official/PyTorch/hf-fp8/1`.

The Kaggle model mirror states that it is an unmodified mirror of `Qwen/Qwen3.8-27B-FP8` pinned to upstream revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`.

Kaggle model inputs are mounted under `/kaggle/input/models`. EXP-001 prefers `/kaggle/input/models/mikedan7/qwen3-8-27b-fp8-official/pytorch/hf-fp8/1` and falls back to guarded discovery within the models mount by locating a unique directory for the pinned model slug that contains a Hugging Face `config.json` and safetensor shards.

Kaggle dataset mount layout can vary even when `dataset_sources` is preserved in server-side kernel metadata. EXP-001 checks both the legacy `/kaggle/input/<slug>` layout and the newer `/kaggle/input/datasets/<owner>/<slug>` layout. It resolves exactly one `arc3-vllm-h100-wheelhouse-v3` mount containing `requirements.lock` and wheel files.

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
  -p /path/to/arc-agi-3-exp-001/dist/kaggle-exp001 \
  --accelerator NvidiaRtxPro6000
```

This starts Kaggle's save-and-run phase using the explicitly requested RTX PRO 6000 accelerator. Both the kernel metadata (`enable_gpu: true`, `machine_shape: NvidiaRtxPro6000`) and the CLI flag are intentional. Do not infer that the batch execution has CUDA merely from the accelerator selection in the interactive editor: verify the batch logs separately. This does not itself spend a competition submission.

## Execution behavior

During ordinary save-and-run, the notebook boots the pinned Qwen/vLLM runtime and performs one OpenAI-compatible chat-completion probe before writing the placeholder submission. This makes a successful notebook version meaningful evidence that the model deployment path works.

During the competition rerun, it reuses the same model boot path and then:

1. installs ARC runtime packages from the competition wheel directory;
2. resolves the public ARC3 vLLM wheelhouse and collects non-blocking diagnostics on GPU availability, including CUDA device nodes, driver device count, and optional nvidia-smi;
3. installs the wheelhouse's pinned requirements into isolated `/kaggle/working/vllm-site-packages` and exposes only that target through `PYTHONPATH`;
4. launches Qwen3.8-27B FP8 on `127.0.0.1:1234` with the same core vLLM flags used by the public TAAF Kaggle bootstrap;
5. waits for the OpenAI-compatible server to become healthy and, during ordinary save-and-run, performs a real chat-completion validation;
6. configures the agent to call only that loopback endpoint;
7. registers the standalone EXP-001 agent with the ARC framework and runs it against the competition gateway;
8. removes the temporary target install after ordinary validation so it is not persisted as notebook output.

The notebook records the vLLM server log in `/kaggle/working/vllm-openai-server.log` for deployment debugging. GPU diagnostics (`nvidia-smi`, CUDA device nodes, and CUDA Driver API) do not reject the deployment solely because a diagnostic tool is unavailable. The definitive GPU check is starting the pinned vLLM server and completing a real inference probe. If the batch log shows no NVIDIA devices or `libcuda.so.1`, treat that as missing GPU access in that batch session rather than a Qwen model failure.

## Validation gate

Keep PR #3 in draft until:

- the Kaggle notebook version completes successfully;
- the vLLM server starts on RTX Pro 6000;
- the agent reaches the ARC gateway without model transport errors;
- the exact generated standalone-agent SHA-256 is captured;
- the model input/version is confirmed in the Kaggle run;
- an evaluated score is available.

The full competition submission is a separate deliberate step after the notebook run has been inspected.
