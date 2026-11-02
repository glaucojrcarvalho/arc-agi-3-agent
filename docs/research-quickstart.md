# Research policies: local quickstart

The default `agent/my_agent.py` is the deterministic **EXP-000 control**. Qwen prototypes are separate, opt-in source files so the baseline cannot accidentally be packaged as a model-driven experiment.

## Verify without GPU or credentials

```bash
python scripts/public_preflight.py --all
python -m compileall -q agent scripts src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Build exactly one policy

```bash
# Control; no model needed:
python scripts/build_standalone_agent.py --source agent/my_agent.py --output dist/my_agent.py

# EXP-001 direct Qwen; requires a separate offline model server for actual inference:
python scripts/build_standalone_agent.py --source agent/exp001_agent.py --output dist/exp001_agent.py

# EXP-005/019 research lineage: bounded reasoning, transitions and exploration:
python scripts/build_standalone_agent.py --source agent/exp005_agent.py --output dist/exp005_agent.py
```

These commands perform **local packaging only**. They do not run Qwen, create a valid Kaggle notebook by themselves, or submit to the competition. The historical official EXP-019 submission SHA is **not** inferred from this portfolio checkout.

For an optional public-game smoke test, obtain permitted public ARC environments independently, then use `scripts/smoke_exp005_public_offline.py` with an explicit agent, seed and action budget as specified by its matching experiment report. Fake-model tests validate contracts and action-policy regressions; they **do not** demonstrate model-reasoning improvement.

The EXP-001 notebook builder now defaults to the explicitly built `dist/exp001_agent.py` so it cannot silently package the default random control. Use the independent EXP-005 notebook builder for the adaptive policy only after verifying its pinned offline runtime/model requirements.

See [experiment evidence](experiment-evidence.md), [architecture](architecture.md), [public-repository safety](publication-policy.md), and the [official competition rules](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules). Do not commit tokens, downloaded private environments, generated submissions, or model weights.
