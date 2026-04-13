# Support V1 Master Handbook

## What this master handbook adds

This handbook adds one practical top-level map of the current `support_v1` system so you can quickly remember what exists, what each part is for, and which documents matter most without scanning the full folder.

## What `support_v1` is

`support_v1` is a bounded support-routing pilot stack. It takes a helpdesk export slice, checks whether the export is usable, normalizes it into the current support schema, reconstructs visible case history, and evaluates routing decisions on labeled decision points.

The current system is meant for first-pilot work, not broad production rollout. It is explicitly built to avoid core-engine changes in the first pilot phase.

Start here:

- `ARTIFACT_INDEX.md`
- `artifacts/support_v1_system_summary.md`
- `artifacts/support_v1_readiness_memo.md`
- `pilot_handoff_summary.md`

## Current system architecture in plain language

The system is easiest to understand as six layers:

1. Intake: decide the export shape, scope, owner, and constraints.
2. Contract check: verify ids, joins, timestamps, ordering, and usable detail fields before deeper work.
3. Normalization: convert the source export into the current `support_v1` case schema.
4. Event replay: turn normalized cases into the event form used by the evaluation layer.
5. Evaluation: compare `iml`, calibrated `iml`, `naive_summary`, and `full_history` on the same labeled slices.
6. Pilot packaging: assemble review docs, package artifacts, handoff bundles, and real pilot workspaces.

Most relevant references:

- Intake and contract: `real_export_intake_template.md`, `real_export_onboarding_checklist.md`, `helpdesk_export_contract.md`
- Normalization and event replay: `normalize_raw_support_export.py`, `normalize_raw_support_export_csv.py`, `normalize_mapped_support_export.py`, `helpdesk_adapter_zendesk_like.py`, `convert_support_cases_to_events.py`
- Evaluation and system state: `artifacts/support_ingest_modality_comparison.md`, `artifacts/support_v1_readiness_memo.md`, `artifacts/support_v1_system_summary.md`
- Pilot execution: `FIRST_LIVE_PILOT_RUNBOOK.md`, `support_v1_pilot_scorecard.md`, `support_v1_pilot_decision_memo.md`

## Ingest paths that exist today

There are four real export ingest paths plus one built-in labeled support path used for direct evaluation work:

- `raw_ingest`: raw hierarchical JSON export. Best current starting path. Use `normalize_raw_support_export.py`.
- `csv_ingest`: flat CSV export that already matches the current contract. Use `normalize_raw_support_export_csv.py`.
- `mapped_ingest`: flat CSV export that needs an explicit field mapping. Use `normalize_mapped_support_export.py` with `helpdesk_export_mapping_template.json`.
- `zendesk_like`: nested Zendesk-style JSON export. Use `helpdesk_adapter_zendesk_like.py`.
- `labeled_support`: bundled labeled support packs used for evaluation and calibration evidence, not for onboarding a new external export.

Most relevant references:

- Ingest contract: `helpdesk_export_contract.md`, `validate_helpdesk_export_contract.py`
- Schema and mapping: `schema.md`, `helpdesk_export_mapping_template.json`
- Readiness view: `artifacts/helpdesk_export_contract_validation.json`, `artifacts/support_v1_readiness_memo.md`
- Cross-modality summary: `artifacts/support_ingest_modality_comparison.md`

## Evaluation flows that exist today

There are three useful evaluation views in the current repo:

- Labeled support evaluation: the core labeled pack comparison on the bundled support slice.
- Modality-specific evaluation: raw, CSV, mapped, and Zendesk-like labeled evaluations on normalized support exports.
- Cross-modality comparison: one summary view that compares results across the supported evaluation paths.

Most relevant scripts:

- `run_support_evaluation.py`
- `run_support_label_evaluation.py`
- `run_support_label_pack_comparison.py`
- `run_support_ingest_modality_comparison.py`
- `run_support_raw_ingest_label_evaluation.py`
- `run_support_csv_ingest_label_evaluation.py`
- `run_support_mapped_ingest_label_evaluation.py`
- `run_support_zendesk_like_label_evaluation.py`

Most relevant artifacts:

- `artifacts/latest_support_label_evaluation.json`
- `artifacts/latest_support_label_review.csv`
- `artifacts/support_label_pack_comparison.md`
- `artifacts/support_label_pack_decision_memo.md`
- `artifacts/support_raw_ingest_pack_comparison.md`
- `artifacts/support_csv_ingest_pack_comparison.md`
- `artifacts/support_mapped_ingest_pack_comparison.md`
- `artifacts/support_zendesk_like_pack_comparison.md`
- `artifacts/support_ingest_modality_comparison.md`

## Calibration story and what it currently means

Calibration in `support_v1` currently means a support-specific adjustment layer applied after support history replay and before final routing. It is intentionally not a core-engine change.

Right now the evidence says calibrated `iml` is helping mostly by reducing over-conservative routing on clean support histories, while keeping contradiction and staleness protections in place. The repo-level claim is modest: calibration looks directionally strong across the current slices, but the evidence is still small-sample and support-specific.

Most relevant references:

- `CALIBRATION_NOTES.md`
- `CALIBRATION_INTEGRATION_NOTES.md`
- `CALIBRATION_EXPERIMENT_NOTES.md`
- `CALIBRATION_SWEEP_NOTES.md`
- `artifacts/support_label_calibration_experiment.json`
- `artifacts/support_label_calibration_sweep.json`
- `artifacts/support_label_calibration_ablation.json`
- `artifacts/support_v1_readiness_memo.md`

## Artifact stack overview

The artifact stack is the working evidence layer. It gives you normalized outputs, event outputs, latest evaluation outputs, comparison summaries, and top-level readiness summaries.

The most useful top-level artifact docs are:

