# Support V1 Label Evaluation Notes

## What this labeled evaluation measures

The labeled support evaluation is a per-ticket decision-point check on the current `support_v1` path:

`support case history -> support_v1 event conversion -> generic IML replay -> decay/revalidation -> low-stakes route`

For each label, the runner replays only the entity history visible at the labeled `decision_timestamp` and compares the routed path (`fast_path` or `deep_path`) against the hand-authored route label. The artifact is mainly testing whether the current support mapping plus generic router produce the intended top-level handling path from support-visible history.

## What label accuracy does and does not mean

In this scaffold, label accuracy means route agreement on a small labeled slice. It is not a claim that the underlying support judgment was globally correct, that the profile attributes are well calibrated, or that the system is production-ready. It also does not measure downstream resolution quality, cost asymmetry between `fast_path` and `deep_path`, or comparative performance against `naive_summary` and `full_history`.

## Most informative failure patterns

The highest-signal failures are guardrail misses:

- `contradiction_present` labels routed to `fast_path`
- `profile_too_stale` labels routed to `fast_path`
- `wrong_first_impression` cases that do not flip back to `deep_path`

In the current sample, the dominant pattern is the opposite error: recent cooperative histories labeled `fast_path` still route to `deep_path` because `overall_confidence` stays below threshold and `unknownness` stays high. That is more informative than the raw `5/8` accuracy because it suggests the scaffold is currently over-conservative rather than missing obvious contradiction or staleness guardrails.

## Immediate next iteration

The next pass should improve calibration and diagnostics before changing the core route policy:

- make clean recent cooperative histories capable of reaching `fast_path`
- report `fast_path` precision, `deep_path` recall, and explicit guardrail-miss counts alongside overall accuracy
- add baseline comparison on the same visible-history slice
- export enough per-label context to separate support event-mapping issues from generic confidence/unknownness threshold issues

The immediate target is not higher raw accuracy by itself. It is to distinguish safe routine support cases from sparse, stale, or contradictory histories for the right technical reason.
