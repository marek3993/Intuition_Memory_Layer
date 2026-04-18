# Support V1 Master Guide For PDF

## What this guide adds

This guide adds one compact, print-friendly source document for the current `support_v1` system. It is meant to help a human re-orient quickly without reading the full handbook, artifact layer, pilot deliverables pack docs, and sales materials one by one.

It is a summary of the current repo state, not a new framework. It keeps the focus on what already exists, what is ready for a first pilot, where the weak spots still are, and what should happen next.

## What `support_v1` is

`support_v1` is a bounded support-routing pilot system. It takes a support export slice, checks whether the export is usable, normalizes it into the current support schema, reconstructs visible case history, and evaluates routing decisions on labeled decision points.

The current system is designed for a first live pilot, not for broad production rollout. It is also explicitly scoped to avoid core-engine changes in the first pilot phase.

## What already exists

The current repo already contains a complete pilot-oriented stack. At a high level, that stack covers intake, contract validation, normalization, event reconstruction, evaluation, calibration, pilot packaging, handoff, and commercial support material.

There are five supported operating modes in the current repo state: `labeled_support`, `raw_ingest`, `csv_ingest`, `mapped_ingest`, and `zendesk_like`.

The supporting document set is already substantial. The main handbook gives the broad map. The system summary and readiness memo give the current state of evidence. The artifact and sales indexes help a reviewer jump to the right supporting material quickly. Pilot package indexes also exist inside generated pilot deliverables packs and handoff materials rather than as a single top-level file.

The current build state is already concrete:

- Top-level pilot deliverables pack coverage exists for all 5 supported modes.
- Bundle validation reports 11 PASS, 0 FAIL, and 0 missing validation artifacts across scanned pilot deliverables packs and handoff materials.
- One real pilot workspace is currently validated as PASS for `raw_ingest`.
- Contract validation currently passes on 3 bundled sample inputs with 0 warnings and 0 errors.

## Ingest paths

There are four real export ingest paths plus one internal labeled support path used for evaluation evidence.

The raw JSON export path (`raw_ingest`) is the strongest current starting path. It uses raw hierarchical JSON exports and has the best present evidence base for a first live pilot.

`csv_ingest` supports flat CSV exports that already fit the current contract. It is usable when a source system can provide a stable contract-style export without additional mapping work.

The mapped CSV export path (`mapped_ingest`) supports flat CSV exports that need an explicit field map before normalization. This path exists and has evaluation evidence, but it still appears as a summary-layer gap in the top-level ingest comparison artifact.

`zendesk_like` supports nested Zendesk-style JSON exports. It is implemented and evaluated, but it remains the thinnest evidence path.

`labeled_support` is the built-in labeled reference path used to compare route quality on the bundled support slices. It is part of the evidence layer, not the onboarding path for a new external customer export.

## Evaluation and calibration

The evaluation layer compares standard routing (`default iml`), calibrated routing (`calibrated iml`), `naive_summary`, and `full_history` on the same labeled decision points. The goal is not to claim broad automation readiness. The goal is to see whether the current routing logic becomes more reliable on bounded support-history slices.

Calibration is the main adjustment layer in the current system. It is support-specific and intentionally sits outside the core engine. In practical terms, the current repo evidence says calibrated routing is directionally better than standard routing across the loaded support slices while still keeping the broader guardrail posture intact.

The strongest current evidence is on the raw JSON export path (`raw_ingest`) for the `combined_ab` slice: calibrated routing reaches 92.31% versus 69.23% for the best non-calibrated comparison method. Across the current readiness memo, calibrated routing beats the best comparison method on the largest slice in all 5 export formats.

The current evidence base is still modest. The largest current slices are 30 labels for the bundled labeled support path, 13 for raw ingest, 13 for CSV ingest, 11 for mapped ingest, and 9 for Zendesk-like ingest. That is enough to justify a bounded pilot, but not enough to justify a broad production claim.

## Pilot workflow

The pilot workflow is already documented and operationally framed. The sequence is straightforward.

Start with intake and onboarding. Confirm export shape, field coverage, joins, timestamps, ordering, redaction expectations, and pilot owner responsibilities.

Then run contract validation before deeper work. If the export fails basic linkage or ordering requirements, the right move is to stop and review rather than push forward.

If the export is usable, normalize it into the current `support_v1` schema and reconstruct the visible support history needed by the evaluation layer.

From there, run a labeled evaluation pass on the bounded slice. The expected output is a reviewable comparison artifact rather than an automatic deployment decision.

Finally, package the result into the existing handoff and decision materials. The current repo already includes readiness memos, runbooks, scorecards, decision memo templates, handoff summaries, and generated pilot deliverables packs.

The intended first live pilot remains narrow: one partner, one queue, one export modality, one redacted slice, and manual review throughout.

## Commercial and sales assets

The repo already includes a usable commercial layer for a first pilot conversation. The one-pager explains the problem, current build, pilot shape, and constraints in buyer-facing language. The pricing framework defines lightweight, standard, and extended pilot shapes without overreaching beyond the current evidence. The ROI model gives a conservative value frame. Executive and investor briefs provide shorter sponsor-facing versions of the story.

The commercial stance is intentionally modest. The first paid step is a bounded pilot that validates export fit, data quality, routing usefulness, and decision value on a real slice. It is not positioned as a production deployment or a promise of fixed savings.

## Current strengths

The current system is strong in a few specific ways.

First, the system is already end to end. It does not stop at a prototype evaluator. It includes intake, validation, normalization, event reconstruction, comparison outputs, handoff documents, and pilot packaging.

Second, the evidence direction is consistently positive. Calibrated routing currently clears the best comparison method on the largest slice in each supported export format in the readiness memo.

Third, the raw JSON export path (`raw_ingest`) is a credible first-pilot path now. It has the strongest evidence and the only validated real pilot workspace.

Fourth, the pilot layer is real rather than aspirational. The repo already contains generated pilot deliverables packs, handoff materials, validation summaries, and a first real pilot workspace structure.

## Current weak spots

The main weakness is still evidence depth. The system is pilot-ready, but the evaluated sample sizes are still small outside the bundled labeled support path.

Zendesk-like ingest is currently the thinnest path. It works, but it has the smallest evaluated largest slice and should not be treated as equally proven as the raw JSON export path (`raw_ingest`).

Real external evidence is still limited. The current proof layer is built mainly on bundled sample exports, not on repeated live customer slices.

There is also one summary inconsistency worth cleaning up. The repo contains mapped-ingest evaluation artifacts, but the top-level system summary still describes the mapped CSV export path (`mapped_ingest`) as a gap in the consolidated ingest comparison snapshot.

Operationally, the first live pilot still depends on good partner data hygiene. Join completeness, timestamp quality, redaction safety, auditability, and manual review discipline remain real stop conditions.

## Recommended next steps

Use the raw JSON export path (`raw_ingest`) as the default first external pilot path unless a partner naturally exports a different supported format.

Add one more labeled Zendesk-like slice so the weakest current modality has a less fragile evidence base.

Expand validated real pilot workspace coverage beyond the raw JSON export path (`raw_ingest`) so the other supported export paths are not just package-ready but workspace-ready.

Clean up the mapped-ingest summary mismatch so the top-level system summary matches the underlying evaluation artifacts.

Keep the first live pilot tightly bounded. The right near-term goal is one credible real-slice decision package, not early production expansion.
