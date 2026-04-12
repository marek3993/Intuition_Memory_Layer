from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from calibration import CALIBRATION_NAME, CALIBRATION_VERSION, WINNING_SETTINGS
from convert_support_cases_to_events import load_support_cases
from evaluate_support_labels import (
    LABELS_PATH,
    LabelEvaluationResult,
    SupportLabel,
    build_entity_events,
    evaluate_label,
    format_percent,
    load_support_labels,
    project_relative_path,
    validate_label,
)
from run_support_label_evaluation import (
    ARTIFACTS_DIR,
    build_aggregate_summary,
    build_baseline_comparison,
    build_calibrated_result,
    replay_visible_history,
)
from calibration import SupportV1CalibrationResult, apply_support_v1_calibration


PACK_A_CASES_PATH = SCRIPT_DIR / "sample_support_cases.json"
PACK_A_LABELS_PATH = LABELS_PATH
PACK_B_CASES_PATH = SCRIPT_DIR / "sample_support_cases_pack_b.json"
PACK_B_LABELS_PATH = SCRIPT_DIR / "sample_support_labels_pack_b.json"
PACK_C_CASES_PATH = SCRIPT_DIR / "sample_support_cases_pack_c.json"
PACK_C_LABELS_PATH = SCRIPT_DIR / "sample_support_labels_pack_c.json"
EXPORT_PATH = ARTIFACTS_DIR / "support_label_pack_comparison.json"
MARKDOWN_EXPORT_PATH = ARTIFACTS_DIR / "support_label_pack_comparison.md"
DECISION_MEMO_EXPORT_PATH = ARTIFACTS_DIR / "support_label_pack_decision_memo.md"
ROUTE_QUALITY_FIELDS: tuple[str, ...] = (
    "fast_path_precision",
    "fast_path_recall",
    "deep_path_precision",
    "deep_path_recall",
)
METHOD_NAMES: tuple[str, ...] = (
    "iml",
    "calibrated_iml",
    "naive_summary",
    "full_history",
)
ACCURACY_TOLERANCE = 1e-12


def assert_unique_values(
    values: Sequence[str],
    *,
    label: str,
    slice_name: str,
) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []

    for value in values:
        if value in seen:
            duplicates.append(value)
            continue
        seen.add(value)

    if duplicates:
        duplicate_list = ", ".join(sorted(set(duplicates)))
        raise ValueError(
            f"Slice {slice_name} contains duplicate {label} values: {duplicate_list}."
        )


def load_slice_inputs(
    cases_paths: Sequence[Path],
    labels_paths: Sequence[Path],
    *,
    slice_name: str,
) -> tuple[list[Any], list[SupportLabel]]:
    cases: list[Any] = []
    labels: list[SupportLabel] = []

    for path in cases_paths:
        cases.extend(load_support_cases(path))
    for path in labels_paths:
        labels.extend(load_support_labels(path))

    assert_unique_values(
        [case.case_id for case in cases],
        label="case_id",
        slice_name=slice_name,
    )
    assert_unique_values(
        [label.label_id for label in labels],
        label="label_id",
        slice_name=slice_name,
    )

    return cases, labels


def build_route_quality(method_summary: dict[str, Any]) -> dict[str, float | None]:
    return {
        field_name: method_summary[field_name]
        for field_name in ROUTE_QUALITY_FIELDS
    }


