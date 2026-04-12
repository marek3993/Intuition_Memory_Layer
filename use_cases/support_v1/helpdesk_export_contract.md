# Support V1 Helpdesk Export Contract

This contract defines the minimum external export shape that `support_v1` can ingest before normalization. It is intentionally narrow and matches the current adapter assumptions in this folder.

The validator for this contract is:

```powershell
py use_cases/support_v1/validate_helpdesk_export_contract.py
```

## Required logical reconstruction targets

Every accepted export must let `support_v1` reconstruct:

- entity/account identity
- ticket identity and entity linkage
- record identity and deterministic record order
- actor role
- source type
- raw action
- outcome
- details text

The current ingest path assumes one support account contains one or more tickets, and each ticket contains one or more ordered records.

## Timestamp rules

Required timestamps must:

- be present
- be ISO-8601 strings
- include a timezone offset or `Z`

The minimum required timestamps are:

- ticket open timestamp
- ticket close timestamp
- record/event timestamp

`exported_at` is useful but not required for `support_v1` ingest.

## Identity linkage rules

At minimum, the export must support these joins:

- entity/account key -> ticket entity/account link
- ticket key -> record ticket link
- actor/user key -> record actor link when the source model uses separate users

If a link target is missing, ingest must fail.

## Supported source layouts

The validator currently accepts three concrete layouts because those are the layouts already exercised in `support_v1`.

### 1. Raw hierarchical JSON

Top-level collections:

- `accounts`
- `tickets`
- `records`

Required `accounts[]` fields:

- `account_ref`: stable account key used by tickets
- `entity_id`: stable entity/account id emitted into the normalized entity
- `display_name`: account name
- `segment`: account segment/tier

Required `tickets[]` fields:

- `ticket_ref`: stable ticket key used by records
- `case_id`: external case code
- `account_ref`: joins to `accounts[].account_ref`
- `opened_at`
- `closed_at`
- `channel`
- `priority`
- `subject`

Required `records[]` fields:

- `event_ref`: stable record id
- `ticket_ref`: joins to `tickets[].ticket_ref`
- `occurred_at`
- `source_system`
- `source_type`
- `actor.role`
- `event_name`

Record detail behavior:

- `body` is preferred
- if `body` is empty, the adapter may fall back to the ticket `subject`

Current supported raw values:

- `source_type`: `message`, `ticket_status`, `workflow_timer`, `audit_entry`
- `actor.role`: `customer`, `support_agent`, `automation`, `qa_analyst`
- `event_name`: `ticket_created`, `agent_requested_logs`, `customer_supplied_artifacts`, `customer_confirmed_resolution`, `requester_deadline_elapsed`, `customer_replied_without_artifacts`, `qa_flagged_conflict`

### 2. Zendesk-like JSON

Top-level collections:

- `organizations`
- `users`
- `tickets`
- `comments`
- `events`

Required `organizations[]` fields:

- `organization_id`: stable organization key used by tickets and users
- `entity_id`: normalized entity/account id
- `name`: account name

Recommended `organizations[]` field:

- `details.segment`: preferred account segment; missing segment downgrades to a warning because the current adapter can fall back to `unknown`

Required `users[]` fields:

- `user_id`
- `role`
- `name`

Required `tickets[]` fields:

- `id`
- `external_id`
- `organization_id`: joins to `organizations[].organization_id`
- `requester_id`: joins to `users[].user_id`
- `created_at`
- `closed_at`
- `status`
- `subject`

Recommended `tickets[]` fields:

- `via.channel`: preferred channel; missing value becomes a warning because the current adapter can fall back to `unknown`
- `priority`: preferred priority; missing value becomes a warning because the current adapter can fall back to `unknown`

Required `comments[]` fields:

- `comment_id`
- `ticket_id`: joins to `tickets[].id`
- `created_at`
- `author_id`: joins to `users[].user_id`

Required `events[]` fields:

- `event_id`
- `ticket_id`: joins to `tickets[].id`
- `created_at`
- `author_id`: joins to `users[].user_id`
- `type`

Record detail behavior:

- `comments[].body` is preferred
- `events[].note` is preferred
- if either is empty, the adapter may fall back to the ticket `subject`

Current supported Zendesk-like values:

