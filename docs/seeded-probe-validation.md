# Public Qwen probe comparison — seed and progress contract

**Portfolio-only engineering correction, 2026-11-03.** This file documents a
backward-compatible, fail-closed validation extension of
[`scripts/compare_real_public_probes.py`](../scripts/compare_real_public_probes.py).
It does **not** run a model, Kaggle scoring, or competition submission.
The independent experimental provenance is [EXP-020/021 PR #26](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/26);
the already-integrated historical comparator is [PR #16](https://github.com/glaucojrcarvalho/arc-agi-3-agent/pull/16).
The EXP-019 v1 official submission **57915318**, displayed public score
**0.34**, is unchanged.

## Validated invariants

A pairing is accepted only if **both** probe files are complete, report the
same Qwen model, exactly the same public-game inventory and per-game action
counts, and pass the authoritative `levels_completed` trace checks.

Newer probes exposing `probe_protocol` must state
`official_submission: false`, `verified_progress: levels_completed`, and
explicit `controller_seed` (integer >= 0 or explicit `null`) and
`environment_seed` (integer >= 0). Each game row must repeat both values,
and `level_completion_actions` must exactly match new high-water marks
derived from the action-level `levels_completed` counter. The comparator
rejects mixed seeds, missing row seed metadata, unsupported progress
provenance, and inconsistent completion actions. Pixel changes never count
as level completion, and the output contains aggregates rather than raw
action traces. A `null` controller seed is explicitly **not** an
independent seeded trial.

Older probes with **no** protocol metadata can still be compared using the
historical interface, but are labeled
`legacy-unseeded-not-independently-paired`. A legacy probe may not be
paired with a probe carrying an explicit protocol. Historical outputs
remain observational; they do not inherit seed verification retroactively.

## Reproduce locally

With two public-only result JSON files containing `model`,
`probe_complete`, `completed_games`, and per-game
`action_trace`/`levels_completed` records:

```bash
python scripts/compare_real_public_probes.py --baseline /path/to/baseline.json \
  --candidate /path/to/candidate.json --output /tmp/public-qwen-aggregate.json
PYTHONPATH=src python -m unittest tests.test_compare_real_public_probes -v
```

Do not commit private traces, model weights, tokens, hidden-game content,
Kaggle authentication, or notebook submissions. The provided tests use
synthetic fixture documents and **no Qwen inference**.

## Historical decision and limitations

The EXP-020/021 **real-Qwen** public probe pair, controller seed 101,
environment seed 0, completed **1 level vs. 1** across four public games.
The only first completion in `r11l` occurred at actions **46 vs. 59**
(the candidate was later by 13 actions). Model calls were **88 vs. 86**;
sum recorded wallclock **426.56 vs. 410.58 seconds**. These observations
do **not** demonstrate higher completion or competitive score.

Checking matching seed metadata does not prove that the runtime actually
applied those seeds, that public cases generalize to private games, or
that wallclock conditions were controlled. For a new competition, the
comparison protocol needs independent runtime provenance and explicit
per-run action limits in addition to this offline JSON contract.
No score or Qwen-real claim arises from fixture-based unit tests.

**Disposition:** integrate this validation-only correction; keep EXP-020/021
model and notebook interventions as historical, unpromoted hypotheses.
EXP-022 (negative fake-model result) and EXP-023 (fake-model tie without
real-Qwen validation) likewise remain unpromoted. Existing Apache-2.0
licensing and third-party attribution rules are unchanged.
