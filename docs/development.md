# Development Workflow

The repository uses a PR-first workflow. `main` represents validated research milestones rather than the raw sequence of implementation attempts.

## Branch and worktree model

Keep one primary task per branch and, when working locally on multiple tasks, one worktree per branch.

Example:

```bash
git fetch origin

git worktree add ../arc-exp-000 -b feat/exp-000-runtime origin/main
git worktree add ../arc-exp-001 -b feat/exp-001-qwen-baseline origin/main
git worktree add ../arc-transition-memory -b research/transition-memory origin/main
```

This keeps experiment dependencies, generated files, and uncommitted changes isolated while allowing independent progress.

## Pull requests

Each PR should answer one clear question or deliver one coherent infrastructure change. Prefer a small number of meaningful commits over a commit per edit.

Before opening or updating a PR:

```bash
python scripts/public_preflight.py
python -m compileall -q agent scripts src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

For experiment PRs, include:

- experiment identifier;
- hypothesis or purpose;
- exact project and upstream revisions used for evaluated runs;
- relevant configuration;
- actual measured results only;
- known limitations or negative findings.

## Main branch

Normal work should not be committed directly to `main`. After the one-time foundation-history sanitation, changes should arrive through reviewed PRs so the public history remains concise and interpretable.
