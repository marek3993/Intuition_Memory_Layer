# Support V1 Expected Signals

This is a compact reference for whether `support_v1` outputs look sane under the current generic IML engine.

## Route-Driving Patterns

`contradiction_detected` should usually drive `deep_path` when:

- contradiction is recent and explicit in the visible support history
- contradiction appears alongside ignored requests or reopen-style instability
- contradiction load stays high enough that the route reason points to `contradiction_load above 0.35`

`long_inactivity` or long silent gaps should increase staleness and unknownness when:

- the entity has little recent evidence after a long gap
- old positive history is the main reason the profile still looks favorable
- repeated inactive periods interrupt otherwise small histories

Consistent follow-through should raise trust when:

- multiple `fulfilled_commitment` or `cooperative_response` events arrive with decent reliability
- the events are recent enough that decay has not already erased freshness
- later events do not introduce visible contradiction

## Expected Healthy Behavior

Plausible `fast_path`:

- recent event history
- low contradiction
- low unknownness
- enough evidence for `overall_confidence >= 0.55`
- low-stakes next step
- support-visible behavior that looks cooperative or predictable, even if not perfect

Plausible `deep_path`:

- contradiction is already visible
- the profile is stale, sparse, or heavily decayed
- the entity looks routine only because there is not enough recent evidence
- the route reason cites low confidence, low freshness, high contradiction, or high unknownness

## Wrong First Impression

A wrong first impression in support looks like:

- one or two early clean resolutions make the entity appear easy to trust
- the history is still thin, but the surface impression suggests `fast_path`
- later tickets add ignored requests, contradiction, or long silence
- the profile fails to move back toward `deep_path` quickly enough

The reverse case also matters:

- early missed follow-through or silence makes the entity look risky
- later repeated follow-through and cooperative responses stay consistent
- trust, predictability, and confidence should recover enough that routine low-stakes handling can become `fast_path`

## Sanity Checks By Signal

Trust should rise when:

- requested artifacts are provided
- the customer confirms fixes after agreed next steps
- useful follow-up repeats across cases

Unknownness should rise when:

- the entity has few events overall
- the only evidence is old
- inactivity breaks continuity and no new confirming evidence arrives

Freshness should fall when:

- there are long gaps between meaningful interactions
- the current route depends mostly on old history

`fast_path` is suspicious when:

- contradiction is visible
- silence or no-response patterns are recent
- the profile is being carried by old wins rather than recent evidence

`deep_path` is suspicious when:

- the entity has several recent cooperative or fulfilled-commitment events
- contradiction is low
- unknownness is low enough that the profile should support a routine next step

## Current Engine Reminder

Under the current engine, the route is mainly justified by:

- `overall_confidence`
- `freshness`
- `contradiction_load`
- `unknownness`

Direct `trust` improvement alone is not enough for `fast_path` if the profile is still stale, contradictory, or too unknown.
