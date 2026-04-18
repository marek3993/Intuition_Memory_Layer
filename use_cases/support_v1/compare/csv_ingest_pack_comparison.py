from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parents[1]

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from calibration import CALIBRATION_NAME, CALIBRATION_VERSION, WINNING_SETTINGS
from calibration import SupportV1CalibrationResult, apply_support_v1_calibration
from evaluate_support_labels import (
    LabelEvaluationResult,
    build_entity_events,
    evaluate_label,
    format_percent,
    project_relative_path,
    validate_label,
)
from normalize_raw_support_export_csv import load_flat_export, normalize_rows
from use_cases.support_v1.compare.common import (
    assert_unique_values,
    load_combined_labels,
    load_support_cases_from_payload,
)
from use_cases.support_v1.eval.label_evaluation import (
    build_aggregate_summary,
    build_baseline_comparison,
    build_calibrated_result,
    format_dataset_path,
    replay_visible_history,
)
from shared.io_utils import atomic_write_json, atomic_write_text


ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
CSV_SAMPLE_A_PATH = SCRIPT_DIR / "raw_support_export_sample.csv"
CSV_SAMPLE_A_LABELS_PATH = SCRIPT_DIR / "raw_support_export_sample_labels.json"
CSV_SAMPLE_B_PATH = SCRIPT_DIR / "raw_support_export_sample_b.csv"
CSV_SAMPLE_B_LABELS_PATH = SCRIPT_DIR / "raw_support_export_sample_b_labels.json"
CSV_SAMPLE_C_PATH = SCRIPT_DIR / "raw_support_export_sample_c.csv"
CSV_SAMPLE_C_LABELS_PATH = SCRIPT_DIR / "raw_support_export_sample_c_labels.json"
EXPORT_PATH = ARTIFACTS_DIR / "support_csv_ingest_pack_comparison.json"
MARKDOWN_EXPORT_PATH = ARTIFACTS_DIR / "support_csv_ingest_pack_comparison.md"


def merge_csv_rows(
    csv_paths: Sequence[Path],
    *,
    slice_name: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    record_ids: list[str] = []

    for csv_path in csv_paths:
        loaded_rows = load_flat_export(csv_path)
        rows.extend(loaded_rows)
        record_ids.extend(str(row["record_id"]).strip() for row in loaded_rows)

    assert_unique_values(
        record_ids,
        label="record_id",
        slice_name=slice_name,
    )
    return rows


def evaluate_slice(
    slice_name: str,
    *,
    csv_paths: Sequence[Path],
    labels_paths: Sequence[Path],
) -> dict[str, Any]:
    rows = merge_csv_rows(csv_paths, slice_name=slice_name)
    normalized_payload = normalize_rows(rows)
    normalized_payload["dataset_name"] = f"support_v1_csv_ingest_{slice_name}"
    cases = load_support_cases_from_payload(normalized_payload)
    labels = load_combined_labels(labels_paths, slice_name=slice_name)
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
            "csv_paths": [format_dataset_path(path) for path in csv_paths],
            "labels_paths": [format_dataset_path(path) for path in labels_paths],
        },
        "normalized_dataset": {
            "dataset_name": str(normalized_payload["dataset_name"]),
            "entity_count": len(normalized_payload["entities"]),
            "case_count": len(cases),
            "row_count": len(rows),
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


def build_summary_rows(slice_results: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "slice": slice_result["slice_name"],
            "labels": slice_result["total_labels"],
            "iml_accuracy": slice_result["accuracies"]["iml"],
            "calibrated_iml_accuracy": slice_result["accuracies"]["calibrated_iml"],
            "naive_summary_accuracy": slice_result["accuracies"]["naive_summary"],
            "full_history_accuracy": slice_result["accuracies"]["full_history"],
        }
        for slice_result in slice_results
    ]


def format_delta(value: float) -> str:
    if value > 0:
        return f"+{format_percent(value)}"
    if value < 0:
        return f"-{format_percent(abs(value))}"
    return format_percent(0.0)


def build_slice_markdown(slice_result: dict[str, Any]) -> list[str]:
    calibrated_comparison = slice_result["baseline_comparison"]["calibrated"]
    return [
        f"## {slice_result['slice_name']}",
        "",
        f"- Label count: {slice_result['total_labels']}",
        f"- CSV row count: {slice_result['normalized_dataset']['row_count']}",
        (
            f"- Accuracy: IML {format_percent(float(slice_result['accuracies']['iml']))}, "
            f"calibrated IML {format_percent(float(slice_result['accuracies']['calibrated_iml']))}, "
            f"naive_summary {format_percent(float(slice_result['accuracies']['naive_summary']))}, "
            f"full_history {format_percent(float(slice_result['accuracies']['full_history']))}."
        ),
        (
            "- Calibration delta vs default IML: "
            f"{format_delta(float(calibrated_comparison['accuracy_delta_vs_original_iml']))}"
        ),
        (
            "- Calibration applied count: "
            f"{slice_result['calibration_applied_count']}"
        ),
        "",
    ]


