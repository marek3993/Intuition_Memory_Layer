# Support V1 Runbook

Run commands from the repository root.

## Raw-ingest prototype

Normalize the upstream-style raw support export into the existing `support_v1` case schema:

```powershell
py use_cases/support_v1/normalize_raw_support_export.py
```

This prototype adds one explicit ingest step before the current converter and evaluation flow:

- `use_cases/support_v1/raw_support_export_sample.json` models a more realistic upstream export with separate accounts, tickets, and records.
- `use_cases/support_v1/normalize_raw_support_export.py` maps that export into the existing support case schema and writes `use_cases/support_v1/artifacts/normalized_support_cases.json`.

## CSV raw-ingest prototype

Normalize a flat helpdesk-style CSV export into the existing `support_v1` case schema:

```powershell
py use_cases/support_v1/normalize_raw_support_export_csv.py
```

This prototype adds a CSV ingest path that:

- reads `use_cases/support_v1/raw_support_export_sample.csv`
- groups flat export rows by entity and ticket
- reconstructs ordered records in the existing support case schema
- writes `use_cases/support_v1/artifacts/normalized_support_cases_from_csv.json`

## Mapping-based CSV ingest prototype

Normalize a realistic flat helpdesk export through an explicit column-mapping file into the existing `support_v1` case schema:

```powershell
py use_cases/support_v1/normalize_mapped_support_export.py
```

This mapping-based ingest prototype adds:

- `use_cases/support_v1/helpdesk_export_mapping_template.json`, an explicit column map from external export fields into the current `support_v1` raw case schema
- `use_cases/support_v1/helpdesk_export_sample_generic.csv`, a more realistic flat export whose column names differ from the fixed sample
- `use_cases/support_v1/normalize_mapped_support_export.py`, a small adapter that reads the CSV plus mapping, groups rows by entity and ticket, and writes `use_cases/support_v1/artifacts/normalized_support_cases_from_mapping.json`

## Zendesk-like helpdesk adapter prototype

Normalize a small Zendesk-like export with nested users, tickets, comments, and audit-style events into the existing `support_v1` case schema:

```powershell
py use_cases/support_v1/helpdesk_adapter_zendesk_like.py
```

This Zendesk-like adapter adds:

- `use_cases/support_v1/zendesk_like_export_sample.json`, a compact export sample with organizations, users, tickets, comments, nested ticket metadata, timestamps, statuses, priorities, and channels
- `use_cases/support_v1/helpdesk_adapter_zendesk_like.py`, one explicit adapter that reads the sample export and writes `use_cases/support_v1/artifacts/normalized_support_cases_from_zendesk_like.json`

## Mapping-based CSV ingest labeled evaluation runner

Run the end-to-end mapping-based ingest flow:

```powershell
py use_cases/support_v1/run_support_mapped_ingest_label_evaluation.py
```

This runner adds one explicit mapped-CSV-to-label-eval path that:

- reads `use_cases/support_v1/helpdesk_export_sample_generic.csv`
- reads `use_cases/support_v1/helpdesk_export_mapping_template.json`
- reads the matching label pack `use_cases/support_v1/helpdesk_export_sample_generic_labels.json`
- normalizes the mapped external CSV into the existing support case schema
- runs the existing labeled decision-point evaluation on that normalized output
- writes `use_cases/support_v1/artifacts/latest_support_mapped_ingest_label_evaluation.json`
- writes `use_cases/support_v1/artifacts/latest_support_mapped_ingest_label_review.csv`

Override the CSV, mapping, or labels files if needed:

```powershell
py use_cases/support_v1/run_support_mapped_ingest_label_evaluation.py --csv-path C:\path\to\helpdesk_export.csv --mapping-path C:\path\to\helpdesk_mapping.json --labels-path C:\path\to\support_mapped_ingest_labels.json
```

## CSV ingest labeled evaluation runner

Run the end-to-end CSV ingest flow:

```powershell
py use_cases/support_v1/run_support_csv_ingest_label_evaluation.py
```

This runner adds one explicit CSV-ingest-to-label-eval path that:

