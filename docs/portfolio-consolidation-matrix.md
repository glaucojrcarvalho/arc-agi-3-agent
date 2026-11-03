# Portfolio consolidation decision matrix

**Snapshot:** 2026-11-02 22:57 UTC (2026-11-03 00:57 Kyiv). This is a
**portfolio integration plan**, not an ARC-AGI-3 scoring result or evidence
of an improved competitive agent. Re-check live refs before each mutation.

## Post-deadline disposition (2026-11-03)

The matrix below is retained as the **pre-merge decision record**. Its gate for #30 is now satisfied: [PR #30](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/30) was merged into `main` as `feb4f6e3672f1f76467e8e72d97f1eb322a44a29` after the deadline, following independent 150/150 unit tests, a clean 87-file public preflight, compileall, three standalone packaging/syntax checks and a clean detached clone. The model-free EXP-000 default's Git blob remained byte-identical. Ancestor PRs #3, #7, #8, #9, #10, #11, #13, #14, #15 and #25 are closed/integrated; rejected EXP-011 PR #17 was closed with negative evidence retained. Remaining isolated PRs #5, #12, #16, #26 and #28 are **not automatically mergeable by evidence**. The authoritative state and next steps are in the [post-deadline handoff](portfolio-handoff-20261103.md).

## Safety boundary and source of truth

- Default `main`: `ecae40ddbcb6bba57625ddf76145a37a71a638e8` at snapshot.
- Integration PR [#30](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/30):
  `4f17d300ae23e0f91c53a337f24dabd40d292587`, tree
  `98b81d445680af411be5c863ae83179d9f3af9ec`. It retains the
  EXP-000 default at `agent/my_agent.py` and adds opt-in experimental
  sources and tests. EXP-019 source commit `6c4224b` is an ancestor.
- Official EXP-019 v1 Kaggle submission `57915318`, displayed public score
  **0.34**, is an **external, historically completed artifact**, not a
  repository branch or a value reconstructed from fake-model tests.
  Neither merge nor notebook rebuild should modify or resubmit it.
- At the snapshot GitHub listed **17 open PRs, 30 remote branches and no
  open issues**. Open PR checks reported no combined commit statuses for
  PR #30; absence of a status is **not** a successful CI check.
- Keep Apache-2.0 on this integration. Do not copy third-party agent
  source or adopt the unrelated MIT-0 change in PR #5 without a rights
  and competition-eligibility review.

## Explicit PR dependency and disposition matrix

| PR(s) | Verified relationship to PR #30 HEAD | Decision and evidence gate |
| --- | --- | --- |
| [#30](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/30) | Integration branch from `main`, carrying EXP-001..005, EXP-007..009 and EXP-019 lineages | **MERGE AFTER DEADLINE ONLY**, with fresh public preflight, compile, unit, packaging, diff/license/secret review, exact head SHA and verified mergeability. Use merge commit to retain scientific commit ancestry; no competitive-score claim. |
| [#3](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/3), [#7](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/7), [#8](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/8), [#9](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/9), [#10](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/10), [#11](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/11), [#13](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/13), [#14](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/14), [#15](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/15), [#25](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/25) | Each exact head SHA was an ancestor of PR #30's checked-out HEAD | **CLOSE AS SUPERSEDED AFTER #30 MERGES**, with a link to its merge commit. Keep branches and PR discussions until the historical experiment evidence has been indexed; do not squash away evidence. |
| [#12](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/12) | EXP-006 multiseed evaluator head is **not** an ancestor | **CHERRY-PICK selectively** only independently useful evaluation/seed instrumentation after diff review and offline regression. Do not inherit an obsolete policy wholesale. |
| [#16](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/16) | EXP-010 real-Qwen audit head is **not** an ancestor | **PRESERVE AUDIT; cherry-pick independent reporting/tests** after checking licenses, actual data provenance and compatibility. Regressive inference-cadence experiments are not scoring improvements. |
| [#17](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/17) | EXP-011 rejected balanced clicks; head **not** ancestor | **ARCHIVE negative result** (paired 6→3 level regression on 75 synthetic-model sessions); **consider only** separate public-game-ID RNG alias correction plus tests in a later small PR. Never import failed click policy as default. |
| [#26](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/26) | EXP-020/021 seeded real-Qwen comparisons; head **not** ancestor | **CHERRY-PICK evaluation-only comparator / documentation** after contract/offline validation and exact baseline mapping. EXP-021 matched real-Qwen comparison was 1 level vs 1, not an observed completion gain. |
| [#28](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/28) | EXP-023 bounded observed completion memory; head **not** ancestor | **KEEP ISOLATED DRAFT** or close with explicit unvalidated result. 75/75 fake-model ties and no paired real-Qwen proof: not eligible for default policy promotion. |
| [#5](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/5) | Separate compliance proposal changes Apache-2.0 to MIT-0; head **not** ancestor | **LEGAL/ATTRIBUTION HOLD**: do not merge or relicense without reviewing authorship, dependency notices and applicable competition terms. |
| [#27](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/27) | EXP-022 closed negative study | **PRESERVE CLOSED HISTORY**; 7→6 levels under its paired fake-model protocol, not a real-Qwen regression claim. |

Additional remote heads (`feat/exp-012-*` through `feat/exp-018-*`,
`deadline/*`, `docs/portfolio-audit-20261102`, `sanitize/*`) need
per-branch reachability, unique-commit and published-evidence checks before
any deletion. **No force push, branch deletion or history rewriting** is
authorized by this matrix. Closed PRs and negative-results reports remain
discoverable by permalink.

## Reproduced integration gate (isolated clone)

At the snapshot, a **separate fresh clone** checked out exact PR #30 HEAD
`4f17d30`, with no edits to another agent's worktree:

```bash
python3 scripts/public_preflight.py --all
python3 -m compileall -q agent scripts src tests
PYTHONPATH=src python3 -m unittest discover -s tests -q
python3 scripts/build_standalone_agent.py --help
git diff --check origin/main...HEAD
```

Observed: **86 tracked files**, public preflight clean, Python compilation
passed, **150/150 unit tests passed**, builder CLI smoke passed, diff-check
passed, clean detached worktree. The `--help` check verifies only command
startup; it is not a successful standalone packaging/build test. Full
packaging and representative agent smoke must be rerun before merging.

## Integration sequencing

1. **Until 2026-11-02 23:59 UTC (2026-11-03 01:59 Kyiv): do not merge or
   change any Kaggle submission, selected notebook, quota, or official run.**
2. After the deadline, fetch fresh `main` and PR #30 heads; confirm no
   competing writer or dirty worktree, validate full source/bundle/tests and
   licenses, then merge #30 only if all checks pass.
3. Close only verified, fully subsumed draft PRs with explanatory links.
   Never mark a failed experiment as scoring-positive.
4. Extract unique evaluation corrections from #12/#16/#17/#26 into one
   tightly scoped, tested follow-up PR **per compatible hypothesis**.
   Keep #28 isolated. Document unresolved legal and hardware/model gates.
5. Update README links/status and GitHub repository description/topics only
   after confirming the final `main` revision and access. Review explicit
   attribution and dependency licenses before claiming prize eligibility.

**Interpretation rule:** a Kaggle save-and-run, offline fake-model regression,
real-Qwen public probe, official submitted version, and scored leaderboard
entry are different evidence tiers and must stay labeled separately.
