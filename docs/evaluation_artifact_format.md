# Evaluation Artifact Format

This document describes the current export contract for the `run_evaluation.py` runner. The runner writes a machine-readable JSON artifact to `artifacts/latest_evaluation.json` alongside the console summary.

The intent is simple: the JSON artifact mirrors the runner's evaluation output in a form that is easy to inspect across runs, diff in tooling, and consume in lightweight analysis scripts. It is not intended to be a versioned schema system or a general-purpose benchmark format.

## Format Goals

- keep the export close to the current runner output
- make aggregate and per-entity results easy to inspect programmatically
- preserve enough trajectory detail to support run-to-run comparison and trajectory-derived metrics

## Top-Level Sections

The current export contains these top-level keys:

- `run_metadata`
- `aggregate_metrics`
- `baseline_comparison`
- `entity_summaries`
- `entity_trajectories`
- `trajectory_metrics`

## `run_metadata`

Run-level metadata identifies what was evaluated and under which runner settings.

Expected contents include:

- dataset path or dataset identifier
- stakes used for evaluation
- decay gap configuration
- final decision gap configuration
- export path
- runner timestamp

This section should make it possible to tell whether two artifacts are directly comparable without inspecting the code path that produced them.

## `aggregate_metrics`

Aggregate metrics summarize the full evaluation run.

This section is expected to mirror the aggregate console block and may include values such as:

- entity count
- total events replayed
- decay checkpoints applied
- revalidations triggered
- `fast_path` count
- `deep_path` count
- average `overall_confidence`
- average `unknownness`
- false-first-impression recovery proxy

## `baseline_comparison`

Baseline comparison is exported as a list of per-method aggregate summaries.

The current export includes entries for:

- `IML`
- `naive_summary`
- `full_history`

Each entry contains:

- method name
- `fast_path` count
- `deep_path` count
- average `overall_confidence`
- average `unknownness`

## `entity_summaries`

Entity summaries provide one compact record per evaluated entity.

Expected contents include:

- entity identifier
- scenario name
- event count
- decay checkpoint count
- first-impression event index
- final decision gap
- final trust and first-impression trust
- final `overall_confidence`
- final `unknownness`
- final `freshness`
- final `contradiction_load`
- revalidation triggered flag
- revalidation reasons
- `iml` decision fields
- `naive_summary` baseline summary
- `full_history` baseline summary

This section is the machine-readable counterpart to the current per-entity console summaries.

## `entity_trajectories`

Entity trajectories capture the stepwise state history recorded during event replay.

Each entity trajectory record contains:

- entity identifier
- scenario
- `trajectory`

`trajectory` is an ordered list of per-event checkpoints. Each checkpoint currently includes:

- event index
- event identifier
- event type
- timestamp
- trust
- `overall_confidence`
- `unknownness`
- `freshness`
- `contradiction_load`

The purpose of this section is inspection of replayed state changes, not full profile serialization.

## `trajectory_metrics`

Trajectory metrics summarize behavior that depends on the path taken, not only the final state.

The current export contains:

- `aggregate`
- `per_entity`

The aggregate block currently includes:

- average trust trajectory span
- average contradiction peak
- recoverable entity count
- recovered entity count
- average recovery event index

The per-entity block currently includes:

- entity identifier
- scenario
- first-impression event index
- recovery event index
- trust trajectory span
- contradiction peak

## Notes

- The console summary remains the human-readable output surface for the runner.
- The JSON artifact should be a direct export of evaluation results, not a second source of evaluation logic.
- When the runner adds new fields, prefer additive changes inside the existing sections over structural churn.
