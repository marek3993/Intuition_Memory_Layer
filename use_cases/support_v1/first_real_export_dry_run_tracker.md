# Support V1 First Real Export Dry-Run Tracker

## What this tracker adds

This adds one concise operational tracker for the first real external export dry run so the team can move from intake through validation, normalization, labeling, evaluation, pilot-package build, handoff export, and final decision without changing the core engine.

Use it with `real_export_onboarding_checklist.md`, `FIRST_LIVE_PILOT_RUNBOOK.md`, `ARTIFACT_INDEX.md`, and `support_v1_pilot_decision_memo.md`.

## How to use it

- Copy the stage rows from `first_real_export_dry_run_tracker_template.csv`.
- Keep one row per stage and update owner, status, date, artifact path, and notes as the dry run moves forward.
- Record blockers at the stage where they appear. Do not skip forward without noting the reason.

## Stage guide

| Stage | What to confirm before marking complete | Primary alignment |
| --- | --- | --- |
| export received | The bounded real export slice, owner, modality, and date range are known. | `real_export_intake_template.md`, `pilot_handoff_summary.md` |
| intake captured | Intake record and field inventory are filled with joins, timestamps, actor roles, redaction notes, and known gaps. | `real_export_intake_template.md`, `real_export_field_inventory_template.csv` |
| contract validated | The export passes the current contract gate or has an explicit accepted warning list. | `real_export_onboarding_checklist.md`, `helpdesk_export_contract.md` |
| normalization path selected | One ingest path is fixed for the slice: raw JSON, Zendesk-like JSON, fixed-contract CSV, or mapped CSV. | `FIRST_LIVE_PILOT_RUNBOOK.md`, `ARTIFACT_INDEX.md` |
| normalization run complete | One normalized artifact exists and the slice is auditable end to end. | current normalizer plus `ARTIFACT_INDEX.md` |
| labels prepared | The first real-slice label pack exists with route labels, auxiliary flags, short justification, and labeler ID. | `real_export_onboarding_checklist.md`, `LABELING_GUIDE.md` |
| evaluation run complete | The matching labeled evaluation run produced its JSON artifact and case-review CSV. | `FIRST_LIVE_PILOT_RUNBOOK.md`, `ARTIFACT_INDEX.md` |
| calibrated vs baseline reviewed | Default `iml`, calibrated `iml`, `naive_summary`, and `full_history` were reviewed on the same slice. | `FIRST_LIVE_PILOT_RUNBOOK.md`, `support_v1_pilot_scorecard.md` |
| pilot package built | The scorecard, readiness evidence, and supporting pilot artifacts are assembled for review. | `ARTIFACT_INDEX.md`, `support_v1_pilot_scorecard.md` |
| handoff package exported | The review package or handoff bundle is exported for pilot stakeholders. | `pilot_handoff_summary.md`, `pilot_handoff_email_template.md` |
| final dry-run conclusion | One recommendation state is recorded with owner and next action: `proceed`, `proceed with constraints`, `revise and rerun`, or `stop`. | `support_v1_pilot_decision_memo.md`, `support_v1_pilot_decision_memo_template.md` |

## Completion rule

- Mark the dry run complete only when every stage is either `complete` or explicitly closed as `blocked` with a recorded decision.
- Keep the final conclusion aligned with the same recommendation states already used in the pilot decision memo flow.
