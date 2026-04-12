# Support V1 Real Export Intake Template

Use this for the first real helpdesk export slice before running contract validation, normalization, or labeled evaluation.

Keep the slice small, redacted, and auditable. Prefer one bounded entity/account scope and one small export sample over a broad backfill.

## Source system

- Source system name:
- Product / tenant / workspace:
- Export generated at:
- Ticket date range in slice:
- Notes:

## Export owner / contact

- Owner name:
- Team:
- Contact channel:
- Backup contact:
- Approval for redacted repo-safe slice confirmed: yes / no

## Export type and format

- Layout candidate: raw hierarchical JSON / Zendesk-like JSON / flat CSV / flat CSV plus mapping
- File format: json / csv / other
- Single file or multi-file export:
- Expected ingest path:
- Exported-at field present: yes / no

## Expected entity/account identifier

- Chosen entity scope for this slice: account / organization / requester / other
- Candidate stable entity field:
- Example value:
- Present across all tickets in slice: yes / no
- Join path into tickets:

## Ticket identifier

- Candidate stable ticket field:
- Candidate external case code/id field:
- Example ticket value:
- Ticket-to-entity join field:
- Ticket subject/summary field:

## Event/comment table sources

- Record source table(s) or file(s):
- One row/object per record: yes / no
- Separate comments source:
- Separate audit/events source:
- Ticket-to-record join field:
- Record identity field:
- Ordering tie-break field if timestamps collide:

## Timestamp fields

- Ticket opened timestamp field:
- Ticket closed timestamp field:
- Record/event timestamp field:
- Timestamp format sample:
- Timezone offset or `Z` present on all required timestamps: yes / no
- Known timestamp issues:

## Actor role fields

- Actor/user table or inline actor object:
- Raw actor role field:
- Actor join field if separate:
- Expected mapped roles: requester / agent / system / qa
- Known unmapped roles:

## Source type fields

- Raw source type field:
- Comment/event discriminator fields:
- Expected source type examples:
- Candidate mapping notes:

## Action / outcome / detail candidate fields

- Raw action candidate field:
- Outcome candidate field:
- Detail/body/note field:
- Ticket subject fallback usable when detail is blank: yes / no
- Support-specific metadata worth preserving:
- Known inference-only fields that need explicit review:

## Redaction / privacy notes

- Direct identifiers present:
- Free-text fields requiring summarization or masking:
- Attachment handling plan:
- Stable surrogate ID plan:
- Repo-safe redaction completed for first slice: yes / no

## Known gaps / risks

- Missing joins:
- Missing timestamps or timezone issues:
- Blank detail risk:
- Unsupported roles / source types / event types:
- Reopened / merged / duplicate ticket risk:
- Label leakage or outcome-lookahead risk:

## First test file path

- First redacted test file path:
- Companion files, if any:
- Field inventory CSV path:
- Planned labels file path:

## Onboarding decision

- Contract status: pass / warning / fail
- Normalization path to try first:
- Labeling slice approved: yes / no
- Go / no-go decision:
- Blocking issues to resolve before ingest:
- Owner for next step:

## Quick alignment checks

- Contract reconstruction targets are identifiable: entity/account, ticket, record order, actor role, source type, raw action, outcome, details.
- Deterministic ordering is available from record timestamp plus stable record ID.
- Current normalization can preserve support-specific details in `metadata` without expanding the event vocabulary.
- First label pack will use visible history only at each decision timestamp and current route labels/flags only.
