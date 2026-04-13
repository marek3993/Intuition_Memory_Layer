# Support V1 Commercial Pilot One-Pager

## What this adds

This one-pager turns the current Support V1 readiness work into a short commercial pilot artifact for someone deciding whether to approve a first trial.

## What problem Support V1 solves

Support teams often have to decide which cases can stay on a fast path and which need a deeper review path, but that decision is slowed down by messy export data, incomplete case-history reconstruction, and inconsistent manual triage. Support V1 is designed to take a bounded helpdesk export, reconstruct visible ticket history, and support a more reliable routing decision without requiring a core-engine rewrite.

## What is already built

- Prototype export paths for raw JSON, flat CSV, mapping-based CSV, and Zendesk-like nested exports.
- A contract validator that checks whether an export has the ids, joins, timestamps, ordering, and detail fields required for the current flow.
- Normalization and evaluation runners that compare standard routing, calibrated routing, and current comparison methods on the same labeled decision points.
- Pilot deliverables, handoff materials, onboarding, and workspace materials for a first bounded external pilot.

## What evidence exists so far

- Current evidence is directionally strong across the implemented Support V1 export formats.
- On the largest slice in each loaded format, calibrated routing beats the best non-calibrated comparison method in 5 of 5 formats.
- The strongest current result is on the raw JSON export path: calibrated routing reaches 92.31% versus 69.23% for the best non-calibrated comparison method.
- Contract validation passes on the current bundled raw JSON, flat CSV, and Zendesk-like JSON samples with 0 warnings and 0 errors.
- Pilot deliverables, handoff materials, and one validated real pilot workspace already exist.

## What the first pilot would look like

- One customer or partner.
- One queue or workflow in scope.
- One export format, preferably the raw JSON export path unless another format is the customer's natural export.
- One small, redacted, auditable export slice rather than a broad backfill.
- Human review and manual override kept in place for the full pilot.
- One first labeled review pass on the real slice so routing quality can be checked against actual visible history.

## What the customer or team would need to provide

- One bounded export sample in a supported format.
- Basic field and join context so ids, timestamps, ordering, and relationships can be validated.
- Redaction and privacy requirements for the pilot slice.
- One operational owner who can review the slice and confirm whether the routing output is usable.
- A small labeled review set on the real slice for pilot evaluation.

## What deliverables they would get back

- A contract-validation readout on the supplied export.
- A normalized and auditable pilot slice in the current Support V1 workflow.
- A reviewable comparison artifact showing calibrated routing against the current comparison methods on the pilot slice.
- Pilot handoff materials that make the result easier to review operationally.
- A practical recommendation on whether the slice supports expanding, repeating, or stopping the pilot.

## What success would look like

- The export passes contract validation and can be normalized without custom engine changes.
- The pilot slice is auditable end to end for joins, ordering, and redaction safety.
- The first labeled evaluation run completes on the real slice and produces a reviewable routing comparison.
- The team can show that calibrated routing is useful enough on the pilot slice to justify a second, broader trial or a stronger ROI discussion.

## What constraints still exist

- This is pilot-ready for a first external trial, not production-ready for broad rollout.
- Current evidence is still based mainly on bundled sample exports and small labeled slices rather than a real customer evidence base.
- The raw JSON export path is the strongest starting point; other export formats are usable, but some have thinner evidence.
- Human review must stay in place for the first pilot.
- Join gaps, unsafe redaction, unstable ordering, or guardrail misses should be treated as stop-and-review conditions.
