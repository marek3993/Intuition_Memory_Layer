# Support V1 Labeling Guide

## Labeling Goal

Label support decision points, not entire tickets in the abstract.

Each labeled item should represent:

- one `entity_id`
- one `ticket_id`
- one decision timestamp
- the event history visible at that timestamp
- the current profile snapshot or enough raw history to recreate it

The main question is whether the current evidence is strong enough for `fast_path` or whether the case should go to `deep_path`.

## Label Set

Use one required route label and a small set of auxiliary flags.

Required route label:

- `should_route_fast_path`
- `should_route_deep_path`

These are mutually exclusive. Pick exactly one.

Auxiliary flags:

- `trust_high`
  - the requester or account can be taken at face value for the next low-stakes step
- `trust_low`
  - the requester or account should not be taken at face value without extra checking
- `contradiction_present`
  - the visible history contains materially conflicting claims or evidence
- `profile_too_stale`
  - the visible history is too old, too sparse, or too interrupted to support a confident route
- `wrong_first_impression`
  - later evidence shows that the likely initial route impression was wrong

`trust_high` and `trust_low` are also mutually exclusive. If the case is too sparse to judge, leave both false and rely on `profile_too_stale`.

## Route Label Criteria

Mark `should_route_fast_path` when all of these are broadly true:

- the next step is low stakes
- the visible history is recent enough
- the requester has been cooperative or consistent enough
- no material contradiction is already visible
- a standard handling path is unlikely to create avoidable rework

Mark `should_route_deep_path` when any of these are true:

- contradiction or instability is already visible
- the history is stale or too thin
- the next step depends on specialist review or careful fact-checking
- the likely cost of a wrong first move is high
- the ticket looks routine only because important context is missing

Do not use staffing pressure or queue load as a label rule. The label should reflect what the case deserves, not what the team had time to do.

## Who Should Label

Good first labelers:

- support lead or escalation lead
- QA reviewer with ticket-audit experience
- experienced frontline agent with a short calibration pass

Minimum acceptable setup:

- one primary labeler for all cases
- one second reviewer on a 20 percent sample
- adjudication on route disagreements and `wrong_first_impression` cases

Avoid using only junior agents without calibration. The labels require judgment about contradiction, evidence sufficiency, and whether the first route would have been unsafe.

## Minimum Viable Labeled Dataset

A useful first labeled set is small but intentionally mixed.

Recommended minimum:

- 120 to 150 labeled decision points
- 40 to 60 likely `fast_path` cases
- 40 to 60 likely `deep_path` cases
- at least 20 `contradiction_present` cases
- at least 20 `profile_too_stale` cases
- 30 to 50 full-ticket timelines eligible for `wrong_first_impression`

Per labeled item, keep:

- `entity_id`
- `ticket_id`
- decision timestamp
- visible event history or normalized record slice
- chosen route label
- auxiliary flags
- short justification, one or two lines max
- labeler ID

## Consistency Rules

Apply these rules to reduce label drift.

- Label from the decision timestamp only. Do not look ahead unless you are explicitly assigning `wrong_first_impression`.
- Keep entity scope fixed. Do not sometimes label per requester and sometimes per account.
- Treat contradiction as evidence conflict, not mere frustration or negative tone.
- Treat staleness as an evidence-timing problem, not a trust problem.
- `trust_low` does not require bad intent. Repeated inconsistency or low follow-through is enough.
- `should_route_deep_path` can be correct even when the requester is cooperative if the evidence is still thin or stale.
- A ticket being hard does not automatically imply `trust_low`.

## Common Failure Modes In Labeling

- Outcome leakage: the ticket was eventually solved, so the labeler retroactively marks early `fast_path` as correct.
- Agent-performance leakage: slow or weak agent handling gets mislabeled as requester unreliability.
- Overusing contradiction: changing details during troubleshooting is not automatically a true contradiction.
- Underusing staleness: old but positive history is still stale history.
- Collapsing route and trust into one judgment: routing depends on freshness, contradiction, and unknownness, not trust alone.

## Review Pass

After the first labeling pass, review disagreements in three buckets:

- route disagreement
- contradiction disagreement
- wrong-first-impression disagreement

If disagreement is frequent, tighten the examples and decision rules before expanding the dataset. The v1 goal is a stable small truth set, not maximum coverage.
