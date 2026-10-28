# EXP-000 Deadline Fallback

This path exists to protect the ARC-AGI-3 deadline while model-serving work
continues independently in EXP-001.

It deliberately uses the stable EXP-000 reproducible random policy and avoids:

- external APIs;
- model inputs;
- vLLM;
- GPU requirements;
- non-competition datasets.

## Build

```bash
python3 scripts/build_standalone_agent.py
python3 scripts/build_kaggle_exp000_fallback.py \
  --username YOUR_KAGGLE_USERNAME
```

Generated files are written to `dist/kaggle-exp000-fallback/` and are ignored
by Git.

## Push

```bash
kaggle kernels push -p dist/kaggle-exp000-fallback
```

The ordinary save-and-run path installs the ARC runtime from the attached
competition wheel directory, validates notebook execution, and writes a dummy
`submission.parquet`. During the competition rerun, the notebook copies the
official ARC-AGI-3 agent framework, registers the standalone EXP-000 agent, and
runs it against the competition gateway.

This fallback is intentionally score-conservative. Its purpose is deadline
coverage: establish a small, auditable submission path that does not depend on
EXP-001 model-serving infrastructure.
