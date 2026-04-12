# Support V1 Real Export Onboarding Checklist

This adds one concrete pre-ingest checklist for the first real customer or helpdesk export so `support_v1` can be onboarded through the current contract validation, normalization, labeled evaluation, and calibration-vs-baseline comparison flow without changing the core engine.

Use this before plugging a real export into any `support_v1` runner.

## Export source identification

- [ ] Identify the source system and export layout: raw hierarchical JSON, Zendesk-like JSON, flat CSV, or flat CSV plus explicit mapping.
- [ ] Record the exact source files, export timestamp, and ticket date range for the onboarding slice.
- [ ] Keep the first slice bounded and auditable. Prefer one small real export slice over a full backfill.
- [ ] Pick one tracked entity scope for the slice and keep it fixed: prefer account/org ID; use stable requester ID only if account ID is unavailable. Do not mix scopes inside one dataset.
- [ ] Select the matching current path before doing any repo-side work:
  - raw JSON -> `normalize_raw_support_export.py` / `run_support_raw_ingest_label_evaluation.py`
  - Zendesk-like JSON -> `helpdesk_adapter_zendesk_like.py` / `run_support_zendesk_like_label_evaluation.py`
  - fixed-contract CSV -> `normalize_raw_support_export_csv.py` / `run_support_csv_ingest_label_evaluation.py`
  - mapped CSV -> `normalize_mapped_support_export.py` / `run_support_mapped_ingest_label_evaluation.py`

## Required fields to confirm

- [ ] Confirm the export can reconstruct the current contract targets: entity/account identity, ticket identity, record identity, deterministic record order, actor role, source type, raw action, outcome, and details text.
- [ ] Confirm required joins are present and complete: entity -> ticket, ticket -> record, and actor/user -> record when users are separate.
- [ ] Confirm ticket open, ticket close, and record/event timestamps are present, ISO-8601, and include timezone offset or `Z`.
- [ ] Confirm each ticket has a stable external case code/id, subject/summary, and the channel/priority fields required by the selected ingest path.
- [ ] Confirm every record has usable detail text. For mapped CSV, `activity_detail` cannot be blank.

## Redaction / Privacy Checks

- [ ] Redact direct identifiers before the export enters the repo workspace: names, emails, phone numbers, account numbers, secrets, tokens, and attachment contents.
- [ ] Replace free-text bodies with short operational summaries when raw text contains customer PII or sensitive incident detail.
- [ ] Keep stable surrogate IDs after redaction so entity, ticket, and record joins still work.
- [ ] Verify label justifications and metadata do not reintroduce raw customer identifiers.
- [ ] Stop onboarding if the only usable signal depends on unredacted free text that cannot be stored safely.

## Identity Linkage Checks

- [ ] Check that one entity/account key resolves consistently across all tickets in the slice.
- [ ] Check that every ticket links to exactly one entity/account in the chosen scope.
- [ ] Check that every record links to a valid ticket and that there are no orphan comments/events/rows.
- [ ] Check merged, reopened, or duplicated tickets manually so the same history is not counted twice.
- [ ] Fail the slice if identity linkage is incomplete; current `support_v1` ingest assumes missing link targets are hard errors.

## Ticket / Event Ordering Checks

- [ ] Confirm record order can be rebuilt by timestamp first and record ID second.
- [ ] Check for missing timezone offsets, duplicated timestamps without stable record IDs, and imported rows that break deterministic ordering.
- [ ] Check that ticket open time is not after the first record and that close time is not before the final meaningful record.
- [ ] Spot-check one routine ticket and one escalated ticket end to end to confirm the visible history reads in the right order.
- [ ] Resolve ordering problems before labeling. A bad timeline will corrupt both replay and route labels.

## Label Creation Requirements

- [ ] Create a small first label pack on the real slice before broader rollout.
- [ ] For each labeled item, include `entity_id`, `ticket_id`, `decision_timestamp`, one route label, auxiliary flags, a one- or two-line justification, and labeler ID.
- [ ] Use the current route labels only: `should_route_fast_path` or `should_route_deep_path`.
- [ ] Use the current auxiliary flags only when supported by visible history: `trust_high`, `trust_low`, `contradiction_present`, `profile_too_stale`, `wrong_first_impression`.
- [ ] Label from the decision timestamp only. Do not use eventual resolution outcome except when explicitly assigning `wrong_first_impression`.
- [ ] Include a deliberate mix of routine, stale, contradictory, and escalated cases so the first pass can expose guardrail misses.

## Normalization Validation

- [ ] Run the existing contract gate first with `py use_cases/support_v1/validate_helpdesk_export_contract.py` or an equivalent invocation pointed at the real export.
- [ ] Run the matching normalizer/adapter and write one normalized artifact for the real slice.
- [ ] Spot-check that normalized records still carry the current minimum fields: `record_id`, `entity_id`, `ticket_id`, `timestamp`, `source_system`, `source_type`, `actor_role`, `raw_action`, `outcome`, `reliability`, `intensity`, and `metadata`.
- [ ] Confirm support-specific detail stays in `metadata` rather than expanding the `support_v1` event vocabulary.
- [ ] Convert the normalized cases into events and manually inspect at least one entity history to confirm the mapped events are plausible and auditable.

## First Evaluation Pass

- [ ] Run the matching labeled evaluation runner on the real export plus the real label pack.
- [ ] Review the JSON artifact and review CSV, not just the top-line accuracy.
- [ ] Check the same visible-history comparison already used in `support_v1`: `iml`, calibrated `iml`, `naive_summary`, and `full_history`.
- [ ] Check guardrail failures first: any `contradiction_present` or `profile_too_stale` label routed to `fast_path`, and any obvious `wrong_first_impression` case that never returns to `deep_path`.
- [ ] If calibrated `iml` improves over default `iml`, confirm the gain comes from clean support-history interpretation rather than bad mapping, label leakage, or timeline errors.
- [ ] Prefer fixing mapping, normalization, label quality, or slice composition before touching route thresholds. `support_v1` calibration is the current adjustment layer; core-engine changes are out of scope.

## Go / No-Go Criteria

- [ ] Go only if the export passes contract checks, privacy review, identity linkage checks, and ordering checks with no unresolved blockers.
- [ ] Go only if the normalized artifact is auditable and the first label pack can be reviewed from visible history without outcome leakage.
- [ ] Go only if the first evaluation pass shows no obvious guardrail regressions on contradiction/staleness cases.
- [ ] Go only if calibrated `iml` is at least not worse than default `iml` on the real slice and the baseline comparison is understandable enough to explain wins and losses against `naive_summary` and `full_history`.
- [ ] No-go if joins are incomplete, timestamps are not trustworthy, redaction is unsafe, labels rely on future knowledge, or evaluation results are dominated by mapping/order errors instead of real routing behavior.