- reads `use_cases/support_v1/raw_support_export_sample.csv`
- reads the CSV-compatible label pack `use_cases/support_v1/raw_support_export_sample_labels.json`
- normalizes the CSV export into the existing support case schema
- runs the existing labeled decision-point evaluation on that normalized output
- writes `use_cases/support_v1/artifacts/latest_support_csv_ingest_label_evaluation.json`
- writes `use_cases/support_v1/artifacts/latest_support_csv_ingest_label_review.csv`

Override the labels file if needed:

```powershell
py use_cases/support_v1/run_support_csv_ingest_label_evaluation.py --labels-path C:\path\to\support_csv_ingest_labels.json
```

## CSV ingest pack comparison runner

Run one compact comparison across CSV sample A, CSV sample B, and the in-memory combined A+B slice:

```powershell
py use_cases/support_v1/run_support_csv_ingest_pack_comparison.py
```

This flow reuses the existing CSV normalization plus labeled evaluation path, prints one compact table for `iml`, `calibrated_iml`, `naive_summary`, and `full_history`, and writes:

- `use_cases/support_v1/artifacts/support_csv_ingest_pack_comparison.json`
- `use_cases/support_v1/artifacts/support_csv_ingest_pack_comparison.md`

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

Raw-export normalization plus labeled decision-point evaluation:

```powershell
py use_cases/support_v1/run_support_raw_ingest_label_evaluation.py
```

This flow:

- reads `use_cases/support_v1/raw_support_export_sample.json`
- reads the native label pack `use_cases/support_v1/raw_support_export_sample_labels.json`
- normalizes it into the existing support case schema
- runs the existing labeled decision-point evaluation on that normalized output
- writes `use_cases/support_v1/artifacts/latest_support_raw_ingest_label_evaluation.json`
- writes `use_cases/support_v1/artifacts/latest_support_raw_ingest_label_review.csv`

The native raw-sample label set adds five hand-authored decision points across the three raw-export tickets, with a small mix of `fast_path` and `deep_path` outcomes plus targeted `contradiction_present`, `profile_too_stale`, and `wrong_first_impression` flags.

Override the labels file if needed:

```powershell
py use_cases/support_v1/run_support_raw_ingest_label_evaluation.py --labels-path C:\path\to\support_raw_ingest_labels.json
```

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

Run one compact comparison across pack A, pack B, pack C, pack D, and the in-memory combined A+B / A+B+C / A+B+C+D slices:

```powershell
py use_cases/support_v1/run_support_label_pack_comparison.py
```

This flow reuses the labeled decision-point evaluation logic, writes `use_cases/support_v1/artifacts/support_label_pack_comparison.json`, and prints one compact accuracy table for `iml`, `calibrated_iml`, `naive_summary`, and `full_history` across every slice.

It also writes:

- `use_cases/support_v1/artifacts/support_label_pack_comparison.md`, a compact human-readable summary that calls out the winner on `pack_a`, `pack_b`, `pack_c`, `pack_d`, `combined_ab`, `combined_abc`, and `combined_abcd`, along with the key accuracy deltas, route-quality metrics, diagnostics, and one overall takeaway
- `use_cases/support_v1/artifacts/support_label_pack_decision_memo.md`, a concise engineering recommendation memo that turns the comparison into an explicit winner summary, calibration readout, baseline position, main risks, and one recommended next step

## Quick inspection

Inspect the latest decision-point artifact with PowerShell:

```powershell
Get-Content use_cases/support_v1/artifacts/latest_support_label_evaluation.json
Get-Content use_cases/support_v1/artifacts/latest_support_label_evaluation.json | Select-String '"aggregate_summary"|"baseline_comparison"|"flag_breakdown"|"calibration"'
Import-Csv use_cases/support_v1/artifacts/latest_support_label_review.csv | Format-Table
Import-Csv use_cases/support_v1/artifacts/latest_support_label_errors.csv | Format-Table
Import-Csv use_cases/support_v1/artifacts/latest_support_label_route_changes.csv | Format-Table
```
