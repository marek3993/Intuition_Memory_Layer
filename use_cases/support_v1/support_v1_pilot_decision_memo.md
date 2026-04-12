# Support V1 Pilot Decision Memo

## What this pack adds

This pack adds one concise post-pilot decision memo for `support_v1`. It gives operators and decision owners one place to combine the pilot scorecard, measured ROI inputs, pilot handoff evidence, and readiness position before choosing one recommendation state: `proceed`, `proceed with constraints`, `revise and rerun`, or `stop`.

## Pilot Scope

- Define the exact queue, export slice, pilot window, and review owner.
- Keep the comparison on the same queue and the same baseline process used before `support_v1`.
- Record the export modality used in the pilot: raw JSON, Zendesk-like JSON, fixed-contract CSV, or mapped CSV.
- Note whether the slice passed contract validation and stayed auditable end to end without core-engine changes.

## What Was Measured

- Pilot scorecard decision metrics: `fast_path` precision, `deep_path` recall, and contradiction / stale guardrail misses.
- Pilot scorecard diagnostic metrics: unnecessary deep-path volume, review time / escalation burden, and analyst / operator confidence in the selected route.
- ROI model inputs updated with measured queue data where available: minutes saved, review-load change, senior-review change, and any measured escalation or rework effect.
- Handoff and readiness checks: export quality, normalization stability, redaction safety, and whether the pilot team could explain where calibrated `iml` helped or stayed mixed.

## Key Results

- Summarize the pilot volume reviewed, the baseline used, and the highest-signal scorecard results.
- State whether calibrated `iml` held or improved the decision metrics that mattered on the live slice.
- Separate measured operational changes from directional observations. Do not treat assumptions as results.
- Call out any result that depended on a small sample or incomplete labeling coverage.

## Where Support V1 Beat Baseline

- Record the specific routing decisions, queue segments, or review steps where `support_v1` improved on the current baseline.
- Prioritize concrete wins: higher `fast_path` precision, stronger `deep_path` recall, lower unnecessary deep-path volume, lower review time, fewer avoidable escalations, or better reviewer confidence.
- Tie each win to evidence already used elsewhere in the pack: scorecard metrics, review CSV findings, or measured ROI inputs.

## Where It Failed or Stayed Mixed

- Record any queue segment where `support_v1` missed baseline, tied baseline without clear operational value, or created extra review burden.
- Call out repeated guardrail misses, unclear route decisions, or cases where reviewers could not defend the selected route.
- Distinguish between fixable pilot issues such as weak labeling coverage or export quality gaps and route-behavior problems that changed the outcome materially.

## Operational Impact Observed

- State the observed effect on reviewer minutes, handoffs, escalation burden, override rate, and confidence in day-to-day use.
- Keep the operational readout grounded in the pilot slice only. Do not extrapolate to full deployment without measured queue data.
- Note whether the pilot reduced deep-path load on clean routine work without allowing risky, stale, or contradictory cases onto `fast_path`.

## Risk Summary

- Summarize the main decision risks in plain terms: small sample size, export quality gaps, labeling gaps, guardrail misses, or unstable performance by slice.
- Note any modality-specific weakness already visible in current readiness evidence, especially when the pilot did not materially expand that evidence base.
- Mark any risk that requires a rollout constraint, a pilot design revision, or a stop decision.

## Final Recommendation

- Choose exactly one state: `proceed`, `proceed with constraints`, `revise and rerun`, or `stop`.
- Use `proceed` when `support_v1` beats or clearly holds baseline on the decision metrics that matter, guardrail misses are absent or rare and explainable, operational burden is flat or lower, and measured ROI is directionally positive.
- Use `proceed with constraints` when the pilot is directionally positive but still needs bounded rollout controls such as queue limits, daily review, mandatory overrides review, or export-type restrictions.
- Use `revise and rerun` when the result is mixed but fixable through a tighter slice, better labels, cleaner export data, or a clearer operating constraint before another pilot pass.
- Use `stop` when `support_v1` misses baseline on key decision metrics, creates material operational burden, or shows unresolved risk on guardrail-sensitive cases.
