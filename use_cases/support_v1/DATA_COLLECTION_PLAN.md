# Support V1 Data Collection Plan

## Goal

Move from the synthetic MVP to a small semi-real support dataset that can be replayed through the current IML path:

`raw support record -> normalized record -> Event list -> EvidenceUnit updates -> IntuitionProfile -> fast_path/deep_path evaluation`

For `support_v1`, keep one tracked entity per requester or account. Pick one identifier and use it consistently across the dataset. Prefer `account_id`; fall back to a stable requester email hash if account IDs are unavailable.

## Raw Data Sources

Use structured exports first. Avoid making free-form text the primary source of truth in v1.

- Helpdesk ticket export: ticket ID, requester/account ID, timestamps, assignee changes, status changes, tags, SLA timestamps, resolution state.
- Ticket comment export: public replies, internal notes, author role, reply timing, attachments present, requested-info markers.
- QA or support review sheet: manual flags for escalation quality, contradiction, missing info, and whether the initial handling path was appropriate.
- Optional CRM/account context: plan tier, account priority, or known account owner. Use only as metadata, not as a routing target.
- Optional incident/escalation log: specialist handoff timestamps, escalation reason, reopen reason.

Good first systems are Zendesk, Intercom, Freshdesk, Jira Service Management, or any internal CSV/JSON export with similar fields.

## Minimum Fields

Each raw record needs enough information to produce a canonical `Event` and to audit where it came from.

Minimum normalized fields:

- `record_id`
- `entity_id`
- `ticket_id`
- `timestamp`
- `source_system`
- `source_type`
- `actor_role`
- `raw_action`
- `outcome`
- `reliability`
- `intensity`
- `metadata`

Minimum fields needed for the final IML event:

- `event_id`
- `entity_id`
- `timestamp`
- `event_type`
- `source`
- `reliability`
- `polarity`
- `intensity`
- `metadata`

`metadata` should carry support-specific detail such as `ticket_id`, `channel`, `sla_state`, `requested_info_type`, `escalated`, `reopened`, `priority`, and a short redacted reason string.

## Export Or Mocking Approach

Start with one bounded export slice, not a full warehouse pull.

Recommended first slice:

- 100 to 200 resolved tickets
- 30 to 60 distinct entities
- last 60 to 90 days
- include both straightforward and escalated cases
- include reopened tickets and long-response-gap tickets on purpose

Practical export path:

1. Export tickets and comments from the helpdesk as CSV or JSON.
2. Redact direct identifiers and free-form PII before the data enters the repo workspace.
3. Normalize into one row per support interaction or system transition.
4. Produce a second artifact with one canonical IML event per row.

If semi-real export is blocked, build a mock dataset from real operational patterns:

- keep real timestamp spacing, ticket state changes, and escalation outcomes
- replace message text with short redacted summaries
- preserve agent/customer role, timing, and contradiction structure
- do not invent labels directly from the desired routing outcome

## Converting Support Records Into Event Streams

Do not expand the IML event vocabulary in `support_v1`. Map support records into the existing event types and keep extra detail in `metadata`.

Suggested mapping:

- `fulfilled_commitment`
  - requester supplied logs or requested steps by the promised time
  - requester confirmed a fix after agreeing to test
  - requester followed through on a required next action
- `cooperative_response`
  - requester answered clarifying questions promptly
  - requester provided partial but useful context
  - requester stayed aligned with the troubleshooting flow
- `ignored_request`
  - requester did not respond within the defined waiting window after a clear next action
  - requester replied without the requested information multiple times
- `contradiction_detected`
  - requester statements conflict with earlier statements, attached evidence, or prior ticket history
  - duplicate or reopened tickets contain materially incompatible claims
- `long_inactivity`
  - long gap since the last meaningful interaction for the same entity

Implementation notes:

- Use structured system events for higher `reliability` than agent-authored notes.
- Keep `intensity` proportional to operational significance. Missing a minor clarification is weaker than refusing repeated mandatory steps.
- Set `source` to something inspectable such as `zendesk_comment`, `zendesk_status_change`, `qa_review`, or `crm_flag`.
- Keep `polarity` simple in v1. Positive cooperative or follow-through events can be `+1.0`; ignored or contradictory events can be `-1.0`.

The first event stream should stay small and auditable. A reviewer should be able to inspect one ticket and understand why each event exists.

## First Evaluation Loop

Use a replay-and-review loop close to the existing synthetic runner.

1. Build a small normalized export and convert it into canonical IML events grouped by `entity_id`.
2. Replay each entity history into an `IntuitionProfile` using the current extractor, decay, revalidation, and routing logic.
3. Define one decision point per ticket:
   usually the first meaningful routing point after the opening message and initial clarification.
4. Compare the IML route at that decision point against lightweight human labels from `LABELING_GUIDE.md`.
5. Review false `fast_path`, false `deep_path`, and `wrong_first_impression` cases.
6. Adjust only mapping rules, reliability calibration, intensity calibration, and evaluation slicing before changing core thresholds.

First-pass metrics:

- `fast_path` precision
- `deep_path` recall
- count of `contradiction_present` cases sent to `fast_path`
- count of `profile_too_stale` cases sent to `fast_path`
- wrong-first-impression rate
- reviewer agreement on route labels

## Data Risks

- Entity boundary drift: mixing account-level and requester-level histories will corrupt the profile.
- Label leakage: using final resolution outcome to justify an earlier routing decision can overstate performance.
- Support-side behavior mixed with requester behavior: the current event vocabulary models the tracked entity, so avoid turning agent delay into requester unreliability.
- Source reliability drift: internal notes, status automations, and QA reviews should not all carry the same reliability.
- Duplicate history: merged tickets, reopened tickets, and channel duplication can inflate evidence counts.
- Sparse histories: many entities will have too little recent evidence, which should surface as unknownness or staleness rather than forced confidence.
- Privacy and redaction failures: free-form ticket text may contain PII or secrets.
- Class imbalance: most tickets may look routine, which can make `fast_path` appear stronger than it is.
- Timestamp quality: missing timezone handling or imported update order can break decay behavior.

## V1 Deliverable

The v1 data package should be enough to inspect manually and small enough to relabel quickly:

- one raw redacted export slice
- one normalized support-interaction artifact
- one canonical IML event artifact
- one labeled decision-point sheet
- one evaluation run summary with error review notes
