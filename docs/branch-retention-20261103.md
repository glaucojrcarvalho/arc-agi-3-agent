# ARC-AGI-3 remote-branch retention gate — 2026-11-03

This is a **post-deadline portfolio maintenance** inventory, not an ARC score,
license change, notebook rebuild, or Kaggle submission. A branch may be
reachable from `main` but still be an important named reference for a paper,
negative result, review or notebook. **No branch is deleted by this process.**

## Reproduce in a fresh clone

```bash
git clone https://github.com/glaucojrcarvalho/arc-agi-3-agent.git
cd arc-agi-3-agent
git fetch origin --prune
python3 scripts/report_branch_lifecycle.py --repo . --json > /tmp/arc-branch-inventory.json
PYTHONPATH=src python3 -m unittest tests.test_branch_lifecycle_report -v
```

The Python utility is **read-only**. It reports actual fetched remote refs,
the exact `main` commit, per-head ancestry, and distinct commits relative
to `main`. It will not delete, force-update, checkout or fetch any refs.
`--prune` in the example only prunes **local stale tracking refs**, not
branches on GitHub; for a fully non-pruning inspection use `git fetch origin`.
The inventory becomes stale when upstream moves; repeat immediately before
taking any lifecycle action.

## Verified snapshot / decision matrix

At observed `main` **`59f2c8eb58283cb5b3f1df88b5d618508a6e278a`**:
32 remote branch refs, including `main`; **16 additional reachable branch
heads** and **15 heads with distinct commits**. Counts are *head ancestry*,
not a list of unique experimental ideas or verification of code correctness.

| Group | Branches | Disposition |
| --- | --- | --- |
| Integrated engineering and historical PR heads | `chore/portfolio-handoff-20261103`, `chore/portfolio-integrate-exp019-20261103`, `fix/strict-public-probe-evidence-20261103`, `sanitize/foundation-v1` | **REVIEW RETENTION**, only after confirming source SHAs, surviving GitHub PR and commit links, and no documentation depending on mutable branch names. |
| Integrated experiment heads | `feat/exp-001` through `feat/exp-010` (actual full names in JSON output), `feat/exp-019-transition-evidence-20261101` | **REVIEW RETENTION**; scientific provenance may justify preserving these names despite their commits being on `main`. |
| Unmerged, historically valuable experiments | `feat/exp-011` through `feat/exp-018`, `feat/exp-020-kaggle-probe-seed-20261101`, `feat/exp-022-plan-continuity-20261102`, `feat/exp023-observed-progress-20261102` | **PRESERVE UNMERGED**. Do not promote rejected or unvalidated policies. |
| Other unmerged audit / deadline heads | `deadline/compliance-audit`, `deadline/exp000-fallback`, `deadline/score-exploration`, `docs/portfolio-audit-20261102` | **PRESERVE UNMERGED** pending separate provenance and legal review. |

The abbreviated `feat/exp-001` etc. strings above are group labels, **not**
exact ref names. The live machine-readable inventory contains the exact names.

## Outstanding PRs and decisions

- **PR #5** (license transition, draft): keep **OPEN / LEGAL HOLD**.
  The branch changes Apache-2.0 to MIT-0; do not merge without verifying
  exclusive authorship of submitter-authored portions, third-party notices,
  and actual applicable competition rules. No license was changed here.
- **EXP-019 v1**: preserve official historical submission `57915318`,
  reported public score **0.34**. No portfolio merge reconstructs or changes
  that submitted notebook.
- **EXP-022**: negative fake-model comparison (**7 to 6** levels); preserve
  closed PR #27 and unmerged history. **EXP-023**: fake-model tie (**6 to 6**),
  without matched Qwen-real demonstration; preserve closed PR #28.
- **PR #26**: strict-seed, non-scoring correction selectively incorporated in
  PR #32. Preserve its experimental discussion, do not re-merge conflicting
  policy history. Other documented studies remain linked from
  `docs/experiment-evidence.md`.

**Deletion gate for future maintainers:** require a complete snapshot, exact
per-branch head SHA, verified reachability, retained PR/commit permalinks,
review of README/docs links, no exclusive study artifacts and adequate
write permissions. Never force-push or delete a unique-commit branch merely
because a pull request was closed. This run deliberately retains all names.

## Evidence boundary and handoff

Run `public_preflight.py --all`, `compileall`, full `unittest`, and
standalone build on an **isolated** clean checkout after any code change.
A standalone import or fake-model smoke is not real-Qwen performance.
Kaggle has already closed official submissions (2026-11-02 23:59 UTC);
do not use remaining quota or attempt post-deadline scoring. For the next
competition, start with a new, independently licensed and contract-tested
hypothesis branch; verify its own legal and submission requirements.