- `users.role`: `end_user`, `agent`, `system`, `qa`
- `events.type`: `status_change`, `sla_breach`, `qa_review`

Current supported comment inference shapes:

- first requester comment on a ticket -> `ticket_opened` / `issue_reported`
- requester comment with `metadata.fulfills_request == true` -> `provided_requested_info` / `requested_artifacts_uploaded`
- requester comment with `metadata.followup_without_requested_info == true` -> `followed_up_without_requested_info` / `reply_missing_requested_artifacts`
- agent comment with `metadata.request_id` -> `requested_diagnostics` / `diagnostics_requested`

If a comment does not match one of those shapes, ingest must fail.

### 3. Flat helpdesk CSV

The CSV contract is defined at the logical field level. The current sample uses these required columns:

- `customer_account_key`
- `customer_name`
- `customer_tier`
- `helpdesk_ticket_ref`
- `case_code`
- `case_opened_ts`
- `case_closed_ts`
- `intake_channel`
- `case_priority`
- `case_subject`
- `activity_id`
- `event_occurred_ts`
- `platform_name`
- `activity_kind`
- `performed_by_role`
- `normalized_action`
- `normalized_outcome`
- `activity_detail`

Rules for flat CSV exports:

- each row is one record
- entity/account fields must stay consistent for the same `customer_account_key`
- ticket fields must stay consistent for the same `helpdesk_ticket_ref`
- `activity_id` must be stable within a ticket
- record order is reconstructed by `event_occurred_ts`, then `activity_id`

Required CSV actor role values:

- `requester`
- `agent`
- `system`
- `qa`

For the current mapped CSV ingest path, `activity_detail` is required. There is no built-in fallback from blank row detail to ticket subject in that path.

## Minimum field coverage by reconstruction target

### Entity/account

Minimum fields:

- stable entity/account id
- account display name
- stable ticket-to-account link

The current adapters also expect a segment/tier value, except for the Zendesk-like adapter where missing segment falls back to `unknown`.

### Ticket

Minimum fields:

- stable ticket id/reference
- external case code/id
- entity/account link
- open timestamp
- close timestamp
- subject/summary

Channel and priority are also required for the raw JSON and flat CSV paths. In the Zendesk-like path they may be missing, but that is only a warning because the adapter falls back to `unknown`.

### Record order

Minimum fields:

- stable record id
- record timestamp
- ticket link

Order is reconstructed by timestamp first and record id second.

### Actor role

Minimum fields:

- a role value that maps to one of the current normalized roles: `requester`, `agent`, `system`, `qa`

### Source type

Minimum fields:

- a source/event type string that the current adapter can either pass through directly or map explicitly

### Raw action

Minimum fields:

- either a direct raw action field
- or enough upstream signal to infer it deterministically

For Zendesk-like comments, deterministic inference means one of the supported comment shapes listed above.

### Outcome / details

Minimum fields:

- a deterministic outcome string or enough upstream signal to infer it
- detail text for the record

Raw JSON and Zendesk-like JSON may fall back from empty record detail to the ticket subject. The current flat CSV path may not.

## Hard failures

These are contract failures and should block normalization:

- missing required top-level collections for a supported layout
- missing required ids, links, timestamps, or required text fields
- invalid timestamp format
- timestamp without timezone
- record references unknown ticket
- ticket references unknown entity/account
- user/author/requester references unknown user in the Zendesk-like layout
- unsupported raw role, source type, event name, user role, or event type when the adapter requires explicit mapping
- unsupported Zendesk-like comment shape
- duplicate entity/account keys, ticket keys, or duplicate record ids within the same ticket
- a ticket with zero records
- inconsistent repeated entity/ticket fields in flat CSV rows

## Soft warnings

These do not block normalization, but the validator should surface them:

- missing `exported_at`
- missing optional actor identity such as actor id, email, or display name
- missing Zendesk-like `details.segment`
- missing Zendesk-like `via.channel`
- missing Zendesk-like `priority`
- blank raw/Zendesk-like record detail when the adapter can fall back to the ticket subject
- timestamps that are syntactically valid but fall outside the ticket open/close window

## Contract intent

This contract is not a generic helpdesk schema. It is the smallest concrete contract needed for the current `support_v1` adapters to normalize external support exports into the existing support case schema without changing the core engine.
