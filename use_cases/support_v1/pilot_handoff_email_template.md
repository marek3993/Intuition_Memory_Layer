# Support V1 Pilot Handoff Email Template

Subject: Request for first redacted helpdesk export slice for `support_v1` pilot

Hi team,

We are ready to run the first practical `support_v1` pilot on one small helpdesk export slice.

What we need:

- One redacted export slice in one of these formats: raw JSON, Zendesk-like JSON, flat CSV, or flat CSV plus a field mapping.
- Stable account/entity, ticket, and activity/comment/event IDs.
- Ticket open/close timestamps and activity timestamps with timezone information.
- Enough ticket/comment/event detail to reconstruct the support history for evaluation.

Privacy / redaction expectation:

- Please remove or mask direct identifiers such as names, emails, phone numbers, account numbers, secrets, tokens, and attachment contents.
- Keep stable surrogate IDs so joins between account, ticket, and activity records still work.

What the first test will do:

- Validate the export against the current contract.
- Normalize it into the existing `support_v1` prototype flow.
- Run a small first evaluation on labeled decision points from the visible support history.

What you will get back:

- A short intake/fit assessment.
- A pass/warn/fail view of export readiness.
- One initial pilot result summary showing whether the slice is usable for the next evaluation step.

Thanks,
