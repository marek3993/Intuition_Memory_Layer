# Support V1 Golden Path For First Pilot

## What this artifact adds

This artifact adds one explicit default path for the first real `support_v1` pilot so operators do not treat every supported ingest mode as equally preferred on day one.

Use it with `FIRST_LIVE_PILOT_RUNBOOK.md`, `pilot_readiness_decision_brief.md`, `artifacts/support_v1_system_summary.md`, and the mode-specific `PILOT_PACKAGE_INDEX.md`.

## Recommended first pilot path

- Recommended first pilot path: one small, redacted, auditable `raw_ingest` export slice with manual review, then one calibrated-vs-default label evaluation on that same slice.
- Default ingest mode: `raw_ingest`

## Why this path is preferred right now

- `pilot_readiness_decision_brief.md` already names `raw_ingest` as the strongest starting path for the first external pilot.
- `artifacts/support_v1_system_summary.md` shows the only validated real pilot workspace is `raw_ingest` and that workspace is `PASS`.
- `artifacts/support_v1_real_pilot_workspace_summary.md` shows `raw_ingest` is the only mode with a validated workspace path today.
- `artifacts/support_ingest_modality_comparison.md` shows calibrated IML clears the best baseline on the largest slice in every implemented ingest mode, so `raw_ingest` is not an evidence outlier that needs special caution before use.
- `artifacts/support_raw_ingest_pack_comparison.md` shows the current raw path holds together across the combined raw sample slice.
- `PILOT_PACKAGE_INDEX.md` and `FIRST_LIVE_PILOT_RUNBOOK.md` already fit the current `raw_ingest` package and workspace flow.

`raw_ingest` is the default not because every raw metric is the single best number in the repo, but because it combines solid comparison evidence with the strongest operational readiness: contract coverage, package coverage, and the only validated real pilot workspace.

## Run this path in order

### 1. Lock scope and intake

Use:

- `real_export_intake_template.md`
- `real_export_field_inventory_template.csv`
- `real_export_onboarding_checklist.md`
- `pilot_handoff_summary.md`

Required output before moving on:

- one completed intake record
- one completed field inventory
- one bounded first slice
- one explicit mode choice recorded as `raw_ingest`
- one blocker list for privacy, joins, timestamps, or missing fields

### 2. Initialize the pilot workspace

Run:

```powershell
py use_cases/support_v1/init_support_v1_real_pilot_workspace.py --mode raw_ingest --workspace-name first_real_pilot
```

Required output before moving on:

- `use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot/workspace_manifest.json`
- the initialized `intake/`, `evaluation/`, `decision/`, and `references/` folders

### 3. Validate the workspace before using it

Run:

```powershell
py use_cases/support_v1/validate_support_v1_real_pilot_workspace.py --workspace-path use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot
```

Required output before moving on:

- `use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot/validation_result.json`
- validation status `PASS`

### 4. Gate the partner export against the current contract

Use:

- `helpdesk_export_contract.md`
- `validate_helpdesk_export_contract.py`
- `real_export_onboarding_checklist.md`

Required output before moving on:

- one explicit contract check recorded in the workspace notes against the fields defined in `helpdesk_export_contract.md`
- one accepted warning list if the export is not perfectly clean
- no unresolved blocker on ids, joins, ordering, timestamps, actor roles, or usable detail text

### 5. Normalize the raw export

Use:

- `normalize_raw_support_export.py`

For a real export, run the raw-ingest evaluation runner with explicit override paths so the normalized artifact is written into the pilot workspace and retained there.

Required output before moving on:

- one normalized cases JSON for the real slice
- one recorded source export path and normalized output path in the workspace notes

### 6. Spot-check auditability and event replay

Use:

- `convert_support_cases_to_events.py`
- `real_export_onboarding_checklist.md`
- `ARTIFACT_INDEX.md`

Required output before moving on:

- one spot-check record showing at least one routine case and one risky case are auditable
- one event replay artifact or equivalent event inspection confirming ordering and identity linkage make sense

### 7. Build the first real pilot labels

Use:

- `LABELING_GUIDE.md`

Required output before moving on:

- one pilot labels file for the real slice
- route labels, auxiliary flags, short justification text, and labeler identity captured for each reviewed decision

### 8. Run the raw-ingest labeled evaluation twice

Run default first, then calibrated, keeping separate output paths:

```powershell
py use_cases/support_v1/run_support_raw_ingest_label_evaluation.py --raw-path C:\path\to\pilot_raw_export.json --labels-path C:\path\to\pilot_labels.json --normalized-output-path use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot/evaluation/pilot_normalized_cases.json --evaluation-output-path use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot/evaluation/pilot_default_label_evaluation.json --review-output-path use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot/evaluation/pilot_default_label_review.csv
py use_cases/support_v1/run_support_raw_ingest_label_evaluation.py --raw-path C:\path\to\pilot_raw_export.json --labels-path C:\path\to\pilot_labels.json --normalized-output-path use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot/evaluation/pilot_normalized_cases.json --evaluation-output-path use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot/evaluation/pilot_calibrated_label_evaluation.json --review-output-path use_cases/support_v1/artifacts/real_pilot_workspaces/first_real_pilot/evaluation/pilot_calibrated_label_review.csv --calibrated
```

Required output before moving on:

- `pilot_normalized_cases.json`
- `pilot_default_label_evaluation.json`
- `pilot_default_label_review.csv`
- `pilot_calibrated_label_evaluation.json`
- `pilot_calibrated_label_review.csv`

### 9. Review the package docs and make the pilot call

Use:

- `FIRST_LIVE_PILOT_RUNBOOK.md`
- `support_v1_pilot_scorecard.md`
- `support_v1_pilot_decision_memo_template.md`
- the latest `raw_ingest` `PILOT_PACKAGE_INDEX.md`

Required output before closing:

- one completed pilot scorecard
- one completed decision memo draft
- one final pilot state recorded as `proceed`, `proceed with constraints`, `revise and rerun`, or `stop`

## Fall back to another path only when

- the partner cannot provide a raw hierarchical export with reliable account, ticket, and event joins
- the partner's natural export is already a supported alternative shape and that shape passes the contract gate more cleanly than a forced raw conversion
- the raw export fails auditability on ordering, actor roles, timestamps, or detail text and the issue cannot be corrected quickly

Fallback order for the first pilot:

1. `csv_ingest` if the partner can provide the fixed flat contract cleanly
2. `mapped_ingest` if the partner only has flat CSV with non-standard columns but the mapping is stable
3. `zendesk_like` if the partner already exports that structure naturally

Do not use `labeled_support` as the default first external pilot path. It remains useful as internal evaluation evidence, but it is not the primary external export onboarding path.

## What success looks like

The golden path is successful when all of the following are true:

- one real partner slice completes the `raw_ingest` path without contract or auditability blockers
- the workspace stays `PASS` and all expected evaluation outputs exist in the workspace
- the calibrated run is at least as good as the default run on the pilot slice
- the pilot scorecard can be filled with real-slice evidence rather than assumptions
- the final decision memo can credibly say either `proceed` or `proceed with constraints` with named follow-ups instead of fundamental ingest uncertainty
