# Support V1 Evaluation Plan

## Scope

Evaluate `support_v1` at per-ticket decision points using the current path only:

`support case history -> support_v1 event conversion -> generic IML replay -> decay/revalidation -> low-stakes route`

Do not change the engine for the first pass. The goal is to check whether the existing generic signals look operationally sane on repeated support entities.

## What To Measure First

Measure whether the route at each labeled decision point is justified by the visible entity history.

Primary checks:

- route accuracy against the `LABELING_GUIDE.md` route label
- `fast_path` precision, especially on cases with contradiction or stale history
- `deep_path` recall on cases with visible instability, sparse evidence, or wrong-first-impression risk
- wrong-first-impression rate across multi-case entities

Support-specific guardrail counts:

- `contradiction_present` cases routed to `fast_path`
- `profile_too_stale` cases routed to `fast_path`
- clearly cooperative recent histories still routed to `deep_path`

## Per-Entity Outputs That Matter Most

The current router uses profile-wide control signals, so inspect those first.

Most important outputs per entity at the decision timestamp:

- `selected_path`
- `decision_reason`
- `overall_confidence`
- `unknownness`
- `freshness`
- `contradiction_load`

Secondary outputs for diagnosis:

- `trust`
- `cooperativeness`
- `predictability`
- `risk`
- whether final revalidation triggered and why

Interpretation rule:

- if the route looks wrong, check profile-wide control signals before blaming attribute values, because `route_decision()` currently gates on confidence, freshness, contradiction, and unknownness rather than direct `trust` or `risk`

## Encouraging Vs Concerning Behavior

Encouraging:

- recent cooperative or follow-through history produces enough confidence for plausible `fast_path`
- visible contradiction pushes `contradiction_load` high enough to keep the entity on `deep_path`
- long silence or thin history lowers freshness or raises unknownness instead of preserving old confidence
- repeated fulfilled commitments increase trust and predictability without hiding later contradictory evidence
- wrong early impressions are corrected after later ignored-request or contradiction events

Concerning:

- `fast_path` on entities with obvious contradiction, repeated ignored requests, or stale sparse histories
- profiles that stay confident after long inactivity with little recent evidence
- strong early positive cases that keep driving `fast_path` after later support-visible instability
- `deep_path` on dense, recent, low-contradiction histories where the next step is routine and low stakes
- revalidation masking poor state by making stale contradictory entities look healthy too often

## Baseline Comparison

Compare IML against the existing `naive_summary` and `full_history` baselines on the same converted support events and the same decision timestamps.

Use the same evaluation slice for all three methods:

- same `entity_id`
- same visible event history up to the label timestamp
- same low-stakes routing assumption

Compare:

- route agreement with human labels
- `fast_path` precision
- `deep_path` recall
- contradiction-to-`fast_path` failure count
- stale-profile-to-`fast_path` failure count
- wrong-first-impression rate on entities with enough history to observe a correction

Expected comparison shape:

- IML should beat `naive_summary` on stale or interrupted histories because IML applies decay and freshness
- IML should beat both baselines on wrong-first-impression cases because it replays state over time instead of scoring the full history once
- `full_history` may look competitive on dense consistent histories, so differences there matter less than differences on contradiction and inactivity cases

## Practical First Pass

1. Build labeled decision points from the semi-real support slice.
2. For each decision point, replay only the entity history visible at that timestamp.
3. Record IML route, reason, control signals, and secondary attributes.
4. Score the same visible history with `naive_summary` and `full_history`.
5. Review all `fast_path` errors, all contradiction/staleness misses, and a sample of clean `deep_path` cases.
6. Adjust only support mapping, reliability, intensity, or evaluation slicing before considering core-engine changes.
