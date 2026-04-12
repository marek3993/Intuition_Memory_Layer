# Support V1 ROI Model

## What this pack adds

This pack adds one simple fill-in ROI model for `support_v1`. It turns the current routing-improvement story into a buyer or pilot conversation artifact without claiming production-scale certainty.

## Evidence boundary to keep in mind

- Current evidence is directionally positive: calibrated `iml` improves on default `iml` in 18 of 19 loaded slices and in 13 of 14 slices in the unified ingest comparison.
- The strongest current result is raw-ingest `combined_ab`: calibrated `iml` at 92.31% versus 69.23% for the best non-calibrated method.
- The evidence is still small-sample. The largest current slices range from 9 to 30 labels depending on modality, and no real customer export is in the evidence set yet.

Use this model as a pilot estimate, not as a committed business case.

## Operational variables that matter

- Monthly case volume in scope for routing.
- Share of clean routine cases that could stay on a faster path.
- Current rate of unnecessary deep-path review on clean routine cases.
- Minutes spent on a routine case today versus with a cleaner fast path.
- Share of deep-path reviews that require senior reviewer time.
- Escalation, reopen, or rework rate tied to routing misses.
- Fully loaded hourly cost for frontline and senior reviewers.
- Pilot setup cost and pilot duration.

## Where `support_v1` can create value

- Fewer clean routine cases sent to deep review when calibrated routing is confident enough to keep them on the fast path.
- Faster handling of routine cases that still need review but do not need the full deep-path workflow.
- Lower senior-review load when fewer low-risk cases reach the specialist queue.
- Lower escalation or rework burden when routing is cleaner on the first pass.

## Simple formula structure

Define monthly case volume as `cases_per_month`.

1. Fewer unnecessary deep-path reviews

`value_deep_review_avoidance = cases_per_month x clean_routine_share x unnecessary_deep_review_rate x avoidable_deep_review_reduction x deep_review_minutes_saved_per_case x frontline_hourly_cost / 60`

2. Faster handling of clean routine cases

`value_faster_routine_handling = cases_per_month x clean_routine_share x fast_path_minutes_saved_per_case x frontline_hourly_cost / 60`

3. Reduced senior-review load

`value_senior_load_reduction = cases_per_month x deep_path_share x senior_review_share x senior_review_reduction x senior_review_minutes_saved_per_case x senior_hourly_cost / 60`

4. Lower escalation or rework burden

`value_rework_reduction = cases_per_month x escalation_or_rework_rate x escalation_or_rework_reduction x rework_minutes_saved_per_case x blended_hourly_cost / 60`

5. Total estimated monthly value

`total_monthly_value = value_deep_review_avoidance + value_faster_routine_handling + value_senior_load_reduction + value_rework_reduction`

6. Pilot-period value and simple ROI

`pilot_period_value = total_monthly_value x pilot_months`

`net_pilot_value = pilot_period_value - pilot_setup_cost`

`pilot_roi = net_pilot_value / pilot_setup_cost`

## Practical assumptions

- Start with one export slice and one queue, not the full support operation.
- Use observed queue metrics if available; otherwise use conservative estimates from team leads.
- Keep value assumptions separate from the current calibration evidence. The evidence supports trying the routing approach; it does not yet prove a stable production lift.
- If you do not have measured rework or escalation data, set that component to zero rather than guessing aggressively.
- If you do not have a reliable senior-review cost, use minutes saved first and translate to money second.

## Caution on current dataset size

The current calibrated-versus-default results are useful for pilot positioning, but the evidence base is still too small to justify an aggressive rollout claim. The ROI model should therefore be used in three steps:

- estimate value conservatively
- run one real redacted export pilot
- replace assumptions with measured queue data before using the model in a larger buying decision
