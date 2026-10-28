# ARC-AGI-3 Deadline Compliance

This checklist separates submission validity from prize eligibility.

## Deadline and notebook constraints

For the 2026 ARC-AGI-3 competition:

- final submission deadline: November 2, 2026 at 23:59 UTC;
- submissions are made through Kaggle notebooks;
- CPU notebooks may run for up to 9 hours;
- GPU notebooks may run for up to 9 hours;
- internet access must be disabled;
- publicly available external data and pre-trained models are permitted;
- the submission file is generated automatically when the agent acts.

## Open-source eligibility

ARC Prize 2026 requires submitter-authored code and methods to be released
under a permissive public-domain-style license such as CC0 or MIT-0 for prize
eligibility. Third-party code may remain under compatible open-source licenses
that permit public sharing.

This repository therefore uses MIT-0 for submitter-authored work. Dependencies,
competition assets, and third-party frameworks retain their upstream licenses.

## Before final submission

- ensure the Kaggle notebook completes a save-and-run;
- verify internet is disabled;
- verify the agent takes at least one action so Kaggle produces a submission;
- record the exact repository revision and standalone-agent hash;
- confirm the public repository contains the submitted method;
- publish the corresponding Kaggle disclosure/notebook required by the
  competition's public-code rules;
- preserve third-party license notices where required;
- keep at least one known-good submission before attempting higher-risk
  experiments.

The EXP-000 fallback exists specifically to satisfy the final item without
depending on EXP-001 model-serving infrastructure.
