# Public Repository Policy

This repository is public. Contributions should contain only material intentionally suitable for public distribution.

## Do not commit

- API keys, access tokens, passwords, private keys, cookies, or credentials of any kind.
- `.env` files, `kaggle.json`, project-local Kaggle credentials, or generated submission outputs.
- Local machine paths, shell history, debug dumps, or logs containing environment-specific information.
- Raw competition downloads, local game recordings, generated submissions, checkpoints, or large model artifacts unless there is an explicit reason and redistribution is permitted.
- Private correspondence, chat transcripts, personal notes, or unrelated personal information.
- Third-party source code unless its license clearly permits redistribution and required attribution is preserved.

## Safe publication targets

The repository is intended for:

- original source code for the ARC-AGI-3 agent;
- architecture and algorithm documentation;
- reproducible experiment configurations;
- sanitized aggregate evaluation results;
- public-safe revision/version provenance and artifact hashes;
- tests written for this project;
- references to public external resources;
- deliberately published research notebooks.

## Development workflow

`main` is the stable research line. Normal development should happen on short-lived branches and enter through pull requests. When multiple experiments or infrastructure tasks are active, use separate Git worktrees so generated files, dependencies, and uncommitted changes remain isolated.

Suggested branch families:

```text
feat/        executable capabilities or experiments
research/    exploratory agent/reasoning work
chore/       infrastructure, CI, packaging, security
fix/         correctness fixes
docs/        documentation-only changes
```

One primary purpose per PR keeps experiment history understandable and makes later ablations easier to trace.

## Before each push

1. Review the complete staged diff.
2. Run `python scripts/public_preflight.py`.
3. Confirm newly added third-party code has an explicit compatible license.
4. Confirm generated files and local artifacts are excluded.
5. Confirm experiment notes contain technical observations only.
6. Confirm the exact evaluated standalone artifact can be identified by SHA-256.
7. Confirm public competition code is also disclosed through the ARC-AGI-3 Kaggle competition surface as required by Kaggle's public-code-sharing rule.

If a secret is ever committed, removing it in a later commit is not sufficient. Revoke or rotate the credential immediately and then clean the Git history as appropriate.

## Third-party code

Public availability is not the same as an open-source license. A repository without an explicit license should be treated as source that can be referenced but not copied into this project without separate permission.

The official ARC-AGI-3 starter may be used as external tooling and documentation. Code from external projects should only be incorporated after verifying the applicable license and attribution requirements.

Competition rules: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules
