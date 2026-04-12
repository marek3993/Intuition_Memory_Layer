# Architecture Overview

## What the system does

The current MVP is an explicit decision-memory layer for one entity at a time. It converts timestamped observations into a compact `IntuitionProfile`, lets that profile decay as evidence becomes stale, optionally applies a heuristic revalidation step, and then routes a low-stakes decision to either `fast_path` or `deep_path`.

The implementation is deliberately small and inspectable. There is no learned model, no vector store, and no generated summary state in the IML path.

## Core objects and modules

`Event` (`iml/models.py`)

- Canonical input record for the MVP.
- Carries `event_id`, `entity_id`, `timestamp`, `event_type`, `source`, `reliability`, `polarity`, `intensity`, and `metadata`.
- In the IML update path, `event_type`, `reliability`, `intensity`, and `timestamp` are the main drivers. `polarity` is primarily used by the baseline scorers.

`EvidenceUnit` (`iml/models.py`)

- Small explicit update produced from an event.
- Contains `attribute`, `delta`, `confidence_delta`, and `reason`.
- `iml/extractor.py` maps each supported `event_type` into one or more `EvidenceUnit`s and scales them by event reliability and intensity.

`IntuitionProfile` (`iml/models.py`)

- Persistent state for one entity across events.
- Holds five attribute states: `trust`, `stability`, `predictability`, `cooperativeness`, and `risk`.
- Also holds profile-wide control signals: `overall_confidence`, `contradiction_load`, `unknownness`, `freshness`, `created_at`, `updated_at`, and `last_revalidated_at`.
- Each attribute state tracks current `value`, current `confidence`, evidence counts, and `last_changed_at`.

Core modules in the running MVP:

- `iml/extractor.py`: event-type to evidence mapping.
- `iml/update_engine.py`: applies extracted evidence to the profile and recomputes aggregate state.
- `iml/decay.py`: reduces freshness and attribute confidence over elapsed time and increases unknownness.
- `iml/revalidate.py`: applies a heuristic repair step when the profile looks stale or unreliable.
- `iml/decision.py`: routes to `fast_path` or `deep_path`.
- `iml/baselines.py`: two non-IML comparison scorers used only in evaluation.
- `iml/metrics.py`: per-entity and aggregate evaluation metrics.
- `run_evaluation.py`: synthetic evaluation runner over `datasets/synthetic_entities.json`.

## End-to-end flow

1. `run_evaluation.py` loads synthetic entities and sorts each entity's events by timestamp.
2. It creates a fresh `IntuitionProfile` with default attribute values of `0.50`, default attribute confidence of `0.20`, `overall_confidence=0.20`, `unknownness=0.80`, and `freshness=1.00`.
3. Before each event, it applies decay if the gap since `profile.updated_at` is at least 21 days.
4. `apply_event()` calls `extract_evidence()` and applies each resulting `EvidenceUnit` to the matching attribute state.
5. `apply_event()` then updates profile-wide state:
   - `contradiction_load` increases on `contradiction_detected`, otherwise it decays by a factor of `0.97`
   - `overall_confidence` becomes the mean attribute confidence
   - `unknownness` becomes `1.0 - overall_confidence`
   - `freshness` resets to `1.0`
   - `updated_at` becomes the event timestamp
6. After all events, the runner applies one final 7-day decay, runs revalidation, and routes a low-stakes decision.
7. The runner prints one entity summary, then aggregate metrics, then a baseline comparison block.

## Routing logic

`iml/decision.py` sends a decision to `fast_path` only when all of the following are true:

- `overall_confidence >= 0.55`
- `freshness >= 0.60`
- `contradiction_load <= 0.35`
- `unknownness <= 0.45`
- stakes are not `high`

Otherwise it returns `deep_path` and lists the threshold failures in the reason string.

The IML router does not currently inspect attribute values directly. In particular, `risk` is part of the profile but is not used by `route_decision()`.

## Revalidation role

`iml/revalidate.py` is a small heuristic adjustment pass. It triggers when any of these conditions hold:

- `freshness < 0.50`
- `overall_confidence < 0.40`
- `contradiction_load > 0.30`
- `unknownness > 0.60`
- more than 30 days have elapsed since `updated_at`

When triggered, it:

- reduces `contradiction_load` by `0.08`
- increases `freshness` by `0.18`, capped at `0.70`
- increases `overall_confidence` by `0.08` only if contradiction load ends up at or below the threshold
- reduces `unknownness` by `0.10`
- updates `last_revalidated_at`

This is not a re-read of source evidence. It is a bounded heuristic recovery step applied to the current profile state.

## Baseline comparison role

The evaluation runner computes two comparison baselines before replaying the IML profile:

`naive summary baseline`

- Stateless heuristic over coarse event counts and ratios.
- Uses simple aggregates such as positive vs negative event counts, contradiction ratio, ignored-request ratio, inactivity ratio, average reliability, and whether the last event was negative or inactive.
- Produces scalar outputs like `trust`, `risk`, `overall_confidence`, `unknownness`, `contradiction_load`, then routes through a baseline-specific threshold function.

`full-history baseline`

- Also stateless, but uses weighted totals over the full event history.
- Weights each event by `reliability * intensity` and separates positive, negative, contradiction, ignored-request, and inactivity pressure.
- Produces the same output shape as the naive summary baseline, then routes through the same baseline threshold function.

Difference in lifecycle:

- The IML profile lifecycle is stateful and time-aware: initialize profile, update per event, decay across gaps, apply final decay, optionally revalidate, then route.
- The naive summary baseline is a one-shot scorer over the event list. It does not maintain profile state, decay between events, or revalidate.
- The full-history baseline is also a one-shot scorer, but it preserves more signal than the naive summary by weighting all events instead of collapsing to coarse ratios.

## Current design constraints

- Event semantics are hand-authored for five event types: `fulfilled_commitment`, `cooperative_response`, `ignored_request`, `contradiction_detected`, and `long_inactivity`.
- The update path is attribute-local and additive. There is no learned weighting, cross-attribute inference, or uncertainty model beyond explicit heuristics.
- `overall_confidence` is just the mean attribute confidence; `unknownness` is derived from it in the update path and increased further by decay.
- Decay changes freshness and confidence but does not change attribute values.
- Revalidation is heuristic and state-based. It does not inspect raw history again.
- The evaluation runner only evaluates low-stakes routing and prints human-readable output to stdout.
- Several modules exist but are not part of the running MVP path yet: `iml/profile.py`, `iml/contradiction.py`, `iml/event_log.py`, and `iml/fact_store.py` are currently empty.

## What is intentionally not in scope yet

- Learned extraction, learned routing, or any trained memory model.
- Free-form summary memory as part of the IML state.
- Real data ingestion, persistence, multi-entity services, APIs, or background workers.
- Rich event schemas beyond the current synthetic vocabulary.
- Machine-readable evaluation artifacts or benchmark-grade reporting.
- Ground-truth calibration, recovery-speed metrics, or a large scenario suite.
- Production policies for conflict resolution, source trust management, or profile versioning.
