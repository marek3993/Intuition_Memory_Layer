# Evaluation Notes

## Purpose Of The Synthetic Dataset

`datasets/synthetic_entities.json` is a compact, deterministic testbed for the explicit Intuition Memory Layer MVP.

Its purpose is to exercise the current profile update loop end to end:

- replay timestamped events into an `IntuitionProfile`
- accumulate attribute updates from explicit event semantics
- apply decay across long gaps
- trigger heuristic revalidation when the profile becomes stale, contradictory, or low-confidence
- make a final `fast_path` vs `deep_path` routing decision

The dataset is not trying to model real-world distribution. It is trying to provide small, inspectable scenario traces where expected qualitative behavior is clear.

## Scenario Semantics

### `stable_good_actor`

A consistently positive actor with repeated high-reliability `fulfilled_commitment` events and occasional cooperative responses. This scenario is meant to verify that repeated aligned evidence produces high trust, low contradiction, acceptable confidence, and a `fast_path` outcome under low stakes.

### `false_positive_first_impression`

An actor who starts with several strong positive signals, then accumulates contradictions and ignored requests. This scenario tests whether the profile can recover from an initially favorable but ultimately wrong impression and route to `deep_path` once inconsistency becomes material.

### `false_negative_first_impression`

An actor who starts with several missed requests, then shows a long run of reliable follow-through. This scenario tests the opposite recovery direction: an initially negative impression should be revised upward when later evidence is consistently positive.

### `high_contradiction_actor`

An actor with alternating positive behavior and repeated `contradiction_detected` events. This scenario is meant to stress contradiction handling rather than simple trust accumulation. The expected behavior is persistent hesitation, elevated contradiction load, and conservative routing.

### `sparse_data_actor`

An actor with only a few concrete interactions separated by long inactivity periods. This scenario is meant to test decay, freshness loss, revalidation triggering, and behavior under weak or stale evidence rather than overt contradiction.

## What The Current Evaluation Runner Measures

The current lightweight synthetic runner is `run_evaluation.py`.

It prints console summaries and writes a machine-readable export to `artifacts/latest_evaluation.json`.

For each entity, it currently measures or reports:

- event count
- decay checkpoint count, where a decay checkpoint is a gap of at least 21 days before the next event
- whether revalidation was triggered at the final decision point
- revalidation reason strings from `revalidate_profile()`
- final routing decision: `fast_path` or `deep_path`
- routing reason string from `route_decision()`
- `first_impression_trust`
- `final_trust`
- final `overall_confidence`
- final `unknownness`
- final `freshness`
- final `contradiction_load`

At the aggregate level, it reports:

- number of `fast_path` selections
- number of `deep_path` selections
- average `overall_confidence`
- average `unknownness`
- `false_first_impression_recovery_proxy`

This means the current evaluation remains primarily a final-state harness. It checks what profile state and routing decision the system ends up with after replaying the scenario trace, while also exporting baseline comparisons and a limited set of trajectory metrics.

## False First Impression Recovery Proxy

The current recovery proxy is defined in `iml/metrics.py` and only applies to:

- `false_positive_first_impression`
- `false_negative_first_impression`

The midpoint threshold is `trust = 0.50`.

Recovery is counted as:

- false positive case: `initial_trust > 0.50` and `final_trust < 0.50`
- false negative case: `initial_trust < 0.50` and `final_trust > 0.50`

The aggregate proxy is:

`recovered_relevant_entities / total_relevant_entities`

In the current runner, first-impression trust is taken after the first-impression window defined by `FIRST_IMPRESSION_EVENT_COUNT = 3`, or after the last available event if fewer than three events exist.

## What The Current Evaluation Does Not Yet Measure Well

- Recovery speed. The current proxy only checks whether trust crosses the midpoint by the end, not how long the profile stayed wrong.
- Intermediate trajectory quality. Trajectory metrics v1 now capture a small amount of path information, but they remain limited to simple summaries such as recovery event index, trust span, and contradiction peak rather than a richer trajectory-quality score.
- Calibration. There is no comparison between confidence/unknownness values and any ground-truth correctness target.
- Scenario-level expectations beyond routing and trust flip. For example, there is no explicit assertion that `high_contradiction_actor` should keep contradiction load above a target range.
- Revalidation quality. The runner reports whether revalidation triggered at the final decision point, but it does not score whether that revalidation was useful, timely, or spurious.
- Relative performance. Baseline comparison now exists for naive-summary and full-history scorers, but it is still limited to a small set of aggregate metrics.

## Current Limitations Of The Synthetic Evaluation

- The runner now emits a machine-readable JSON artifact at `artifacts/latest_evaluation.json`, but the export is still intentionally small and tied to the current synthetic evaluation harness.
- The dataset is tiny and hand-authored. It is good for inspection, but weak for coverage.
- Event semantics are narrow. Only a small set of event types map into profile updates.
- The traces are clean and mostly unambiguous. They do not capture noisy sources, missing metadata, or competing evidence reliability regimes.
- Ground truth is implicit in scenario design rather than encoded as explicit per-step labels.
- The runner evaluates only low-stakes routing.
- Current metrics are still final-state heavy even though the runner now exports machine-readable summaries, baseline comparison, trajectories, and limited trajectory metrics.
- `last_revalidated_at` is initialized before replay starts, which is operationally convenient but blurs the distinction between "never revalidated" and "recently revalidated."
- Because the evaluation is synthetic and deterministic, good results here should be treated as a sanity check for the explicit MVP, not as evidence of real-world generalization.
