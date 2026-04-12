# Support V1 Runbook

Run commands from the repository root.

## Full-entity replay runner

Rebuild the grouped support event artifact:

```powershell
py use_cases/support_v1/convert_support_cases_to_events.py
```

Run the full-entity replay evaluation:

```powershell
py use_cases/support_v1/run_support_evaluation.py
```

Run the full-entity replay evaluation with support-only calibration enabled:

```powershell
py use_cases/support_v1/run_support_evaluation.py --calibrated
```

This flow replays each support entity end to end and writes:

- `use_cases/support_v1/artifacts/support_events.json`
- `use_cases/support_v1/artifacts/latest_support_evaluation.json`

## Labeled decision-point runner

Run the labeled decision-point evaluation:

```powershell
py use_cases/support_v1/run_support_label_evaluation.py
```

Run the labeled decision-point evaluation with support_v1 calibration enabled:

```powershell
py use_cases/support_v1/run_support_label_evaluation.py --calibrated
```

This flow replays only the history visible at each labeled `decision_timestamp`, compares the routed path against the hand-authored label, and writes:

- `use_cases/support_v1/artifacts/latest_support_label_evaluation.json`

The label evaluation artifact includes:

- run metadata and calibration mode
- aggregate label accuracy summary
- baseline comparison against `naive_summary` and `full_history`
- flagged-subset breakdown for the label flags
- per-label results, including calibration adjustments when `--calibrated` is enabled

## Quick inspection

Inspect the latest decision-point artifact with PowerShell:

```powershell
Get-Content use_cases/support_v1/artifacts/latest_support_label_evaluation.json
Get-Content use_cases/support_v1/artifacts/latest_support_label_evaluation.json | Select-String '"aggregate_summary"|"baseline_comparison"|"flag_breakdown"|"calibration"'
```
