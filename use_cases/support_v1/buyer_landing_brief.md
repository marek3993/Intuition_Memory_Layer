# Support V1 Buyer Landing Brief

## What this adds

This brief gives a short buyer-facing explanation of what `support_v1` is, where it can help, what is already proven internally, and what a first pilot would require.

## What problem `support_v1` solves

Support teams often need to decide which cases can stay on a fast path and which should move to deeper review, but that decision is often made against messy exports, incomplete ticket history, and inconsistent manual triage. `support_v1` is designed to make that routing decision more reliable on a bounded helpdesk export without asking the buyer to fund a core-engine rewrite first.

## How it works at a high level

`support_v1` takes one scoped support export, checks whether the data has the ids, joins, timestamps, ordering, and text detail needed for the current flow, reconstructs the visible case history, and produces a reviewable routing comparison on that slice.

## What is already proven internally

- Prototype ingest paths already exist for raw JSON, flat CSV, mapped CSV, and Zendesk-like nested exports.
- Contract validation already passes on the current bundled raw JSON, flat CSV, and Zendesk-like samples with 0 warnings and 0 errors.
- Existing evaluation runs show calibrated `iml` beating the best non-calibrated method on the largest evaluated slice in 5 of 5 implemented modalities.
- The strongest current result is `raw_ingest` on `combined_ab`: calibrated `iml` at 92.31% versus 69.23% for the best non-calibrated baseline.
- Pilot packaging, handoff materials, and one validated real pilot workspace already exist.

## What a first pilot looks like

- One buyer, one queue or workflow, and one supported export modality.
- One small redacted and auditable export slice, not a broad historical backfill.
- Manual review and override kept in place for the full pilot.
- One labeled review pass on the real slice so the routing result can be checked against visible history.

## What you would need to provide

- One bounded export sample in a supported format.
- Basic field and join context so ids, timestamps, ordering, and relationships can be validated.
- Redaction and privacy requirements for the pilot slice.
- One operational owner who can review outputs and confirm whether the result is usable.
- A small labeled review set, or reviewer time to create one on the pilot slice.

## What you get back

- A contract-validation readout on your export.
- A normalized and auditable pilot slice in the current `support_v1` flow.
- A reviewable routing comparison against the current baselines on your slice.
- A short handoff summary with findings, risks, and a recommendation to stop, repeat, or expand.

## Current constraints

- This is ready for a first pilot, not for broad production rollout.
- Most current evidence still comes from bundled sample exports and small labeled slices rather than a live customer evidence base.
- `raw_ingest` is the strongest starting path today; other modalities are possible but have thinner evidence.
- Human review should stay in place for the first pilot.
- Join gaps, unsafe redaction, unstable ordering, or guardrail misses should be treated as stop-and-review conditions.
