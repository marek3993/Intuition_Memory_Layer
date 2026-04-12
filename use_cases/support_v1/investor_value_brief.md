# Support V1 Investor Value Brief

This brief adds a short investor/operator view of what `support_v1` already proves, why that matters commercially, and what still has to be de-risked before it is a real product asset.

## Problem it solves

Support teams often have to decide which cases can stay on a fast path and which need deeper review, but that decision is usually made against messy export data and incomplete case history reconstruction. `support_v1` is aimed at making that routing decision on a bounded helpdesk export using the visible support history rather than a manually stitched summary.

## What has already been built

- Prototype ingest paths exist for raw JSON exports, flat CSV exports, mapping-based CSV exports, and Zendesk-like nested exports.
- A contract validator already checks whether an export has the ids, joins, timestamps, ordering, and text detail required for the current flow.
- Existing evaluation runners already compare default `iml`, calibrated `iml`, `naive_summary`, and `full_history` on the same labeled decision points.

## What evidence exists today

- Across the loaded readiness artifacts, calibrated `iml` never underperforms default `iml`: 18 improved, 1 tied, 0 regressed across 19 slices.
- In the unified ingest comparison, calibrated `iml` improves on default `iml` in 13 of 14 slices and ties once.
- On the largest slice in each loaded modality, calibrated `iml` beats the best non-calibrated method.
- The strongest current result is raw-ingest `combined_ab`: calibrated `iml` at 92.31% versus 69.23% for the best non-calibrated baseline.

## Why the calibrated approach matters economically

The current evidence suggests the value is not just that the system can read support exports, but that calibration makes the routing decision materially more reliable without requiring a core-engine rewrite. Economically, that matters because better routing quality can reduce unnecessary deep-review work, preserve fast-path handling where it is justified, and lower implementation risk by building on an already functioning evaluation and ingest layer.

## What still has to happen before this is a real business asset

- The evidence still comes from bundled sample exports and small labeled slices, not a real customer or partner export.
- The thinnest evidence path is still the Zendesk-like modality, where the current largest slice is only 9 labels.
- A real product asset still needs one redacted real export, real label review on visible history, and confirmation that joins, ordering, and privacy constraints hold on live data.

## Next de-risking milestone

Run one small redacted real helpdesk export through the existing contract validation and normalization flow, then complete one first labeled pilot evaluation on that real slice without changing the core engine.
