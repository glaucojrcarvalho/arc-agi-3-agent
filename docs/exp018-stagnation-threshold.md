# EXP-018 — Changing the onset of model-free exploration does not improve public levels

Date: 2026-11-01. Draft public-only experiment stacked on EXP-009 (#15).
This report concerns the offline deterministic FAKE-model public-game transport,
not a Qwen evaluation, Kaggle competition score, or RHAE estimate.

## Prior evidence and research

EXP-005 (#10) added bounded reasoning memory, action plans, and novelty
exploration following stagnation. In saved real-Qwen public probes, EXP-005
v4 and EXP-009 each completed two levels in 320 actions across four public
games; EXP-009 used 100 rather than 147 Qwen calls and 502.36 rather than
700.78 accumulated seconds. Completion-action efficiency moved in opposite
directions across games, so no score improvement has been established.

The ARC-AGI-3 technical description separates exploration, world modeling,
goal inference, and planning. It evaluates completed levels and action
efficiency, not the number of distinct board pixels:
https://arxiv.org/abs/2603.24621

The public Memento 3 report (October 2026) argues for explicit, revisable
transition models grounded in observed outcomes, rather than assuming
all visible changes are progress:
https://arxiv.org/abs/2610.11794
Its reported agent is materially different from this frozen Qwen setup.
Neither paper predicts that a fixed exploration threshold will help.

## Scope and hypothesis

Prior trials showed that more model calls do not necessarily improve level
completion. The current baseline switches from model inference to cheap
model-free novelty after 8 nonprogress steps in coordinate-action games and
16 steps in keyboard-only games. EXP-018 varies only those two onset
thresholds, leaving the policy, transition fingerprint, real model, offline
Kaggle runtime, and scoring hooks unchanged:

| Policy | Coordinate onset | Keyboard onset |
| --- | ---: | ---: |
| EXP-009 baseline | 8 | 16 |
| EXP-018 early | 4 | 8 |
| EXP-018 late | 12 | 24 |

Variants are generated into isolated standalone agents, never copied into
the competition agent. Neither variant is tuned to a particular game's ID,
board data, or goal. Only level-counter transitions count as completion.

## Public screening and measured results

Exactly 25 public ARC-AGI-3 environments, three independently varied
controller RNG seeds (0, 1, 2), and an 80-action budget yield 75 paired
sessions and 6,000 actions per policy, 18,000 actions total. A deterministic
fake transport model was used for every policy. Environment seeds alone are
not taken as proof of independent action trajectories.

| Metric | Baseline | Early | Late |
| --- | ---: | ---: | ---: |
| Completed levels | **6** | 5 | 4 |
| Sessions with levels | **6** | 5 | 4 |
| Fake-model calls | 1,616 | 1,140 | 2,050 |
| Local summed wallclock | 130.724 s | 127.192 s | 129.144 s |
| Session wins/losses vs baseline | — | 1 / 2 | 2 / 4 |
| Session ties vs baseline | — | 72 | 69 |
| Sum of first-completion indices (unpaired) | 229 | 194 | 222 |

The final row is expressly NOT an apples-to-apples action-efficiency
comparison: different sets of levels were completed.

The EXP-018 measurement update also records authoritative first-completion
action indices. For levels completed by both policies in the same game/seed
pair, early exploration finished 3 levels earlier and 1 later (4 matched
level milestones; baseline index sum 157 versus candidate 122). Late
exploration finished both of its 2 matched milestones later (index sums
83 versus 100). All other milestone comparisons are excluded when the
number of solved levels differs.

The early variant produced a net gain in one public game but net losses in
two; late gained in one and lost in three. The early variant's 29.46%
reduction in simulated model calls did not offset a lost completed level.
Late exploration added 26.86% fake-model calls and lost two levels.
The tiny differences in local wallclock are not Qwen or GPU latency
benchmarks, and none of these runs can establish an official RHAE gain.

## Reproduction and verification

The evaluation uses the EXP-009 source at commit
d2a8a174870a04a673e7e3ce736246f942bcc151. Public environments must
already be installed using the ARC toolkit. Generate the baseline with
scripts/build_standalone_agent.py and the two isolated variants with
scripts/build_exp018_variant.py, then run the same
scripts/smoke_exp005_public_offline.py program for each using all 25 public
game IDs, seeds 0 1 2, 80 actions, and --vary-policy-seed. Compare matched
inventories with scripts/compare_public_controller_seeds.py and action
milestones with scripts/compare_exp018_milestones.py.

Aggregates, controller seeds, exact generator thresholds, and SHA-256 hashes
of all three generated public agents are in
experiments/exp018-public-aggregate.json. Raw action trajectories,
local recordings, model weights, Kaggle artifacts, personal context and
evaluation-private data must not be committed.

## Decision

**Reject both EXP-018 variants as submission candidates.** They regressed
verified level completion in the public fake-model screening cohort. The
new action-milestone instrumentation can be retained because it rules out
misleading comparisons based on raw pixel motion or unpaired action sums.

Keep the EXP-009 notebook and original Qwen3.8-27B FP8 / RTX PRO 6000 /
offline pinned runtime unchanged. No additional Kaggle GPU save-and-run
was justified by these results. No official competition submission was
performed. Any submission requires the user's separate Monday review.