- `ARTIFACT_INDEX.md`: best short navigation file for the artifact layer
- `artifacts/support_v1_system_summary.md`: fastest current system-state snapshot
- `artifacts/support_v1_readiness_memo.md`: best short evidence memo
- `artifacts/support_ingest_modality_comparison.md`: best cross-modality result summary
- `artifacts/support_v1_pilot_bundle_validation_summary.md`: shows package and handoff validation health
- `artifacts/support_v1_real_pilot_workspace_summary.md`: shows current real pilot workspace state

The most useful raw artifact outputs are:

- `artifacts/normalized_support_cases.json`
- `artifacts/normalized_support_cases_from_csv.json`
- `artifacts/normalized_support_cases_from_mapping.json`
- `artifacts/normalized_support_cases_from_zendesk_like.json`
- `artifacts/support_events.json`
- `artifacts/latest_support_raw_ingest_label_evaluation.json`
- `artifacts/latest_support_csv_ingest_label_evaluation.json`
- `artifacts/latest_support_mapped_ingest_label_evaluation.json`
- `artifacts/latest_support_zendesk_like_label_evaluation.json`

## Pilot stack overview

The pilot stack is the operator layer around the evaluation system. It handles onboarding, run execution, review, handoff, and decision-making.

Use these docs first:

- `pilot_handoff_summary.md`: quickest plain-language pilot summary
- `FIRST_LIVE_PILOT_RUNBOOK.md`: step-by-step operational flow
- `real_export_onboarding_checklist.md`: intake and go/no-go gate
- `real_export_intake_template.md`: capture source-system facts
- `support_v1_pilot_scorecard.md`: judge pilot success
- `support_v1_pilot_decision_memo.md`: final recommendation structure
- `pilot_readiness_decision_brief.md`: shortest yes/no readiness position

Generated pilot packaging lives under:

- `artifacts/pilot_packages/`
- `artifacts/pilot_handoff_bundles/`
- `artifacts/real_pilot_workspaces/`

Important detail: `PILOT_PACKAGE_INDEX.md` is not currently a single top-level file in `use_cases/support_v1`. It exists inside generated pilot packages and handoff bundles, for example `artifacts/pilot_packages/raw_ingest_20260413T092308/docs/PILOT_PACKAGE_INDEX.md`.

## Sales / pricing / ROI docs overview

The commercial layer is already present and is separate from the technical evidence layer.

Use these docs first:

- `SALES_PACK_INDEX.md`: best short map of the commercial docs
- `commercial_pilot_one_pager.md`: buyer-facing pilot overview
- `support_v1_pilot_pricing_framework.md`: pilot shape and pricing logic
- `support_v1_roi_model.md`: conservative pilot ROI framing
- `executive_status_brief.md`: sponsor-level status snapshot
- `investor_value_brief.md`: broader value framing

Practical read order:

1. `commercial_pilot_one_pager.md`
2. `artifacts/support_v1_readiness_memo.md`
3. `support_v1_pilot_pricing_framework.md`
4. `support_v1_roi_model.md`

## What is already strong

- The system already supports five evaluation modes: `labeled_support`, `raw_ingest`, `csv_ingest`, `mapped_ingest`, and `zendesk_like`.
- Export contract validation passes on the bundled raw JSON, flat CSV, and Zendesk-like JSON samples.
- Calibrated `iml` is directionally strong across the current evidence and beats the best baseline on the largest slice in each implemented modality.
- `raw_ingest` is the strongest current first-pilot path.
- Pilot packaging is real, not aspirational: current summaries show 5 pilot packages, 6 handoff bundles, and clean validation on all scanned bundles.
- A real pilot workspace already exists and passes for `raw_ingest`.
- The repo already has practical onboarding, runbook, scorecard, handoff, and decision docs.

Best evidence docs:

- `artifacts/support_v1_readiness_memo.md`
- `artifacts/support_v1_system_summary.md`
- `artifacts/support_v1_pilot_bundle_validation_summary.md`
- `artifacts/support_v1_real_pilot_workspace_summary.md`

## What is still weak

- The evidence base is still small. Outside the bundled labeled support packs, the largest modality slices are still in the low double digits.
- Zendesk-like evidence is still the thinnest current path.
- Real external export evidence is still limited; the repo is pilot-ready, not production-proven.
- Real-world risks around redaction quality, join completeness, timestamp quality, and auditability still need live validation on partner data.
- Only `raw_ingest` currently has a validated real pilot workspace.
- There is one summary-layer inconsistency to clean up: the repo has mapped-ingest evaluation artifacts, but `artifacts/support_v1_system_summary.md` still describes `mapped_ingest` as a gap in one consolidated ingest snapshot.

Best gap-tracking docs:

- `artifacts/support_v1_readiness_memo.md`
- `artifacts/support_v1_system_summary.md`
- `pilot_readiness_decision_brief.md`
- `commercial_pilot_one_pager.md`

## Recommended next steps

1. Use `raw_ingest` as the default path for the first real external pilot unless the partner naturally exports a different supported format.
2. Add one more real labeled slice on the Zendesk-like path, since it is still the thinnest evidence path.
3. Expand validated real pilot workspace coverage beyond `raw_ingest` so CSV, mapped, and Zendesk-like paths are not just package-ready but workspace-ready.
4. Clean up the mapped-ingest summary mismatch so top-level system summaries and underlying modality artifacts say the same thing.
5. Keep the first pilot bounded: one partner, one queue, one modality, one small redacted slice, manual review throughout, and no core-engine changes.

If you only have time to read four files later, read these:

1. `artifacts/support_v1_system_summary.md`
2. `artifacts/support_v1_readiness_memo.md`
3. `ARTIFACT_INDEX.md`
4. `pilot_handoff_summary.md`