def evaluate_slice(
    slice_name: str,
    cases_paths: Sequence[Path],
    labels_paths: Sequence[Path],
) -> dict[str, Any]:
    cases, labels = load_slice_inputs(
        cases_paths=cases_paths,
        labels_paths=labels_paths,
        slice_name=slice_name,
    )
    entity_events, event_mapping_version = build_entity_events(cases)
    cases_by_ticket_id = {case.case_id: case for case in cases}

    original_results: list[LabelEvaluationResult] = []
    calibrated_results: list[LabelEvaluationResult] = []
    calibration_results: list[SupportV1CalibrationResult] = []

    for label in labels:
        validate_label(label, cases_by_ticket_id, entity_events)
        original_result = evaluate_label(label, entity_events)
        visible_events, replayed_profile = replay_visible_history(label, entity_events)
        calibration_result = apply_support_v1_calibration(
            profile=replayed_profile,
            visible_events=visible_events,
            decision_time=label.decision_timestamp,
        )
        calibrated_result = build_calibrated_result(
            original_result=original_result,
            calibrated_profile=calibration_result.profile,
        )

        original_results.append(original_result)
        calibrated_results.append(calibrated_result)
        calibration_results.append(calibration_result)

    default_summary = build_aggregate_summary(
        active_results=original_results,
        original_results=original_results,
        calibration_results=[None] * len(original_results),
        use_calibration=False,
    )
    calibrated_summary = build_aggregate_summary(
        active_results=calibrated_results,
        original_results=original_results,
        calibration_results=calibration_results,
        use_calibration=True,
    )
    default_baseline_comparison = build_baseline_comparison(
        active_results=original_results,
        original_results=original_results,
        use_calibration=False,
    )
    calibrated_baseline_comparison = build_baseline_comparison(
        active_results=calibrated_results,
        original_results=original_results,
        use_calibration=True,
    )

    default_methods = default_summary["methods"]
    calibrated_methods = calibrated_summary["methods"]

    return {
        "slice_name": slice_name,
        "input_files": {
            "cases_paths": [project_relative_path(path) for path in cases_paths],
            "labels_paths": [project_relative_path(path) for path in labels_paths],
        },
        "event_mapping_version": event_mapping_version,
        "total_labels": len(labels),
        "accuracies": {
            "iml": default_methods["iml"]["accuracy"],
            "calibrated_iml": calibrated_methods["calibrated_iml"]["accuracy"],
            "naive_summary": default_methods["naive_summary"]["accuracy"],
            "full_history": default_methods["full_history"]["accuracy"],
        },
        "methods": {
            "iml": default_methods["iml"],
            "calibrated_iml": calibrated_methods["calibrated_iml"],
            "naive_summary": default_methods["naive_summary"],
            "full_history": default_methods["full_history"],
        },
        "route_quality": {
            "iml": build_route_quality(default_methods["iml"]),
            "calibrated_iml": build_route_quality(calibrated_methods["calibrated_iml"]),
            "naive_summary": build_route_quality(default_methods["naive_summary"]),
            "full_history": build_route_quality(default_methods["full_history"]),
        },
        "comparison_diagnostics": {
            "default": default_summary["comparison_diagnostics"],
            "calibrated": calibrated_summary["comparison_diagnostics"],
        },
        "baseline_comparison": {
            "default": default_baseline_comparison,
            "calibrated": calibrated_baseline_comparison,
        },
        "calibration_applied_count": calibrated_summary["calibration_applied_count"],
    }


def build_summary_rows(slices: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "slice": slice_result["slice_name"],
            "labels": slice_result["total_labels"],
            "iml_accuracy": slice_result["accuracies"]["iml"],
            "calibrated_iml_accuracy": slice_result["accuracies"]["calibrated_iml"],
            "naive_summary_accuracy": slice_result["accuracies"]["naive_summary"],
            "full_history_accuracy": slice_result["accuracies"]["full_history"],
        }
        for slice_result in slices
    ]


def format_optional_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return format_percent(value)


def format_delta(value: float) -> str:
    percent_text = format_percent(abs(value))
    if value > 0:
        return f"+{percent_text}"
    if value < 0:
        return f"-{percent_text}"
    return format_percent(0.0)


def accuracies_match(left: float, right: float) -> bool:
    return abs(left - right) <= ACCURACY_TOLERANCE


def get_slice_winners(slice_result: dict[str, Any]) -> list[str]:
    accuracies = slice_result["accuracies"]
    highest_accuracy = max(float(accuracies[method_name]) for method_name in METHOD_NAMES)
    return [
        method_name
        for method_name in METHOD_NAMES
        if accuracies_match(float(accuracies[method_name]), highest_accuracy)
    ]


def format_winner_text(winners: Sequence[str]) -> str:
    if len(winners) == 1:
        return winners[0]
    return f"Tie: {', '.join(winners)}"


def format_method_list(method_names: Sequence[str]) -> str:
    if not method_names:
        return ""
    quoted_names = [f"`{method_name}`" for method_name in method_names]
    if len(quoted_names) == 1:
        return quoted_names[0]
    if len(quoted_names) == 2:
        return f"{quoted_names[0]} and {quoted_names[1]}"
    return f"{', '.join(quoted_names[:-1])}, and {quoted_names[-1]}"


