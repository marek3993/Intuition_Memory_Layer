# support_v1 schema

## Entity

`entity_id` is the stable support subject whose history should accumulate across tickets.

In the sample dataset that means an account-style identifier such as `acct_northwind`. The memory target is the external requester/account behavior over time, not the behavior of the support team.

## Raw Support Case Schema

The raw dataset is a JSON object with this shape:

```json
{
  "dataset_name": "support_v1_sample",
  "entity_type": "support_account",
  "entities": [
    {
      "entity_id": "acct_northwind",
      "account_name": "Northwind Solar",
      "segment": "mid_market",
      "cases": [
        {
          "case_id": "NW-1001",
          "opened_at": "2026-01-06T08:15:00+00:00",
          "closed_at": "2026-01-06T15:40:00+00:00",
          "channel": "email",
          "priority": "normal",
          "summary": "API timeout after key rotation",
          "records": [
            {
              "record_id": "NW-1001-R3",
              "timestamp": "2026-01-06T10:02:00+00:00",
              "source_system": "helpdesk_demo",
              "source_type": "ticket_comment",
              "actor_role": "requester",
              "raw_action": "provided_requested_info",
              "outcome": "complete_context_provided",
              "details": "Uploaded sanitized logs and curl output.",
              "metadata": {
                "request_id": "diag-1",
                "response_quality": "complete",
                "fulfills_request": true
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### Required raw fields

Case-level:

| Field | Type | Meaning |
| --- | --- | --- |
| `case_id` | string | Stable ticket identifier |
| `opened_at` | ISO-8601 timestamp | Case start time |
| `closed_at` | ISO-8601 timestamp | Case end time |
| `channel` | string | Support channel |
| `priority` | string | Operational priority |
| `summary` | string | Short redacted case description |
| `records` | list | Ordered support records for that case |

Record-level:

| Field | Type | Meaning |
| --- | --- | --- |
| `record_id` | string | Stable record identifier |
| `timestamp` | ISO-8601 timestamp | When the raw support event happened |
| `source_system` | string | Export source |
| `source_type` | string | `ticket_comment`, `status_change`, `system_timer`, or `qa_review` |
| `actor_role` | string | `requester`, `agent`, `system`, or `qa` |
| `raw_action` | string | Structured support action |
| `outcome` | string | Structured result |
| `details` | string | Short redacted note for auditability |
| `metadata` | object | Support-specific fields such as request IDs, severity, or due windows |

## Normalized Interpretation

The adapter does not treat every raw support record as a canonical IML event.

Instead it applies these normalization rules:

1. preserve the support export structure exactly enough to audit where a signal came from
2. convert only requester-facing behavior into IML evidence
3. ignore support-team operational events that describe agent behavior rather than entity behavior
4. derive `long_inactivity` at the entity timeline level when long gaps appear between meaningful support signals

Normalized event fields:

| Field | Meaning |
| --- | --- |
| `event_id` | deterministic `record_id:event_type` or gap-derived ID |
| `entity_id` | copied from the parent entity |
| `timestamp` | raw record time or derived gap timestamp |
| `event_type` | one of the current five generic IML event types |
| `source` | inspectable support source such as `support_ticket_comment` |
| `reliability` | deterministic confidence based on source type and condition |
| `polarity` | `+1.0` for cooperative/follow-through signals, `-1.0` for negative signals |
| `intensity` | deterministic weight based on response quality, missed count, contradiction severity, or gap length |
| `metadata` | case ID, record ID, summary, raw action, outcome, and support-specific details |

## Mapping Into Current Generic IML Events

The adapter stays inside the current generic IML vocabulary only.

| Support condition | IML event | Rule |
| --- | --- | --- |
| Requester opens a ticket with useful initial context | `cooperative_response` | Only when `raw_action=ticket_opened` and `metadata.initial_context_quality` is `useful` or `complete` |
| Requester provides requested logs, screenshots, or context | `cooperative_response` | `raw_action=provided_requested_info` |
| Requester follows through on a requested step or confirms a fix | `fulfilled_commitment` | `raw_action=provided_requested_info` with `metadata.fulfills_request=true`, `completed_requested_step`, or `confirmed_fix` |
| Request expires without requester response | `ignored_request` | `raw_action=request_deadline_missed` from a structured timer |
| Requester replies again without the requested information | `ignored_request` | `raw_action=followed_up_without_requested_info` |
| QA review or reopen flow confirms conflicting claims | `contradiction_detected` | `raw_action=qa_marked_contradiction` or `reopened_with_conflicting_claim` |
| Long gap between meaningful entity signals | `long_inactivity` | Derived after conversion when the gap between consecutive entity events is at least 30 days |

### Deterministic mapping details

- `cooperative_response`
  - polarity: `+1.0`
  - reliability: based on source type, typically `0.78` for requester comments
  - intensity: based on context quality or response quality

- `fulfilled_commitment`
  - polarity: `+1.0`
  - reliability: based on source type with a small positive reliability bump for explicit follow-through
  - intensity: based on whether the requester completed the requested step or confirmed the fix

- `ignored_request`
  - polarity: `-1.0`
  - reliability: highest when emitted from `system_timer`
  - intensity: scales with repeated misses or repeated replies without the requested information

- `contradiction_detected`
  - polarity: `-1.0`
  - reliability: highest for `qa_review`
  - intensity: scales with contradiction severity

- `long_inactivity`
  - polarity: `-1.0`
  - reliability: `0.90`
  - intensity: scales with gap length, capped at `1.0`

## Example Canonical Event

```json
{
  "event_id": "BO-2148-R3:contradiction_detected",
  "entity_id": "acct_blueorbit",
  "timestamp": "2026-03-21T13:20:00+00:00",
  "event_type": "contradiction_detected",
  "source": "support_qa_review",
  "reliability": 0.95,
  "polarity": -1.0,
  "intensity": 1.0,
  "metadata": {
    "case_id": "BO-2148",
    "record_id": "BO-2148-R3",
    "raw_action": "qa_marked_contradiction",
    "outcome": "claim_conflicts_with_prior_confirmation",
    "summary": "Customer says the patch never worked despite earlier confirmation."
  }
}
```

This keeps the support interpretation in the adapter layer while leaving `iml/` unchanged.
