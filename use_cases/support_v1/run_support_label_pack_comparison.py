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
EXPORT_PATH = ARTIFACTS_DIR / "support_label_pack_comparison.json"
ROUTE_QUALITY_FIELDS: tuple[str, ...] = (
    "fast_path_precision",
    "fast_path_recall",
    "deep_path_precision",
    "deep_path_recall",
)


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


def build_export_payload(slice_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_metadata": {
            "evaluation_name": "support_v1_label_pack_comparison",
            "generated_at": datetime.now().astimezone().isoformat(),
            "runner_path": project_relative_path(Path(__file__).resolve()),
            "export_path": project_relative_path(EXPORT_PATH),
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


def print_summary_table(slice_results: Sequence[dict[str, Any]]) -> None:
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
    print(f"json_artifact: {project_relative_path(EXPORT_PATH)}")


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
            "combined",
            cases_paths=(PACK_A_CASES_PATH, PACK_B_CASES_PATH),
            labels_paths=(PACK_A_LABELS_PATH, PACK_B_LABELS_PATH),
        ),
    ]
    export_payload = build_export_payload(slice_results)
    export_results(export_payload)
    print_summary_table(slice_results)


if __name__ == "__main__":
    main()
