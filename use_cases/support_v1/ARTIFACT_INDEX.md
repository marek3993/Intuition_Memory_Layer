# Support V1 Artifact Index

## What this index adds

This index adds one short navigation layer for `support_v1` so a human can quickly find the main artifacts by purpose without scanning the full folder.

## Core Evaluation Runners

- `run_support_evaluation.py` — Runs the main labeled evaluation flow on the bundled support slice. Use it when you want the default end-to-end evaluation output.
- `run_support_label_evaluation.py` — Runs label-based route evaluation and writes the latest label-review artifacts. Use it when you need the current labeled routing readout.
- `run_support_label_pack_comparison.py` — Compares pack variants across the labeled support sets. Use it when you want cross-pack comparison results.
- `run_support_ingest_modality_comparison.py` — Compares results across supported ingest paths. Use it when you need a top-level modality view.
- `run_support_raw_ingest_label_evaluation.py` — Evaluates routing on raw-export ingest. Use it when a pilot or test export comes in raw JSON form.
- `run_support_csv_ingest_label_evaluation.py` — Evaluates routing on flat CSV ingest. Use it when the source export is contract-style CSV.
- `run_support_mapped_ingest_label_evaluation.py` — Evaluates routing on mapped CSV ingest. Use it when the export needs field mapping before evaluation.
- `run_support_zendesk_like_label_evaluation.py` — Evaluates routing on Zendesk-like nested exports. Use it when testing the Zendesk-style prototype path.

## Comparison Artifacts

- `artifacts/support_label_pack_comparison.md` — Human-readable summary of labeled pack comparison results. Use it when reviewing which pack setup performed best.
- `artifacts/support_label_pack_decision_memo.md` — Short decision memo for choosing among labeled pack options. Use it when you need a recommendation, not just raw comparison output.
- `artifacts/support_ingest_modality_comparison.md` — Summary of how the supported ingest paths compare. Use it when deciding which ingest path is strongest or weakest.
- `artifacts/support_raw_ingest_pack_comparison.md` — Comparison summary for raw-ingest pack results. Use it when raw JSON is the current pilot path.
- `artifacts/support_csv_ingest_pack_comparison.md` — Comparison summary for CSV-ingest pack results. Use it when the pilot uses flat CSV exports.
- `artifacts/support_mapped_ingest_pack_comparison.md` — Comparison summary for mapping-based CSV results. Use it when field mapping is part of onboarding.
- `artifacts/support_zendesk_like_pack_comparison.md` — Comparison summary for Zendesk-like ingest results. Use it when nested helpdesk exports are in scope.
- `artifacts/latest_support_label_evaluation.json` — Latest machine-readable labeled evaluation output. Use it when you need the most recent numeric result set.
- `artifacts/latest_support_label_review.csv` — Latest case-level review sheet for labeled evaluation. Use it when reviewers need to inspect individual route decisions.

## Ingest / Normalization Artifacts

- `normalize_raw_support_export.py` — Normalizes raw support export JSON into the working support schema. Use it when onboarding raw hierarchical exports.
- `normalize_raw_support_export_csv.py` — Normalizes flat CSV support exports. Use it when the source system can only provide CSV.
- `normalize_mapped_support_export.py` — Normalizes CSV exports using an explicit field mapping. Use it when customer export fields do not match the contract directly.
- `helpdesk_adapter_zendesk_like.py` — Adapts Zendesk-like nested exports into the same working shape. Use it when the source data follows a Zendesk-style structure.
- `convert_support_cases_to_events.py` — Converts normalized support cases into event form for downstream evaluation. Use it when you need the event-layer artifact.
- `artifacts/normalized_support_cases.json` — Normalized case output for the base support sample. Use it when auditing the post-normalization shape.
- `artifacts/normalized_support_cases_from_csv.json` — Normalized output from flat CSV ingest. Use it when checking CSV normalization quality.
- `artifacts/normalized_support_cases_from_mapping.json` — Normalized output from mapped CSV ingest. Use it when verifying a mapping-based onboarding flow.
- `artifacts/normalized_support_cases_from_zendesk_like.json` — Normalized output from Zendesk-like ingest. Use it when validating nested export conversion.
- `artifacts/support_events.json` — Event-form output derived from the normalized support cases. Use it when tracing what the evaluation layer actually consumed.

## Validation / Contract Artifacts

- `helpdesk_export_contract.md` — Defines the minimum export contract for support onboarding. Use it when confirming what a real export must contain.
- `validate_helpdesk_export_contract.py` — Checks whether an export satisfies the required contract fields and joins. Use it before spending time on normalization or pilot review.
- `artifacts/helpdesk_export_contract_validation.json` — Latest validation result for the bundled sample inputs. Use it when you want a quick pass/fail reference.
- `schema.md` — Documents the current support case schema used by the flow. Use it when mapping or debugging field expectations.
- `helpdesk_export_mapping_template.json` — Starter mapping template for non-contract CSV exports. Use it when onboarding a source with different field names.

## Onboarding / Pilot Artifacts

- `real_export_onboarding_checklist.md` — Checklist for bringing in the first real export slice. Use it when preparing a pilot intake.
- `real_export_intake_template.md` — Intake template for documenting export source details. Use it when collecting onboarding facts from the pilot owner.
- `real_export_field_inventory_template.csv` — Inventory sheet for real export fields. Use it when mapping an unfamiliar export format.
- `pilot_handoff_summary.md` — Short handoff summary of what the current `support_v1` pack can do. Use it when transferring context into a first pilot conversation.
- `pilot_handoff_email_template.md` — Ready-to-send handoff email template for pilot coordination. Use it when reaching out to an internal or external pilot contact.
- `support_v1_pilot_scorecard.md` — Operational scorecard for judging pilot performance against baseline. Use it during and after the pilot review cycle.
- `support_v1_roi_model.md` — Conservative ROI model tied to measured queue effects. Use it when converting pilot outcomes into value language.
- `artifacts/support_v1_readiness_memo.md` — Compact summary of current capability, evidence, and gaps. Use it when deciding whether the pack is ready for a real export pilot.
- `support_v1_pilot_decision_memo.md` — Concise post-pilot decision memo structure. Use it when deciding whether to move forward, constrain, rerun, or stop after a pilot.
- `support_v1_pilot_decision_memo_template.md` — Fill-in template for the post-pilot decision review. Use it when preparing the actual recommendation document.

## Executive / Investor Artifacts

- `executive_status_brief.md` — Short executive-facing status update for current `support_v1` progress. Use it when leadership needs a quick snapshot.
- `investor_value_brief.md` — High-level value framing for external or investor-style conversations. Use it when the discussion is about strategic value rather than operator workflow.
