# Support V1 Pilot Handoff Summary

This pack turns the current Support V1 readiness work into a practical starting point for the first real helpdesk export conversation.

## What Support V1 currently does

- Takes a bounded support export slice, normalizes it into the existing Support V1 case schema, and evaluates routing decisions at labeled decision points.
- Compares standard routing, calibrated routing, and current comparison methods on the same visible-history slice.
- Uses calibration as the current adjustment layer; core-engine changes are not required for the first pilot.

## What export formats already work in prototype form

- Raw hierarchical JSON exports with account, ticket, and record collections.
- Flat helpdesk CSV exports that match the current contract fields.
- Flat CSV exports plus an explicit mapping file.
- Zendesk-like nested JSON exports with organizations, users, tickets, comments, and events.

## What validation / evaluation capability already exists

- A contract validator checks minimum export requirements before normalization: ids, joins, timestamps, ordering fields, actor roles, source types, action/outcome coverage, and details text.
- Existing normalization paths cover the current raw JSON, CSV, mapped CSV, and Zendesk-like prototype flows.
- Existing labeled evaluation runners already produce comparison artifacts and review CSVs for a first real slice.
- Current readiness evidence is positive, but still based on bundled sample exports rather than a real pilot export.

## What is needed from a first pilot export

- One small, redacted, auditable export slice rather than a broad backfill.
- A clear export format choice: raw JSON, Zendesk-like JSON, fixed-contract CSV, or mapped CSV.
- Stable entity/account, ticket, and record identifiers with complete joins.
- ISO-8601 timestamps with timezone offsets or `Z`, plus deterministic record ordering.
- Enough detail text to reconstruct visible ticket history without storing unsafe raw PII.
- A small first label pack on the real slice so routing can be reviewed against actual visible history.

## What success would look like in the first pilot

- The export passes contract validation and can be normalized without custom engine changes.
- The resulting normalized slice is easy to audit end to end for identity linkage, ordering, and redaction safety.
- A first labeled evaluation run completes on the real slice and produces a reviewable comparison artifact.
- The team can explain where calibrated routing helps, where guardrails hold, and what data gaps remain before a larger rollout.
