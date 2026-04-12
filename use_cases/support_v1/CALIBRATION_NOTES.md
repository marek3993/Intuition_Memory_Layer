# Support V1 Calibration Notes

The current labeled result means the `support_v1` replay is directionally separating risky support histories, but it is not yet calibrated to let clean routine cases reach `fast_path`. In the current artifact, IML is `5/8` correct: all three `fast_path` labels miss as `deep_path`, while all flagged `contradiction_present`, `profile_too_stale`, and `wrong_first_impression` labels route correctly to `deep_path`.

That pattern points to over-conservatism rather than missing guardrails. The current failures are not unsafe promotions of stale or contradictory histories. They are one-sided false negatives caused mainly by `overall_confidence` staying below `0.55` and `unknownness` staying above `0.45` even when the visible history is recent, cooperative, and internally clean.

Safe calibration to test first:

- make recent cooperative histories accumulate confidence faster from `cooperative_response` and `fulfilled_commitment`
- reduce `unknownness` more effectively when the visible history is small but clean and recent
- tune revalidation so it improves weak-but-clean profiles without manufacturing confidence for stale or contradictory ones
- add metrics that separate `fast_path` false negatives from true guardrail misses before changing core policy

Do not change too early:

- contradiction and staleness protections
- penalties tied to `contradiction_detected`, `ignored_request`, and inactivity decay
- the requirement that risky or sparse histories stay on `deep_path`
- route-threshold changes made globally before confirming the issue is support-specific confidence calibration rather than event-mapping loss
