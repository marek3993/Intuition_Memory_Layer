# Support V1 Executive Status Brief

This brief adds one short executive-facing view of where `support_v1` stands today, what has already been proven in prototype form, and what still has to happen before real production use.

## What `support_v1` is

`support_v1` is a support-history routing prototype. It takes a bounded helpdesk export, reconstructs the visible case history, and decides whether a case should stay on a faster path or be routed to a deeper review path.

## What has already been built

- Prototype ingest paths already exist for raw JSON exports, flat CSV exports, mapped CSV exports, and Zendesk-like nested exports.
- A contract validator already checks whether an export has the ids, joins, timestamps, ordering, and text detail needed for the current flow.
- Existing evaluation runners already compare default `iml`, calibrated `iml`, `naive_summary`, and `full_history` on the same labeled decision points.

## What evidence exists today

- Across the loaded readiness artifacts, calibrated `iml` never underperforms default `iml`: 18 improved, 1 tied, 0 regressed across 19 slices.
- In the unified ingest comparison, calibrated `iml` improves on default `iml` in 13 of 14 slices and ties once.
- On the largest slice in every implemented modality, calibrated `iml` beats the best baseline.
- The strongest current result is the raw-ingest comparison, where calibrated `iml` reaches 92.31% versus 69.23% for the best non-calibrated method.

## What is still missing before real production use

- The evidence is still based on sample exports and small labeled slices rather than a real customer or partner export.
- The smallest evidence path is still the Zendesk-like modality, where the current largest slice is only 9 labels.
- Real production use still needs a redacted real export, real label review on visible history, and confirmation that joins, ordering, and privacy constraints hold on live data.

## Immediate next step

Obtain one small redacted real helpdesk export, run it through the existing contract validation and normalization flow, and complete one first labeled pilot evaluation without changing the core engine.
