# Deadline Transition-Aware Score Experiment

This branch is deliberately downstream of EXP-001. It does not change the
Kaggle model-serving runtime.

The experiment records the observable transition produced by each selected
action. For a given visual-state fingerprint, a simple action is suppressed
from the model's legal action set only after at least two observed attempts
produced no frame change, no level progress, and no state change.

Complex coordinate actions are never suppressed by action id alone because
different coordinates can have different effects.

This is a deadline-side experiment, not a replacement for the stable EXP-001
baseline. It should be evaluated only after the direct-model notebook completes
successfully and a known-good submission is preserved.
