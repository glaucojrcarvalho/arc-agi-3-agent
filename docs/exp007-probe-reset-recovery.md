# EXP-007 — Recover EXP-005 public-game probe from RESET metadata omission

Date: 2026-10-31. **Public-only smoke and harness correctness, not an official competition submission.**

## Confirmed Kaggle EXP-005 v2 failure

The latest EXP-005 v2 **save-and-run** finished with KernelWorkerStatus.ERROR.
Its Kaggle logs show a successful vLLM boot with Qwen3.8-27B FP8 on
RTX PRO 6000, successful model-validation inference, and the full first
public-game trace summary for ls20:

| Game | Qwen calls | Public actions | Levels | Elapsed | Heuristic actions | Plan actions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ls20 seed 0 | 11 | 80 | 0 | 51.04 s | 59 | 10 |

The second public game, vc33, then failed with:
AttributeError: 'GameAction' object has no attribute 'reasoning'.
This is independent of the earlier v1 missing-game_id constructor bug.

Root cause: MyAgent.choose_action deliberately returns raw GameAction.RESET
in GAME_OVER and NOT_PLAYED states. Unlike normal EXP-005 actions, RESET
has no per-action reasoning attribute. The old probe dereferenced it during
Arcade.step and again during trace collection. The enum values are singletons,
so a stale dynamically attached reasoning field would not be reliable.

## Corrections

- Normalize optional metadata, sending an empty dictionary on RESET even
  if stale enum metadata is present, accepting dict on other actions and
  rejecting malformed types.
- Preserve GameAction.action_data.model_dump() for the official step contract.
- Distinguish RESET transitions in traces and report reset counts and highest
  observed level separately from final level.
- Write public results checkpoint after *each* completed game, so if a later
  game fails, earlier traces remain accessible. Incomplete runs are labeled.
- Add regression tests for absent and stale RESET metadata, invalid metadata,
  and partial checkpoint recovery.
- Add offline smoke with real public environments, standalone packaged agent,
  two seeds, deterministic FAKE model. No Qwen, hidden eval or official submit.

## Local validation

Suite: 114 passed, command:
    PYTHONPATH=src:. python -m unittest discover -s tests -q

Offline smoke command, with standalone agent already built:
    PYTHONPATH=src:. python scripts/smoke_exp005_public_offline.py --environments-dir /path/to/public/environment_files --seeds 0 1 --max-actions 80

| Game | Seeds | Actions | RESETs | Max levels each |
| --- | --- | ---: | ---: | --- |
| ls20 | 0, 1 | 160 | 0 | 0, 0 |
| vc33 | 0, 1 | 160 | 2 | 0, 0 |
| r11l | 0, 1 | 160 | 2 | 1, 1 |
| tn36 | 0, 1 | 160 | 2 | 0, 0 |
| **Total** | **8 sessions** | **640** | **6** | **2** |

Local screen: 278 FAKE model calls, 356 heuristic actions, 38.589 s summed
per-session CPU wallclock. vc33 and tn36 generated RESET and continued.
Both r11l first-level completions were observed with a FAKE deterministic
model, **not Qwen**.

These results **do not** indicate improved Kaggle scores. EXP-006 used a
different model-free policy, 25 games, and three seeds; it is not a direct
A/B against Qwen. Only a real-Qwen public probe can establish finished
notebook execution and game progress.

## Release gates

1. Build same pinned offline Python 3.12 notebook, same Qwen FP8 model
   and wheelhouse, RTX PRO 6000, internet disabled.
2. Save-and-run only after checking for active Kaggle GPU jobs.
3. Verify Qwen inference and four completed public-game checkpoints.
4. Compare levels, actions, model calls and elapsed time against EXP-004,
   noting its three 15-action public games were a much smaller budget.
5. Do not invoke competition submit endpoint before approval on 2026-11-02.
   Do not equate public progress to the leaderboard score.

Background: https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/
