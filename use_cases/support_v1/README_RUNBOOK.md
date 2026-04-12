# Support V1 Runbook

Run from the repository root:

```powershell
py use_cases/support_v1/convert_support_cases_to_events.py
```

This converts `use_cases/support_v1/sample_support_cases.json` into:

- `use_cases/support_v1/artifacts/support_events.json`

Run the end-to-end support evaluation:

```powershell
py use_cases/support_v1/run_support_evaluation.py
```

This rebuilds the support event artifact, replays each support entity through the generic IML pipeline, and writes:

- `use_cases/support_v1/artifacts/latest_support_evaluation.json`

Generated artifacts:

- `support_events.json`: grouped derived generic events per support entity
- `latest_support_evaluation.json`: run metadata, aggregate summary, and per-entity evaluation results

Inspect outputs with PowerShell:

```powershell
Get-Content use_cases/support_v1/artifacts/support_events.json
Get-Content use_cases/support_v1/artifacts/latest_support_evaluation.json
Get-Content use_cases/support_v1/artifacts/latest_support_evaluation.json | Select-String '"aggregate_summary"|"selected_path"|"reason"'
```

Current next step after this sample run: build a labeled per-decision-point support slice and replay only the history visible at each ticket decision timestamp, then measure route accuracy before changing the engine.
