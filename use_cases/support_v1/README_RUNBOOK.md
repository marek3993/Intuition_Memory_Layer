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

Default labeled decision-point evaluation:

```powershell
py use_cases/support_v1/run_support_label_evaluation.py
```

Calibrated labeled decision-point evaluation:

```powershell
py use_cases/support_v1/run_support_label_evaluation.py --calibrated
```

Pack B labeled decision-point evaluation:

```powershell
py use_cases/support_v1/run_support_label_evaluation.py --cases-path use_cases/support_v1/sample_support_cases_pack_b.json --labels-path use_cases/support_v1/sample_support_labels_pack_b.json
```

Calibrated pack B labeled decision-point evaluation:

```powershell
py use_cases/support_v1/run_support_label_evaluation.py --calibrated --cases-path use_cases/support_v1/sample_support_cases_pack_b.json --labels-path use_cases/support_v1/sample_support_labels_pack_b.json
```

Labeled decision-point evaluation against explicit files:

```powershell
py use_cases/support_v1/run_support_label_evaluation.py --cases-path C:\path\to\support_cases.json --labels-path C:\path\to\support_labels.json
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

Dataset switching adds explicit `--cases-path` and `--labels-path` selection to the runner. If you omit both flags, it still uses the existing pack A defaults; if you pass them, the runner uses that cases/labels pair directly without any inline PowerShell patching.

## Label pack comparison runner

Run one compact comparison across pack A, pack B, and the in-memory combined A+B slice:

```powershell
py use_cases/support_v1/run_support_label_pack_comparison.py
```

This flow reuses the labeled decision-point evaluation logic, writes `use_cases/support_v1/artifacts/support_label_pack_comparison.json`, and prints a compact accuracy table for `iml`, `calibrated_iml`, `naive_summary`, and `full_history`.

It also writes `use_cases/support_v1/artifacts/support_label_pack_comparison.md`, a compact human-readable summary that calls out the winner on `pack_a`, `pack_b`, and `combined`, along with the key accuracy deltas, route-quality metrics, diagnostics, and one overall takeaway.

## Quick inspection

Inspect the latest decision-point artifact with PowerShell:

```powershell
Get-Content use_cases/support_v1/artifacts/latest_support_label_evaluation.json
Get-Content use_cases/support_v1/artifacts/latest_support_label_evaluation.json | Select-String '"aggregate_summary"|"baseline_comparison"|"flag_breakdown"|"calibration"'
Import-Csv use_cases/support_v1/artifacts/latest_support_label_review.csv | Format-Table
Import-Csv use_cases/support_v1/artifacts/latest_support_label_errors.csv | Format-Table
Import-Csv use_cases/support_v1/artifacts/latest_support_label_route_changes.csv | Format-Table
```