def compare_accuracy(active_accuracy: float, baseline_accuracy: float) -> str:
    if accuracies_match(active_accuracy, baseline_accuracy):
        return "ties"
    if active_accuracy > baseline_accuracy:
        return "beats"
    return "loses to"


def build_win_stats(
    slice_results: Sequence[dict[str, Any]],
) -> tuple[dict[str, int], int]:
    outright_wins = {method_name: 0 for method_name in METHOD_NAMES}
    tied_slices = 0

    for slice_result in slice_results:
        winners = get_slice_winners(slice_result)
        if len(winners) == 1:
            outright_wins[winners[0]] += 1
        else:
            tied_slices += 1

    return outright_wins, tied_slices


def build_route_quality_lines(slice_result: dict[str, Any]) -> list[str]:
    lines = ["Route-quality metrics:"]
    route_quality = slice_result.get("route_quality")

    if not route_quality:
        lines.append("- Not available")
        return lines

    for method_name in METHOD_NAMES:
        summary = route_quality.get(method_name)
        if summary is None:
            continue
        lines.append(
            (
                f"- `{method_name}`: "
                f"fast_path_precision={format_optional_percent(summary['fast_path_precision'])}, "
                f"fast_path_recall={format_optional_percent(summary['fast_path_recall'])}, "
                f"deep_path_precision={format_optional_percent(summary['deep_path_precision'])}, "
                f"deep_path_recall={format_optional_percent(summary['deep_path_recall'])}"
            )
        )

    return lines


def build_diagnostic_lines(slice_result: dict[str, Any]) -> list[str]:
    lines = ["Comparison diagnostics:"]
    comparison_diagnostics = slice_result.get("comparison_diagnostics")

    if not comparison_diagnostics:
        lines.append("- Not available")
        return lines

    for mode_name in ("default", "calibrated"):
        diagnostics = comparison_diagnostics.get(mode_name)
        if diagnostics is None:
            continue
        lines.append(
            (
                f"- `{mode_name}`: "
                f"iml_only_correct_vs_baselines={diagnostics['iml_only_correct_vs_baselines']}, "
                f"baselines_only_correct_vs_iml={diagnostics['baselines_only_correct_vs_iml']}, "
                f"all_methods_correct={diagnostics['all_methods_correct']}, "
                f"all_methods_wrong={diagnostics['all_methods_wrong']}"
            )
        )

    return lines


def build_slice_markdown(slice_result: dict[str, Any]) -> list[str]:
    calibrated_comparison = slice_result["baseline_comparison"]["calibrated"]
    winners = get_slice_winners(slice_result)

    lines = [
        f"## {slice_result['slice_name']}",
        "",
        f"- Label count: {slice_result['total_labels']}",
        f"- IML accuracy: {format_percent(float(slice_result['accuracies']['iml']))}",
        (
            "- Calibrated IML accuracy: "
            f"{format_percent(float(slice_result['accuracies']['calibrated_iml']))}"
        ),
        (
            "- naive_summary accuracy: "
            f"{format_percent(float(slice_result['accuracies']['naive_summary']))}"
        ),
        (
            "- full_history accuracy: "
            f"{format_percent(float(slice_result['accuracies']['full_history']))}"
        ),
        f"- Winner: {format_winner_text(winners)}",
        (
            f"- Accuracy delta vs default IML for calibrated_iml: "
            f"{format_delta(float(calibrated_comparison['accuracy_delta_vs_original_iml']))}"
        ),
        (
            f"- Accuracy delta vs default IML for naive_summary: "
            f"{format_delta(float(slice_result['accuracies']['naive_summary']) - float(slice_result['accuracies']['iml']))}"
        ),
        (
            f"- Accuracy delta vs default IML for full_history: "
            f"{format_delta(float(slice_result['accuracies']['full_history']) - float(slice_result['accuracies']['iml']))}"
        ),
        f"- Calibration applied count: {slice_result['calibration_applied_count']}",
        "",
    ]
    lines.extend(build_route_quality_lines(slice_result))
    lines.append("")
    lines.extend(build_diagnostic_lines(slice_result))
    lines.append("")
    return lines


