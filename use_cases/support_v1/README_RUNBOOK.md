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
- `use_cases/support_v1/artifacts/latest_support_label_review.csv`
- `use_cases/support_v1/artifacts/latest_support_label_errors.csv`
- `use_cases/support_v1/artifacts/latest_support_label_route_changes.csv`

The label evaluation artifact includes:

- run metadata and calibration mode
- aggregate label accuracy summary
- baseline comparison against `naive_summary` and `full_history`
- flagged-subset breakdown for the label flags
- per-label results, including calibration adjustments when `--calibrated` is enabled

The flat CSV review export keeps one row per labeled decision and makes it easier to scan:

- label identity and decision timestamp
- active method prediction versus the original IML and baseline predictions
- correctness flags for each method
- label flags and visible history size
- profile confidence, unknownness, freshness, contradiction load, and calibration adjustments

The focused CSV exports speed up review of the highest-signal subsets:

- `latest_support_label_errors.csv` keeps only rows where the active method prediction is wrong
- `latest_support_label_route_changes.csv` keeps only rows where `--calibrated` changes the routed path versus original IML; in default mode it is still written with header only

## Quick inspection

Inspect the latest decision-point artifact with PowerShell:

```powershell
Get-Content use_cases/support_v1/artifacts/latest_support_label_evaluation.json
Get-Content use_cases/support_v1/artifacts/latest_support_label_evaluation.json | Select-String '"aggregate_summary"|"baseline_comparison"|"flag_breakdown"|"calibration"'
Import-Csv use_cases/support_v1/artifacts/latest_support_label_review.csv | Format-Table
Import-Csv use_cases/support_v1/artifacts/latest_support_label_errors.csv | Format-Table
Import-Csv use_cases/support_v1/artifacts/latest_support_label_route_changes.csv | Format-Table
```
