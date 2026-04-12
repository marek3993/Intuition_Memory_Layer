# Support V1 Evaluation Notes

## What `support_v1` currently measures

The current sample evaluation is a per-entity replay sanity check, not a labeled accuracy benchmark.

It measures whether support case history converts into the existing generic IML event vocabulary and produces plausible final profile state after:

- support case -> event conversion
- event replay through `apply_event()`
- decay on gaps of 21+ days
- one final 5-day decay gap
- final revalidation
- final low-stakes routing

Per entity, the runner reports:

- case count and derived event count
- event mix by generic event type
- final route and route reason
- final attribute values: `trust`, `cooperativeness`, `predictability`, `risk`
- final control signals: `overall_confidence`, `unknownness`, `freshness`, `contradiction_load`
- whether revalidation triggered and why

## What the current outputs mean

`selected_path` is the generic router output:

- `fast_path` means all current low-stakes gates passed
- `deep_path` means one or more gates failed

The current gates are:

- `overall_confidence >= 0.55`
- `freshness >= 0.60`
- `contradiction_load <= 0.35`
- `unknownness <= 0.45`
- stakes not high

`decision_reason` lists the failed gate(s).

The attribute outputs are support-visible behavior summaries after replay:

- `trust`: follow-through vs missed follow-through
- `cooperativeness`: helpful response vs ignored requests
- `predictability`: consistency vs contradiction
- `risk`: support-visible instability or contradiction risk

The profile-wide control signals matter most for routing:

- `overall_confidence`: mean attribute confidence
- `unknownness`: inverse of confidence in the current engine
- `freshness`: recency after decay
- `contradiction_load`: contradiction pressure accumulated outside the attribute states

`revalidation_triggered` means the generic heuristic repair step ran after the final decay gap. It can slightly improve freshness/confidence and reduce unknownness/contradiction, but it does not change the underlying support evidence.

## Good sign vs worrying sign

Good signs:

- clearly cooperative entities end with higher `trust`, `cooperativeness`, and `predictability` than contradiction-heavy entities
- contradiction-heavy entities show meaningfully higher `risk` and `contradiction_load`
- long gaps and silence reduce freshness or keep routing conservative
- `decision_reason` matches the obvious failure mode in the visible history

Worrying signs:

- clean entities and problematic entities collapse to nearly the same route for the same reason
- contradiction-heavy histories do not separate from cooperative histories on `risk` or `contradiction_load`
- stale or silence-heavy histories retain strong confidence
- revalidation makes weak profiles look healthy without new evidence

In the current sample, the main warning sign is that all entities still route to `deep_path`, mostly because generic confidence remains too low and unknownness stays too high even for clean histories.

## Current limitations

- The sample is very small and hand-authored.
- The runner evaluates only the final per-entity state after all cases, not per-ticket decision points.
- There are no route labels in this sample run, so it does not measure accuracy, precision, or recall.
- The support runner does not compare against baselines or export a richer artifact.
- The adapter maps only a narrow set of operational fields into generic events.
- The result is currently dominated by generic engine confidence/unknownness behavior, so it is hard to tell whether failures come from support mapping or core thresholds.

## Next validation step

Build a labeled per-decision-point support slice and replay only the history visible at each ticket decision timestamp.

That next pass should measure route accuracy, `fast_path` precision, `deep_path` recall, and guardrail failures such as contradiction-present or stale histories reaching `fast_path`.

Do that before changing the engine. If the labeled pass still shows systematic misses, adjust support event mapping or confidence calibration first, then revisit core routing thresholds.