def build_takeaway(slice_results: Sequence[dict[str, Any]]) -> str:
    outright_wins, _ = build_win_stats(slice_results)
    calibrated_beats_iml_all = all(
        float(slice_result["accuracies"]["calibrated_iml"])
        > float(slice_result["accuracies"]["iml"])
        for slice_result in slice_results
    )
    calibrated_beats_baselines_all = all(
        float(slice_result["accuracies"]["calibrated_iml"])
        > float(slice_result["accuracies"]["naive_summary"])
        and float(slice_result["accuracies"]["calibrated_iml"])
        > float(slice_result["accuracies"]["full_history"])
        for slice_result in slice_results
    )
    calibrated_wins_most = outright_wins["calibrated_iml"] == max(outright_wins.values())

    if calibrated_beats_baselines_all:
        return "Calibrated IML is the clear winner across every slice in this run."
    if calibrated_wins_most and not calibrated_beats_iml_all:
        return "Calibrated IML leads overall, but its gains are concentrated in only part of the slice set."
    if calibrated_wins_most:
        return "Calibrated IML improves on default IML consistently and leads the overall comparison."
    return "No single method dominates every slice; the results stay slice-dependent."


def build_winner_summary_lines(slice_results: Sequence[dict[str, Any]]) -> list[str]:
    lines: list[str] = ["## Current Winner Summary", ""]

    for slice_result in slice_results:
        winners = get_slice_winners(slice_result)
        winning_accuracy = max(
            float(slice_result["accuracies"][method_name]) for method_name in METHOD_NAMES
        )
        if len(winners) == 1:
            lines.append(
                f"- `{slice_result['slice_name']}`: {format_method_list(winners)} wins by accuracy at {format_percent(winning_accuracy)}."
            )
            continue
        lines.append(
            f"- `{slice_result['slice_name']}`: tied at {format_percent(winning_accuracy)} across {format_method_list(winners)}."
        )

    lines.append("")
    return lines


def build_calibration_effect_lines(slice_results: Sequence[dict[str, Any]]) -> list[str]:
    lines: list[str] = ["## Calibration Effect Summary", ""]
    improved_slices = 0
    tied_slices = 0

    for slice_result in slice_results:
        calibrated_accuracy = float(slice_result["accuracies"]["calibrated_iml"])
        default_accuracy = float(slice_result["accuracies"]["iml"])
        delta = calibrated_accuracy - default_accuracy
        relation = compare_accuracy(calibrated_accuracy, default_accuracy)
        if relation == "beats":
            improved_slices += 1
        elif relation == "ties":
            tied_slices += 1
        lines.append(
            (
                f"- `{slice_result['slice_name']}`: calibrated IML {relation} default IML "
                f"by {format_delta(delta)} ({format_percent(calibrated_accuracy)} vs {format_percent(default_accuracy)})."
            )
        )

    overall_label = "consistent" if improved_slices == len(slice_results) else "mixed"
    lines.append(
        (
            f"- Overall: improvement is {overall_label}; calibrated IML beats default IML on "
            f"{improved_slices} of {len(slice_results)} slices and ties on {tied_slices} of {len(slice_results)} slices."
        )
    )
    lines.append("")
    return lines


def build_baseline_position_lines(slice_results: Sequence[dict[str, Any]]) -> list[str]:
    lines: list[str] = ["## Baseline Position Summary", ""]
    beats_both_count = 0

    for slice_result in slice_results:
        calibrated_accuracy = float(slice_result["accuracies"]["calibrated_iml"])
        naive_accuracy = float(slice_result["accuracies"]["naive_summary"])
        full_history_accuracy = float(slice_result["accuracies"]["full_history"])
        beats_naive = calibrated_accuracy > naive_accuracy and not accuracies_match(
            calibrated_accuracy, naive_accuracy
        )
        beats_full_history = calibrated_accuracy > full_history_accuracy and not accuracies_match(
            calibrated_accuracy, full_history_accuracy
        )

        if beats_naive and beats_full_history:
            beats_both_count += 1
            lines.append(
                f"- `{slice_result['slice_name']}`: calibrated IML beats both baselines."
            )
            continue

        lines.append(
            (
                f"- `{slice_result['slice_name']}`: calibrated IML "
                f"{compare_accuracy(calibrated_accuracy, naive_accuracy)} `naive_summary` and "
                f"{compare_accuracy(calibrated_accuracy, full_history_accuracy)} `full_history`."
            )
        )

    lines.append(
        f"- Overall: calibrated IML beats both baselines on {beats_both_count} of {len(slice_results)} slices."
    )
    lines.append("")
    return lines


