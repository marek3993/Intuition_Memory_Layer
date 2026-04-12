# Support V1 Pilot Scorecard

## What this pack adds

This pack adds one simple scorecard for the first real `support_v1` pilot so the team can judge whether routing is creating operational value on a real export slice without changing the core engine.

Use it alongside the existing labeled evaluation artifact, review CSV, pilot handoff pack, onboarding checklist, and ROI model.

## What to measure during the pilot

Track one small real slice against the current baseline on the same queue.

### Decision metrics

- `fast_path` precision: of the cases routed to `fast_path`, how many were judged correct on review.
- `deep_path` recall: of the cases that should have gone to `deep_path`, how many were actually routed there.
- contradiction / stale guardrail misses: count any `contradiction_present` or `profile_too_stale` case that still lands on `fast_path`.

These decide whether the pilot is safe enough to continue.

### Diagnostic metrics

- unnecessary deep-path volume: count or share of clean routine cases that still go to `deep_path` with no clear guardrail reason.
- review time / escalation burden: reviewer minutes, extra handoffs, or escalations created because the route was unclear or had to be overridden.
- analyst / operator confidence in the route: whether the reviewer can quickly explain and defend why a case went `fast_path` or `deep_path`.

These explain where value is or is not showing up.

## Recommended review cadence

- Daily for week 1: review all guardrail misses, all routed `fast_path` errors, and a small sample of clean `deep_path` cases.
- Twice weekly after week 1: update the scorecard, compare against baseline, and decide whether to hold, revise, or expand the slice.
- End of pilot: update the ROI model only with measured queue data, not with assumptions.

## Good early signal

- `fast_path` precision is at or above the current baseline and stays high on reviewed pilot cases.
- `deep_path` recall stays strong enough that risky, stale, or contradictory cases are still reaching `deep_path`.
- contradiction / stale guardrail misses are zero or rare enough to explain as labeling or data-quality issues, not route behavior.
- unnecessary deep-path volume drops on clean routine work without raising escalations or rework.
- review time stays flat or improves.
- analyst / operator confidence trends upward and route overrides stay limited.

## Stop / revise signal

- repeated `contradiction_present` or `profile_too_stale` cases are routed to `fast_path`.
- `fast_path` precision falls below baseline or shows a clear downward trend.
- `deep_path` recall weakens enough that obvious risky cases are being missed.
- unnecessary deep-path volume stays high, so the pilot adds review cost without reducing burden.
- review time, handoffs, or escalations rise materially.
- reviewers do not trust or cannot explain the selected route.

## Practical use notes

- Use the current route names only: `fast_path` and `deep_path`.
- Use the current guardrail flags only: `contradiction_present`, `profile_too_stale`, and `wrong_first_impression`.
- Pull decision-quality numbers from the matching label evaluation JSON and review CSV for the pilot slice.
- Pull burden and confidence measures from pilot operations review, not from model outputs alone.
- Treat this as a pilot decision tool, not a production rollout claim.
