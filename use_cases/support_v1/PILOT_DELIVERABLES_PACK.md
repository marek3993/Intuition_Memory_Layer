# Support V1 Pilot Deliverables Pack

## What this pack adds

This pack makes the first `support_v1` pilot deliverable concrete. It defines what the client provides, what the `support_v1` team does during the pilot, what the client gets back at the end, what is not included, and what next step is recommended.

## What the client provides

- One bounded support export slice in a supported format, preferably `raw_ingest`.
- Basic field and join context so ids, timestamps, ordering, and relationships can be validated.
- Redaction and privacy requirements for the pilot slice.
- One operational owner who can answer workflow questions and review results.
- A small labeled review set on the pilot slice, or reviewer time to create one.

## What the `support_v1` team does during the pilot

- Validates whether the supplied export fits the current contract and flags blockers early.
- Normalizes the pilot slice into the current `support_v1` flow without core-engine changes.
- Runs the pilot evaluation on the real slice and compares baseline routing with calibrated routing.
- Reviews auditability, redaction safety, joins, and visible-history reconstruction on the scoped slice.
- Prepares a decision-ready handoff package for the client review owner.

## What exact outputs the client gets back

- Export validation result: a clear pass / warning / fail readout on whether the export is usable for the current pilot flow.
- Normalized ingest and evaluation result: one auditable pilot slice in the current `support_v1` schema plus the corresponding evaluation outputs for the scoped review set.
- Calibrated vs baseline comparison: a reviewable comparison showing default `iml`, calibrated `iml`, and the current baselines on the same pilot slice.
- Pilot scorecard: a short scorecard covering decision quality, guardrail misses, review burden, and operator confidence on the pilot slice.
- Decision memo: one recommendation state for the pilot outcome: `proceed`, `proceed with constraints`, `revise and rerun`, or `stop`.
- Recommended next step: a plain recommendation on whether to repeat the pilot, expand the slice, move into a broader paid phase, or stop.
- Pilot package and handoff materials: the summary materials needed for an internal buyer, operator owner, or sponsor to review the pilot result without re-running the analysis.

## What is not included in the first pilot

- Production deployment or unattended live routing.
- Deep integration into the client's ticketing platform.
- Multi-queue, multi-region, or broad historical backfill scope.
- Net-new core-engine work, custom model development, or unrelated system changes.
- SLA-backed operational use without manual review.

## Possible next steps after the pilot

- Repeat the pilot on the same queue with a cleaner export or better label coverage.
- Expand the pilot to a larger slice if the first result is directionally positive.
- Run a second pilot on another supported export modality if the client's natural export requires it.
- Move into a broader paid phase with tighter ROI tracking and operating constraints.
- Stop if export quality, auditability, or routing quality is not strong enough on the real slice.