def build_main_risk_lines(slice_results: Sequence[dict[str, Any]]) -> list[str]:
    lines: list[str] = ["## Main Risks", ""]
    small_sample_slices = [
        f"`{slice_result['slice_name']}` ({slice_result['total_labels']} labels)"
        for slice_result in slice_results
        if slice_result["total_labels"] < 10
    ]
    if small_sample_slices:
        lines.append(
            f"- Small sample size remains a risk on {', '.join(small_sample_slices)}."
        )

    non_outright_wins = [
        f"`{slice_result['slice_name']}`"
        for slice_result in slice_results
        if "calibrated_iml" not in get_slice_winners(slice_result)
        or len(get_slice_winners(slice_result)) > 1
    ]
    if non_outright_wins:
        lines.append(
            (
                "- Calibrated IML is not an outright winner on every slice; "
                f"the comparison stays mixed on {', '.join(non_outright_wins)}."
            )
        )

    baseline_competitive_slices: list[str] = []
    for slice_result in slice_results:
        calibrated_accuracy = float(slice_result["accuracies"]["calibrated_iml"])
        baseline_notes: list[str] = []
        for baseline_name in ("naive_summary", "full_history"):
            baseline_accuracy = float(slice_result["accuracies"][baseline_name])
            relation = compare_accuracy(calibrated_accuracy, baseline_accuracy)
            if relation != "beats":
                baseline_notes.append(f"{relation} `{baseline_name}`")
        if baseline_notes:
            baseline_competitive_slices.append(
                f"`{slice_result['slice_name']}` ({'; '.join(baseline_notes)})"
            )
    if baseline_competitive_slices:
        lines.append(
            (
                "- Baselines remain competitive on "
                f"{', '.join(baseline_competitive_slices)}."
            )
        )

    if len(lines) == 2:
        lines.append("- No additional material risk signal appears in the current slice comparison.")

    lines.append("")
    return lines


def choose_recommended_next_step(slice_results: Sequence[dict[str, Any]]) -> tuple[str, str]:
    small_sample_count = sum(1 for slice_result in slice_results if slice_result["total_labels"] < 10)
    calibrated_losses_to_baseline = 0
    calibrated_ties_to_baseline = 0
    calibrated_losses_to_default = 0
    combined_abc_result = next(
        (
            slice_result
            for slice_result in slice_results
            if slice_result["slice_name"] == "combined_abc"
        ),
        None,
    )

    for slice_result in slice_results:
        calibrated_accuracy = float(slice_result["accuracies"]["calibrated_iml"])
        default_accuracy = float(slice_result["accuracies"]["iml"])
        if calibrated_accuracy < default_accuracy and not accuracies_match(
            calibrated_accuracy, default_accuracy
        ):
            calibrated_losses_to_default += 1

        for baseline_name in ("naive_summary", "full_history"):
            baseline_accuracy = float(slice_result["accuracies"][baseline_name])
            relation = compare_accuracy(calibrated_accuracy, baseline_accuracy)
            if relation == "loses to":
                calibrated_losses_to_baseline += 1
            elif relation == "ties":
                calibrated_ties_to_baseline += 1

    if combined_abc_result is not None:
        combined_default_accuracy = float(combined_abc_result["accuracies"]["iml"])
        combined_calibrated_accuracy = float(combined_abc_result["accuracies"]["calibrated_iml"])
        combined_naive_accuracy = float(combined_abc_result["accuracies"]["naive_summary"])
        combined_full_history_accuracy = float(combined_abc_result["accuracies"]["full_history"])
        combined_baseline_best = max(combined_naive_accuracy, combined_full_history_accuracy)
        if (
            combined_calibrated_accuracy < combined_baseline_best
            and not accuracies_match(combined_calibrated_accuracy, combined_baseline_best)
            and combined_default_accuracy < combined_baseline_best
            and not accuracies_match(combined_default_accuracy, combined_baseline_best)
        ):
            return (
                "revisit event mapping",
                "Both default and calibrated IML trail the baseline ceiling on the largest combined slice, which points to a mapping problem rather than a calibration-only issue.",
            )
    if calibrated_losses_to_default or calibrated_losses_to_baseline >= 2:
        return (
            "refine calibration",
            "Current results still show calibration losses or repeated baseline deficits, so the calibration policy needs another pass before wider rollout.",
        )
    if small_sample_count or calibrated_ties_to_baseline:
        return (
            "hold current calibration and validate on larger slice",
            "Calibrated IML leads the combined slices and does not post a clear loss, but small-slice ties mean the recommendation still needs confirmation on more labels.",
        )
    return (
        "expand labeled data",
        "Calibrated IML is already ahead in the current comparison, so the next constraint is coverage rather than another immediate tuning loop.",
    )


