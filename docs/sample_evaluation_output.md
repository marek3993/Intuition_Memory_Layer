# Sample Evaluation Output

Illustrative sample output from the current `run_evaluation.py` runner. This is a curated excerpt for readability, not a canonical benchmark result.

## Example entity summary

```text
=== Entity Summary: entity_stable_good_01 ===
scenario: stable_good_actor
event_count: 15
decay_checkpoints: 0
final_decision_gap_days: 7
first_impression_trust: 0.84
final_trust: 1.00
overall_confidence: 0.51
unknownness: 0.54
freshness: 0.79
contradiction_load: 0.00
revalidation_triggered: False
revalidation_reasons: none
iml_selected_path: deep_path
naive_summary_selected_path: fast_path
naive_summary_decision_reason: Baseline score is confident, low-risk, low-contradiction, and low-unknown.
full_history_selected_path: fast_path
full_history_decision_reason: Baseline score is confident, low-risk, low-contradiction, and low-unknown.
iml_decision_reason: overall_confidence below 0.55, unknownness above 0.45
```

## Example aggregate metrics block

```text
=== Aggregate Metrics ===
entities_evaluated: 5
total_events_replayed: 59
decay_checkpoints_applied: 7
revalidations_triggered: 3
fast_path_count: 0
deep_path_count: 5
average_overall_confidence: 0.37
average_unknownness: 0.65
false_first_impression_recovery_proxy: 1.00
```

## Example baseline comparison block

```text
=== Baseline Comparison ===
iml_fast_path_count: 0
iml_deep_path_count: 5
naive_summary_fast_path_count: 3
naive_summary_deep_path_count: 2
full_history_fast_path_count: 2
full_history_deep_path_count: 3
```

To regenerate the current output locally:

```powershell
py run_evaluation.py
```
