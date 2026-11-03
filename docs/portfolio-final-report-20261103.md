# ARC-AGI-3 — final engineering portfolio report (2026-11-03)

**Scope:** post-deadline repository hygiene only. This is **not** a Kaggle submission, score improvement, prize-eligibility certification or proof of hidden-game performance.

## Verified engineering baseline

The final code-focused merge in this review was [PR #34](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/34), merged into `main` as [`18e262056f228c03e4379f5245f69fe1d49e4f62`](https://github.com/glaucojrcarvalho/arc-agi-3-agent/commit/18e262056f228c03e4379f5245f69fe1d49e4f62). This report is a separate documentation-only commit on top of that **verified code snapshot**.

A real public-game smoke failure was reproduced on previous `main` (`cd9a6e38`): direct execution of `scripts/smoke_public_games.py`, with the official SDK available but without an externally supplied `PYTHONPATH`, failed with `ModuleNotFoundError: No module named 'arc_agent'`. Adding `PYTHONPATH=src` made it pass, identifying a missing script bootstrap rather than a policy/gameplay regression.

[PR #34](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/34) modified only:
- `scripts/smoke_public_games.py`: explicitly bootstrap project and `src/` import roots for standalone script execution; remove the incomplete late import-root insert.
- `tests/test_public_smoke_import_path.py`: an external-working-directory, `python -I` subprocess regression test, mocking only the optional game-SDK import layer and importing the real local `arc_agent` code.

This is a **tooling/contract correction**, not an experimental policy promotion.

### Independent pre-merge and post-merge checks

Run on detached clean Remote Workbench worktrees with **Python 3.12.15**, without GitHub Actions:

| Check | Observed result |
| --- | --- |
| `PYTHONPATH=src python -m unittest discover -s tests -q` | **169 tests passed**, including isolated-import regression |
| `python scripts/public_preflight.py --all` | Clean; **98 tracked files** checked |
| `python -m compileall -q agent scripts src tests` | Passed |
| `python scripts/build_standalone_agent.py` | Built `dist/my_agent.py` |
| `python -m py_compile dist/my_agent.py` | Passed |
| `git diff --check` | Passed on the PR |
| Public-only smoke **without** `PYTHONPATH` | Four sessions, five actions each, **20 actions, zero contract errors, zero levels completed** |
| SDK/model for smoke | Existing `arc_agi` and `arcengine` installation; deterministic dummy model, **not Qwen** |
| GitHub Actions triggered by this work | None |

The public smoke used `ls20` and `vc33`, with the EXP-001 and EXP-002 historical agents; it tests import/execution contracts, not game-solving performance. An earlier direct smoke attempt failed on the import boundary and was **not counted** as a successful run.

Exact unchanged blobs at the verified code merge:
- Default stable agent `agent/my_agent.py`: `9695133008db25b63f042ea6371c34a57308a710`.
- `LICENSE`: `dca407aafeebd2ccb07c93a80050df866a61da5f` (Apache-2.0).

## Branch, PR and issue disposition

The fetched-remote snapshot at code HEAD `18e2620` contained **34 remote branch refs including `main`**: **18 other branch heads reachable from main** and **15 with unmerged commits**. This counts branch ancestry, not experimental success. Reproduce the current state using:

```bash
git fetch origin
python3 scripts/report_branch_lifecycle.py --repo . --json > /tmp/arc3-branch-inventory.json
```

| Decision | Evidence / disposition |
| --- | --- |
| **MERGE after tests** | [#30](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/30) engineering integration; [#16](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/16) Qwen probe auditing; [#12](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/12) public multiseed tooling; [#32](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/32) strict seed validation; [#33](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/33) read-only branch inventory; and [#34](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/34) smoke import fix. None demonstrates a new official score. |
| **CHERRY-PICK / selective extraction completed** | Independent provenance/seed checks from the conflicting [#26](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/26) were implemented on `main` via #32; its experimental policy history was **not** merged over the validated comparator. |
| **ARCHIVE, never promote** | EXP-022 [#27](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/27): fake-model A/B regressed from **7** to **6** levels; EXP-023 [#28](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/28): fake-model tie (**6 vs 6**) without matched real-Qwen validation. Both histories remain accessible. |
| **KEEP isolated** | The **15 unmerged** remote heads, including EXP-011–018, EXP-020, EXP-022, EXP-023 and deadline/audit heads, are preserved pending exact SHA/artifact/attribution review. **No experimental history was force-pushed or deleted.** |
| **REVIEW retention only** | The **18 reachable heads** are potential deletion candidates, not automatically disposable; documentation and PR links must be reviewed before removing a named scientific reference. |
| **LEGAL HOLD** | [PR #5](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/5) remains the sole open PR at this snapshot. It proposes a broad Apache-2.0 → MIT-0 switch and cannot be merged safely without rights-holder and third-party attribution review. |
| **Issues** | **Zero open issues** as observed during the GitHub query. |

No remote branches were deleted. The available GitHub connector actions did not provide a dedicated safe branch-delete operation; the isolated Remote Workbench clone had no authenticated `gh` CLI for branch cleanup. This is a **real outstanding repository-hygiene item**, not a completed purge. Re-check exact ref SHAs immediately before any future deletion.

## Competition and publication boundary

The ARC-AGI-3 Kaggle deadline was **2026-11-02 23:59 UTC**. No post-deadline competition submission or quota usage was attempted during portfolio work.

Preserve EXP-019 v1's **historical** official submission **`57915318`**, reported Kaggle public score **0.34**. Repository merges do **not** reconstruct the exact submitted notebook and must not imply a newer competitive score or a final private leaderboard result. The unchanged baseline agent hash above is **not** the EXP-019 submitted artifact hash.

The local public preflight found no issues in the scanned tracked files, but does **not** certify absolute freedom from secrets, third-party rights issues or undisclosed assets. Do not publish credentials, raw private traces, copyrighted model weights or private game data. The Apache-2.0 license remains untouched; review author rights, third-party attributions and current competition rules before considering [PR #5](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/5). GitHub About/topics updates were not performed because no corresponding write operation was available through this connector.

## Handoff for the next competition

Start a **new, independent competition project** rather than treating this repository's historical Kaggle score as a transferable baseline. Reuse only the tested engineering patterns: explicit contract/preflight, standalone build, run identifiers and artifact hashes, public-only fixtures, seed-paired evaluations, error/wallclock/action/model-call telemetry and clear labeling of fake vs real model results. Before implementing a policy, independently verify the new competition's deadline, eligibility/license requirements, dataset and third-party rights, offline/network contract, GPU/time limits, quota and evaluation protocol.

Recommended initial sequence: isolate an official starter + versioned environment; run its unmodified baseline offline; record provenance; write one hypothesis and a minimal contract test; then run paired public tests before any expensive inference. Do not import unvalidated EXP-022/023 policies as improvements.

Related evidence: [architecture](architecture.md), [experimental ledger](experiment-evidence.md), [branch-retention gate](branch-retention-20261103.md), [prior handoff](portfolio-handoff-20261103.md) and [research quickstart](research-quickstart.md).