def build_decision_memo(slice_results: Sequence[dict[str, Any]]) -> str:
    recommended_next_step, recommendation_reason = choose_recommended_next_step(slice_results)
    lines = [
        "# Support V1 Pack Comparison Decision Memo",
        "",
    ]
    lines.extend(build_winner_summary_lines(slice_results))
    lines.extend(build_calibration_effect_lines(slice_results))
    lines.extend(build_baseline_position_lines(slice_results))
    lines.extend(build_main_risk_lines(slice_results))
    lines.extend(
        [
            "## Recommended Next Step",
            "",
            f"- {recommended_next_step}",
            f"- Rationale: {recommendation_reason}",
            "",
        ]
    )
    return "\n".join(lines)


def build_markdown_report(slice_results: Sequence[dict[str, Any]]) -> str:
    outright_wins, tied_slices = build_win_stats(slice_results)
    max_wins = max(outright_wins.values())
    overall_winners = [
        method_name
        for method_name, win_count in outright_wins.items()
        if win_count == max_wins
    ]
    calibrated_beats_iml_all = all(
        float(slice_result["accuracies"]["calibrated_iml"])
        > float(slice_result["accuracies"]["iml"])
        for slice_result in slice_results
    )
    calibrated_beats_baselines_all = all(
        float(slice_result["accuracies"]["calibrated_iml"])
        > float(slice_result["accuracies"]["naive_summary"])
        and float(slice_result["accuracies"]["calibrated_iml"])
        > float(slice_result["accuracies"]["full_history"])
        for slice_result in slice_results
    )

    lines = [
        "# Support Label Pack Comparison Summary",
        "",
        "Compact human-readable comparison for `pack_a`, `pack_b`, `pack_c`, `combined_ab`, and `combined_abc`.",
        "",
    ]
    for slice_result in slice_results:
        lines.extend(build_slice_markdown(slice_result))

    lines.extend(
        [
            "## Overall Takeaway",
            "",
            (
                "- Method winning most slices: "
                f"{format_winner_text(overall_winners)} "
                f"({max_wins} outright wins, {tied_slices} tied "
                f"{'slice' if tied_slices == 1 else 'slices'})"
            ),
            (
                "- Calibrated IML beats default IML on all slices: "
                f"{'yes' if calibrated_beats_iml_all else 'no'}"
            ),
            (
                "- Calibrated IML beats both baselines on all slices: "
                f"{'yes' if calibrated_beats_baselines_all else 'no'}"
            ),
            f"- Takeaway: {build_takeaway(slice_results)}",
            "",
        ]
    )
    return "\n".join(lines)


def build_export_payload(slice_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_metadata": {
            "evaluation_name": "support_v1_label_pack_comparison",
            "generated_at": datetime.now().astimezone().isoformat(),
            "runner_path": project_relative_path(Path(__file__).resolve()),
            "export_path": project_relative_path(EXPORT_PATH),
            "markdown_export_path": project_relative_path(MARKDOWN_EXPORT_PATH),
            "decision_memo_export_path": project_relative_path(DECISION_MEMO_EXPORT_PATH),
            "slice_names": [slice_result["slice_name"] for slice_result in slice_results],
            "calibration": {
                "name": CALIBRATION_NAME,
                "version": CALIBRATION_VERSION,
                "settings": asdict(WINNING_SETTINGS),
            },
        },
        "slices": {
            slice_result["slice_name"]: {
                key: value
                for key, value in slice_result.items()
                if key != "slice_name"
            }
            for slice_result in slice_results
        },
        "summary_rows": build_summary_rows(slice_results),
    }


