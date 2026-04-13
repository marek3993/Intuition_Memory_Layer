# Support V1 Pilot Readiness Decision Brief

## What this brief adds

This brief gives one final decision-facing answer on whether `support_v1` is ready to seek a first real external pilot export now, and under what constraints.

## Current Evidence Snapshot

- Current evidence is directionally strong across all implemented `support_v1` modalities.
- Calibrated `iml` beats the best baseline on the largest evaluated slice in 5 of 5 modalities.
- Evaluation evidence exists across labeled support, raw ingest, CSV ingest, mapped ingest, and Zendesk-like ingest, while the top-level system summary still flags `mapped_ingest` as the remaining gap in one consolidated ingest snapshot.
- Contract validation passes on the current bundled raw JSON, flat CSV, and Zendesk-like JSON samples with 0 warnings and 0 errors.
- Pilot packaging and handoff readiness are in place: 5 of 5 pilot packages exist, and bundle validation reports 11 PASS, 0 FAIL.
- One real pilot workspace is already validated as PASS for `raw_ingest`.

## What Is Already Pilot-Ready

- The team can start a first external pilot conversation now without changing the core engine.
- The current workflow already supports bounded intake, contract validation, normalization, labeled evaluation, review CSV output, pilot packaging, and operator handoff.
- The first pilot can be run with existing runbooks, onboarding checklists, scorecards, and decision templates already in the repo.
- `raw_ingest` is the strongest starting path because it has the strongest current evidence and the only validated real pilot workspace.

## What Is Still Thin Or Risky

- Current evidence is still based on bundled sample exports rather than a real external export.
- Ingest evidence is still small-sample outside the labeled support pack comparison: raw and CSV largest slices are 13 labels, mapped is 11, and Zendesk-like is 9.
- Zendesk-like remains the thinnest evaluated path, and mapped ingest has the smallest lead over the best baseline.
- Real-world risk is still unproven on redaction quality, join completeness, timestamp quality, and auditability on a partner export.
- This is pilot readiness for external export intake, not production readiness.

## Constraints For The First Pilot

- Keep the first pilot to one external partner, one queue, one export modality, and one review owner.
- Start with one small redacted and auditable export slice, not a broad backfill.
- Prefer `raw_ingest` first. Use CSV, mapped CSV, or Zendesk-like only if that is the partner's natural export and the slice passes the current contract gate cleanly.
- Require contract validation, normalization auditability, and visible-history label review before any pilot decision is treated as credible.
- Keep human review and manual override in place for the full first pilot.
- Treat any join gaps, unsafe redaction, unstable ordering, or guardrail misses as stop-and-review conditions.

## Final Recommendation

**Recommendation state: ready for first pilot outreach with constraints**

Seek the first real external pilot export now, but keep the ask narrow. The right first move is a small redacted export on one supported modality, preferably `raw_ingest`, with manual review, explicit stop conditions, and no claim that `support_v1` is ready for broader rollout until real-slice evidence exists.
