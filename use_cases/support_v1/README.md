# support_v1

`support_v1` is the first domain adapter that replays support-style case history through the existing Intuition Memory Layer.

In this use case, an entity is a stable external support subject such as an account or requester identity that appears across multiple tickets. The profile is not a ticket score and not an agent score. It is a rolling memory of how that external entity has behaved across prior cases.

The raw sample dataset is a small structured support export:

- one entity contains multiple cases
- one case contains ordered support records
- each record carries `record_id`, `timestamp`, `source_type`, `actor_role`, `raw_action`, `outcome`, and compact metadata

The adapter does three things:

1. loads the raw support cases
2. converts support conditions into the current generic IML event types only
3. writes canonical grouped event output and replays those events through the existing `iml/` engine

No support-specific fork of the core engine is introduced. The adapter only maps support semantics into:

- `fulfilled_commitment`
- `cooperative_response`
- `ignored_request`
- `contradiction_detected`
- `long_inactivity`

## Run

From the repository root:

```powershell
py use_cases/support_v1/convert_support_cases_to_events.py
```

This writes:

- `use_cases/support_v1/artifacts/support_events.json`

To run the end-to-end support evaluation:

```powershell
py use_cases/support_v1/run_support_evaluation.py
```

This:

- rebuilds the support event artifact
- replays each entity through the generic IML pipeline
- applies gap decay and final decay
- runs revalidation when triggered
- routes a low-stakes decision
- writes `use_cases/support_v1/artifacts/latest_support_evaluation.json`