def export_results(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_export_path = EXPORT_PATH.with_name(f"{EXPORT_PATH.stem}.{uuid4().hex}.tmp")
    with temp_export_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_export_path.replace(EXPORT_PATH)
    return EXPORT_PATH


def export_markdown_report(markdown_report: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_export_path = MARKDOWN_EXPORT_PATH.with_name(
        f"{MARKDOWN_EXPORT_PATH.stem}.{uuid4().hex}.tmp"
    )
    with temp_export_path.open("w", encoding="utf-8") as handle:
        handle.write(markdown_report)
        if not markdown_report.endswith("\n"):
            handle.write("\n")
    temp_export_path.replace(MARKDOWN_EXPORT_PATH)
    return MARKDOWN_EXPORT_PATH


def export_decision_memo(decision_memo: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_export_path = DECISION_MEMO_EXPORT_PATH.with_name(
        f"{DECISION_MEMO_EXPORT_PATH.stem}.{uuid4().hex}.tmp"
    )
    with temp_export_path.open("w", encoding="utf-8") as handle:
        handle.write(decision_memo)
        if not decision_memo.endswith("\n"):
            handle.write("\n")
    temp_export_path.replace(DECISION_MEMO_EXPORT_PATH)
    return DECISION_MEMO_EXPORT_PATH


def print_summary_table(
    slice_results: Sequence[dict[str, Any]],
    *,
    json_artifact_path: Path,
    markdown_artifact_path: Path,
    decision_memo_artifact_path: Path,
) -> None:
    rows = [
        (
            slice_result["slice_name"],
            str(slice_result["total_labels"]),
            format_percent(float(slice_result["accuracies"]["iml"])),
            format_percent(float(slice_result["accuracies"]["calibrated_iml"])),
            format_percent(float(slice_result["accuracies"]["naive_summary"])),
            format_percent(float(slice_result["accuracies"]["full_history"])),
        )
        for slice_result in slice_results
    ]
    headers = (
        "slice",
        "labels",
        "iml",
        "calibrated_iml",
        "naive_summary",
        "full_history",
    )
    widths = [
        max(len(header), max(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]

    def format_row(values: Sequence[str]) -> str:
        return " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(values)
        )

    print("support_v1 label pack comparison")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))
    print(f"json_artifact: {project_relative_path(json_artifact_path)}")
    print(f"markdown_artifact: {project_relative_path(markdown_artifact_path)}")
    print(f"decision_memo_artifact: {project_relative_path(decision_memo_artifact_path)}")


def main() -> None:
    slice_results = [
        evaluate_slice(
            "pack_a",
            cases_paths=(PACK_A_CASES_PATH,),
            labels_paths=(PACK_A_LABELS_PATH,),
        ),
        evaluate_slice(
            "pack_b",
            cases_paths=(PACK_B_CASES_PATH,),
            labels_paths=(PACK_B_LABELS_PATH,),
        ),
        evaluate_slice(
            "pack_c",
            cases_paths=(PACK_C_CASES_PATH,),
            labels_paths=(PACK_C_LABELS_PATH,),
        ),
        evaluate_slice(
            "combined_ab",
            cases_paths=(PACK_A_CASES_PATH, PACK_B_CASES_PATH),
            labels_paths=(PACK_A_LABELS_PATH, PACK_B_LABELS_PATH),
        ),
        evaluate_slice(
            "combined_abc",
            cases_paths=(PACK_A_CASES_PATH, PACK_B_CASES_PATH, PACK_C_CASES_PATH),
            labels_paths=(PACK_A_LABELS_PATH, PACK_B_LABELS_PATH, PACK_C_LABELS_PATH),
        ),
    ]
    export_payload = build_export_payload(slice_results)
    markdown_report = build_markdown_report(slice_results)
    decision_memo = build_decision_memo(slice_results)
    json_artifact_path = export_results(export_payload)
    markdown_artifact_path = export_markdown_report(markdown_report)
    decision_memo_artifact_path = export_decision_memo(decision_memo)
    print_summary_table(
        slice_results,
        json_artifact_path=json_artifact_path,
        markdown_artifact_path=markdown_artifact_path,
        decision_memo_artifact_path=decision_memo_artifact_path,
    )


if __name__ == "__main__":
    main()