def build_markdown_report(slice_results: Sequence[dict[str, Any]]) -> str:
    lines = [
        "# Support CSV Ingest Pack Comparison",
        "",
        (
            "Compares `csv_sample_a`, `csv_sample_b`, `csv_sample_c`, and "
            "`combined_abc` by running the existing CSV normalization and "
            "labeled decision-point evaluation flow end to end."
        ),
        "",
        "## Summary",
        "",
    ]

    for slice_result in slice_results:
        lines.append(
            (
                f"- `{slice_result['slice_name']}`: "
                f"{slice_result['total_labels']} labels, "
                f"IML {format_percent(float(slice_result['accuracies']['iml']))}, "
                f"calibrated IML {format_percent(float(slice_result['accuracies']['calibrated_iml']))}, "
                f"naive_summary {format_percent(float(slice_result['accuracies']['naive_summary']))}, "
                f"full_history {format_percent(float(slice_result['accuracies']['full_history']))}."
            )
        )
    lines.append("")

    for slice_result in slice_results:
        lines.extend(build_slice_markdown(slice_result))

    lines.extend(
        [
            "## Overall",
            "",
            (
                "- This comparison adds one explicit CSV-ingest pack check so support_v1 "
                "can be compared on each CSV sample independently and on the in-memory "
                "combined A+B+C slice without mutating source datasets."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def build_export_payload(slice_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_metadata": {
            "evaluation_name": "support_v1_csv_ingest_pack_comparison",
            "generated_at": datetime.now().astimezone().isoformat(),
            "runner_path": project_relative_path(Path(__file__).resolve()),
            "export_path": project_relative_path(EXPORT_PATH),
            "markdown_export_path": project_relative_path(MARKDOWN_EXPORT_PATH),
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


def export_json_results(payload: dict[str, Any]) -> Path:
    return atomic_write_json(EXPORT_PATH, payload)


def export_markdown_report(markdown_report: str) -> Path:
    if not markdown_report.endswith("\n"):
        markdown_report = f"{markdown_report}\n"
    return atomic_write_text(MARKDOWN_EXPORT_PATH, markdown_report)


def print_summary_table(
    slice_results: Sequence[dict[str, Any]],
    *,
    json_artifact_path: Path,
    markdown_artifact_path: Path,
) -> None:
    headers = (
        "slice",
        "labels",
        "iml",
        "calibrated_iml",
        "naive_summary",
        "full_history",
    )
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
    widths = [
        max(len(header), max(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]

    def format_row(values: Sequence[str]) -> str:
        return " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(values)
        )

    print("support_v1 csv-ingest pack comparison")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))
    print(f"json_artifact: {project_relative_path(json_artifact_path)}")
    print(f"markdown_artifact: {project_relative_path(markdown_artifact_path)}")


def main() -> None:
    slice_results = [
        evaluate_slice(
            "csv_sample_a",
            csv_paths=(CSV_SAMPLE_A_PATH,),
            labels_paths=(CSV_SAMPLE_A_LABELS_PATH,),
        ),
        evaluate_slice(
            "csv_sample_b",
            csv_paths=(CSV_SAMPLE_B_PATH,),
            labels_paths=(CSV_SAMPLE_B_LABELS_PATH,),
        ),
        evaluate_slice(
            "csv_sample_c",
            csv_paths=(CSV_SAMPLE_C_PATH,),
            labels_paths=(CSV_SAMPLE_C_LABELS_PATH,),
        ),
        evaluate_slice(
            "combined_abc",
            csv_paths=(CSV_SAMPLE_A_PATH, CSV_SAMPLE_B_PATH, CSV_SAMPLE_C_PATH),
            labels_paths=(
                CSV_SAMPLE_A_LABELS_PATH,
                CSV_SAMPLE_B_LABELS_PATH,
                CSV_SAMPLE_C_LABELS_PATH,
            ),
        ),
    ]
    export_payload = build_export_payload(slice_results)
    markdown_report = build_markdown_report(slice_results)
    json_artifact_path = export_json_results(export_payload)
    markdown_artifact_path = export_markdown_report(markdown_report)
    print_summary_table(
        slice_results,
        json_artifact_path=json_artifact_path,
        markdown_artifact_path=markdown_artifact_path,
    )


if __name__ == "__main__":
    main()
