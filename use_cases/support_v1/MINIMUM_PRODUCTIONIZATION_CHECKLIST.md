# Support V1 Minimum Productionization Checklist

## What this checklist adds

This adds one short gap-aware checklist for the step after prototype and pilot work: what still has to be true before `support_v1` can be treated as a real production candidate.

This is not a production-readiness claim. It is a minimum gate against moving forward on sample-only evidence.

## Data / export readiness

- [ ] At least one real helpdesk export slice passes the current export contract validation without schema patching or missing-link exceptions.
- [ ] The initial production-bound ingest path is fixed up front: raw JSON, fixed-contract CSV, mapped CSV, or Zendesk-like JSON.
- [ ] The chosen real export has trustworthy entity, ticket, record, and timestamp fields strong enough to rebuild deterministic history order.
- [ ] Normalized output for the real slice is auditable back to source rows or records.
- [ ] The selected launch slice does not depend on fields or structures that only exist in bundled sample exports.

## Labeling / truth-set readiness

- [ ] A real-slice truth set exists; readiness is not based only on bundled sample label packs.
- [ ] Every labeled decision is anchored to the visible `decision_timestamp`, not to the eventual ticket outcome.
- [ ] The truth set includes routine cases, stale-history cases, contradiction cases, and at least some wrong-first-impression cases.
- [ ] Label justifications are short but reviewable enough to defend why a case should route to `fast_path` or `deep_path`.
- [ ] Label coverage is large enough to expose failure patterns on the actual launch modality, not just show isolated wins.

## Evaluation / benchmark readiness

- [ ] The chosen real slice has been run through the current labeled evaluation flow end to end.
- [ ] The same slice has been compared against `iml`, calibrated `iml`, `naive_summary`, and `full_history`.
- [ ] Readiness review includes the case-level review CSVs, not only top-line accuracy.
- [ ] Wins and losses on the real slice are explainable from visible history, not just from aggregate metrics.
- [ ] The weakest result on the intended launch path is understood well enough to describe the operational risk it creates.

## Calibration readiness

- [ ] Calibrated `iml` is at least not worse than default `iml` on the real truth set chosen for launch review.
- [ ] Any calibration gain is traceable to support-history patterns rather than export-mapping errors, timeline defects, or label leakage.
- [ ] The team can explain when calibration changes a route and when it should not.
- [ ] The launch decision does not depend on moving support-specific calibration logic into the generic core engine.

## Safety / guardrail readiness

- [ ] Every `contradiction_present` case that routes to `fast_path` has been reviewed and either fixed or accepted as a known launch constraint.
- [ ] Every `profile_too_stale` case that routes to `fast_path` has been reviewed and dispositioned before rollout.
- [ ] Wrong-first-impression cases have been checked to confirm later contradictory history can still push the route back to `deep_path`.
- [ ] Clean routine cases are not being sent to `deep_path` so often that the launch would create obvious review burden without safety benefit.
- [ ] No unresolved safety concern is being dismissed as a sample artifact without evidence from the real slice.

## Operational integration readiness

- [ ] One named owner is accountable for export intake, evaluation review, and rollout decisions on the initial queue.
- [ ] The selected ingest path has been run as an end-to-end operational rehearsal on a real slice, not only as a prototype command demo.
- [ ] Reviewers know how to inspect the route reason, confidence, freshness, unknownness, and contradiction signals when a case looks wrong.
- [ ] There is a defined manual override path for any case where the route looks unsafe or unjustified.
- [ ] Export failures, missing joins, and bad timestamps have an explicit stop-and-review path rather than ad hoc correction during rollout.

## Privacy / redaction readiness

- [ ] Real exports are redacted before entering the repo workspace.
- [ ] Stable surrogate IDs survive redaction so entity, ticket, and record linkage still works after sanitization.
- [ ] Free-text content kept for labeling or review is limited to what the current workflow actually needs.
- [ ] Review artifacts, label files, and memo outputs have been checked for accidental reintroduction of customer identifiers.
- [ ] If a useful launch slice cannot be evaluated safely after redaction, the slice is not production-candidate ready.

## Rollout readiness

- [ ] The first rollout target is bounded to one queue, one export modality, and one review owner.
- [ ] Initial rollout keeps human review and override in place rather than treating `support_v1` as fully autonomous.
- [ ] The pilot scorecard metrics for the launch slice are defined before rollout starts.
- [ ] Stop, rollback, or hold conditions are written down before the first production-candidate exposure.
- [ ] The rollout recommendation is framed as `production candidate with constraints` until real-slice evidence expands beyond the first bounded launch.
