# Support V1 First Live Pilot Runbook

## What this runbook adds

This runbook adds one short operational path for the first real `support_v1` pilot, from export intake through post-run decision review, using the current onboarding, normalization, evaluation, and pilot review artifacts already in the repo.

Use it with `ARTIFACT_INDEX.md`, `real_export_onboarding_checklist.md`, `support_v1_pilot_scorecard.md`, and `support_v1_pilot_decision_memo.md`.

## 1. Confirm export owner and scope

- What to do: confirm the export owner, backup contact, pilot queue or slice, export date range, entity scope, and export modality before any repo-side work starts.
- Use: `real_export_intake_template.md` and `pilot_handoff_summary.md`.
- Output before moving on: one completed intake record with owner, bounded slice, chosen entity scope, and one selected ingest path: raw JSON, Zendesk-like JSON, fixed-contract CSV, or mapped CSV.

## 2. Collect the intake template and field inventory

- What to do: capture the real export structure, join fields, timestamp fields, actor-role fields, redaction notes, and known gaps for the first slice.
- Use: `real_export_intake_template.md`, `real_export_field_inventory_template.csv`, and `real_export_onboarding_checklist.md`.
- Output before moving on: one completed intake template, one field inventory sheet, and a clear list of any open data-quality or privacy blockers.

## 3. Validate the export contract

- What to do: check that the export can reconstruct the current `support_v1` contract targets, joins, ordering fields, timestamps, actor roles, and usable detail text before normalization starts.
- Use: `helpdesk_export_contract.md`, `validate_helpdesk_export_contract.py`, and `real_export_onboarding_checklist.md`.
- Output before moving on: one contract-validation result JSON plus a pass or explicit warning list that the pilot owner has accepted.

## 4. Choose the normalization path

- What to do: select the existing normalization path that matches the export shape and keep that path fixed for the pilot slice.
- Use: `normalize_raw_support_export.py` for raw hierarchical JSON, `helpdesk_adapter_zendesk_like.py` for Zendesk-like JSON, `normalize_raw_support_export_csv.py` for fixed-contract CSV, or `normalize_mapped_support_export.py` plus `helpdesk_export_mapping_template.json` for mapped CSV.
- Output before moving on: one normalized pilot artifact in the current `support_v1` case schema and one confirmed modality choice recorded in the intake notes.

## 5. Spot-check normalized output and event replay

- What to do: verify that the normalized slice is auditable end to end, then convert it into events and inspect at least one routine case and one risky case for identity linkage, ordering, and plausible support history.
- Use: `real_export_onboarding_checklist.md`, `convert_support_cases_to_events.py`, and `ARTIFACT_INDEX.md`.
- Output before moving on: one normalized cases artifact that passes manual spot-checking and one event-form artifact or equivalent replay inspection showing the visible history is usable.

## 6. Prepare the first pilot label pack

- What to do: create a small, intentionally mixed label set on the real slice using the current route labels and auxiliary flags only, and keep labeling tied to visible history at each decision timestamp.
- Use: `LABELING_GUIDE.md` and `real_export_onboarding_checklist.md`.
- Output before moving on: one pilot labels file with route labels, auxiliary flags, short justifications, and labeler identity for the first reviewed slice.

## 7. Run the labeled evaluation

- What to do: run the matching modality-specific labeled evaluation runner on the normalized pilot slice and the pilot labels file.
- Use: `run_support_raw_ingest_label_evaluation.py`, `run_support_zendesk_like_label_evaluation.py`, `run_support_csv_ingest_label_evaluation.py`, or `run_support_mapped_ingest_label_evaluation.py`, based on the chosen normalization path.
- Output before moving on: one label-evaluation JSON artifact and one case-level review CSV for the real pilot slice.

## 8. Compare calibrated vs default and baselines

- What to do: review the same pilot slice in both default and calibrated mode, then compare `iml`, calibrated `iml`, `naive_summary`, and `full_history` on the evaluation outputs before drawing conclusions.
- Use: the same modality-specific labeled evaluation runner, its calibrated mode, its existing evaluation and review output-path overrides so both pilot runs are retained, the emitted evaluation JSON, the review CSV, and the comparison rules already described in `support_v1_pilot_scorecard.md`.
- Output before moving on: one side-by-side comparison of default vs calibrated pilot results, with baseline position and any guardrail misses called out explicitly.

## 9. Review the pilot scorecard

- What to do: summarize decision metrics, diagnostic metrics, guardrail misses, and operator burden using the live pilot evidence rather than assumptions.
- Use: `support_v1_pilot_scorecard.md`, the pilot evaluation JSON, and the pilot review CSV.
- Output before moving on: one completed pilot scorecard with a clear read on `fast_path` precision, `deep_path` recall, contradiction or stale misses, and operational burden.

## 10. Fill the pilot decision memo

- What to do: roll the scorecard, export quality, normalization stability, and live pilot observations into one recommendation draft.
- Use: `support_v1_pilot_decision_memo.md`, `support_v1_pilot_decision_memo_template.md`, and `artifacts/support_v1_readiness_memo.md`.
- Output before moving on: one completed pilot decision memo draft with a single recommendation state and the reasons behind it.

## 11. Make the pilot decision

- What to do: choose exactly one next state for the pilot and record the constraint or follow-up needed for that choice.
- Use: `support_v1_pilot_decision_memo.md` and `support_v1_pilot_scorecard.md`.
- Output before closing the pilot review: one final decision recorded as `proceed`, `proceed with constraints`, `revise and rerun`, or `stop`, with owner and next action attached.
