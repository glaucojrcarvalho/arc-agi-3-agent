# Local Setup

This project keeps its original agent source in this repository while using the official ARC-AGI-3 starter as **external local tooling** for environment setup, local play, notebook generation, and Kaggle submission.

The upstream starter and framework are not vendored into this repository.

## Requirements

- Python 3.12
- Git
- A Kaggle account with the ARC-AGI-3 competition rules accepted
- A Kaggle API token stored outside version control

## 1. Clone both repositories

Place the project and official starter next to each other:

```bash
git clone https://github.com/glaucojrcarvalho/arc-agi-3-agent.git
git clone https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter.git
```

Expected layout:

```text
workspace/
├── arc-agi-3-agent/
└── ARC-AGI-3-Kaggle-Starter/
```

## 2. Configure the official starter

Follow the upstream setup instructions in:

https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter

Keep the Kaggle token in the starter's local `.kaggle/` directory as described by the upstream project. Never place credentials in this repository.

The starter currently installs `arc-agi` and clones the ARC-AGI-3-Agents framework during setup. Those upstream dependencies can move independently of this repository, so evaluated experiments must record their exact versions rather than assuming `main` is stable.

## 3. Build the standalone agent

The official starter packages only its `agent/my_agent.py` into the generated submission notebook. Reusable modules in this repository therefore need to be bundled into a standalone file first:

```bash
cd arc-agi-3-agent
python scripts/build_standalone_agent.py
```

This produces ignored build output at:

```text
dist/my_agent.py
```

For `EXP-000`, which has no internal package imports, the output is byte-for-byte identical to `agent/my_agent.py`. Later experiments that import `arc_agent` embed the internal package into the standalone artifact.

## 4. Copy the standalone agent into the starter

From the shared parent directory:

```bash
cp arc-agi-3-agent/dist/my_agent.py \
   ARC-AGI-3-Kaggle-Starter/agent/my_agent.py
```

The generated file is intentionally ignored and should not be committed.

## 5. Set up and verify locally

```bash
cd ARC-AGI-3-Kaggle-Starter
make setup
make verify-local
```

If the smoke test succeeds:

```bash
make play-local
```

The first project milestone is to confirm that `EXP-000` executes end-to-end without errors before any Kaggle submission is made.

## 6. Capture experiment provenance

Immediately before an evaluated run, capture the exact versions and exact standalone artifact used:

```bash
cd ../arc-agi-3-agent
python scripts/capture_environment.py \
  --starter ../ARC-AGI-3-Kaggle-Starter
```

The script probes the starter's own `.venv` interpreter rather than whichever Python happens to launch the script. It reports only public-safe identifiers:

```json
{
  "agent_sha256": "...",
  "arc_agi_version": "...",
  "framework_revision": "...",
  "project_dirty": false,
  "python_version": "...",
  "revision": "...",
  "starter_revision": "..."
}
```

The command exits non-zero if required provenance is missing. Copy the identifiers into `experiments/results.csv` together with the actual score, action count, runtime, model, and configuration. Do not invent or copy results from someone else's run.

For a later reproduction, check out the recorded project/starter/framework revisions, use the recorded package/runtime versions, rebuild the standalone agent, and verify its SHA-256 before comparing results.

## 7. Public-code disclosure

Kaggle's public-code-sharing rule requires Competition Code shared publicly during the competition to also be shared on the discussion forum or notebooks associated with that competition. Because this repository is public, create an ARC-AGI-3 Kaggle disclosure and link it from the README before relying on this repository for a competition submission.

Competition rules: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules

## Publication check

Before committing experiment updates:

```bash
git diff --cached
python scripts/public_preflight.py
```

Run the preflight command from this repository, not from the external starter workspace.

## Submission

Notebook generation and Kaggle submission should initially use the official starter's workflow. Generated submission notebooks, `submission.parquet`, credentials, downloaded environments, recordings, and model artifacts remain outside this repository or in ignored paths.

Do not submit until:

1. local verification succeeds;
2. experiment provenance is complete;
3. public-code disclosure requirements are satisfied;
4. the standalone artifact hash matches the artifact being evaluated.
