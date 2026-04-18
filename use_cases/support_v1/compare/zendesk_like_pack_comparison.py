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
from helpdesk_adapter_zendesk_like import load_export, normalize_export
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
ZENDESK_SAMPLE_A_PATH = SCRIPT_DIR / "zendesk_like_export_sample.json"
ZENDESK_SAMPLE_A_LABELS_PATH = SCRIPT_DIR / "zendesk_like_export_sample_labels.json"
ZENDESK_SAMPLE_B_PATH = SCRIPT_DIR / "zendesk_like_export_sample_b.json"
ZENDESK_SAMPLE_B_LABELS_PATH = SCRIPT_DIR / "zendesk_like_export_sample_b_labels.json"
ZENDESK_SAMPLE_C_PATH = SCRIPT_DIR / "zendesk_like_export_sample_c.json"
ZENDESK_SAMPLE_C_LABELS_PATH = SCRIPT_DIR / "zendesk_like_export_sample_c_labels.json"
EXPORT_PATH = ARTIFACTS_DIR / "support_zendesk_like_pack_comparison.json"
MARKDOWN_EXPORT_PATH = ARTIFACTS_DIR / "support_zendesk_like_pack_comparison.md"


def load_normalized_cases(
    export_paths: Sequence[Path],
    *,
    slice_name: str,
) -> tuple[list[SupportCase], dict[str, int]]:
    cases: list[SupportCase] = []

    for export_path in export_paths:
        raw_payload = load_export(export_path)
        normalized_payload = normalize_export(raw_payload)
        cases.extend(load_support_cases_from_payload(normalized_payload))

    assert_unique_values(
        [case.case_id for case in cases],
        label="case_id",
        slice_name=slice_name,
    )

    return cases, {
        "source_export_count": len(export_paths),
        "entity_count": len({case.entity_id for case in cases}),
        "case_count": len(cases),
    }


def evaluate_slice(
    slice_name: str,
    *,
    export_paths: Sequence[Path],
    labels_paths: Sequence[Path],
) -> dict[str, Any]:
    cases, normalized_dataset = load_normalized_cases(
        export_paths,
        slice_name=slice_name,
    )
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
            "export_paths": [format_dataset_path(path) for path in export_paths],
            "labels_paths": [format_dataset_path(path) for path in labels_paths],
        },
        "normalized_dataset": normalized_dataset,
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
            "label_count": slice_result["total_labels"],
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
        f"- Source exports: {slice_result['normalized_dataset']['source_export_count']}",
        f"- Normalized entity count: {slice_result['normalized_dataset']['entity_count']}",
        f"- Normalized case count: {slice_result['normalized_dataset']['case_count']}",
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
        f"- Calibration applied count: {slice_result['calibration_applied_count']}",
        "",
    ]


def build_markdown_report(slice_results: Sequence[dict[str, Any]]) -> str:
    lines = [
        "# Support Zendesk-Like Pack Comparison",
        "",
        (
            "Compares `zendesk_sample_a`, `zendesk_sample_b`, `zendesk_sample_c`, "
            "and `combined_abc` by "
            "running the existing Zendesk-like adapter plus labeled decision-point "
            "evaluation flow on each slice."
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
                "- This comparison adds one explicit Zendesk-like pack runner so the "
                "adapter-backed labeled evaluation path can be checked on sample A, "
                "sample B, sample C, and an in-memory combined A+B+C slice without "
                "mutating the source exports."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def build_export_payload(slice_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_metadata": {
            "evaluation_name": "support_v1_zendesk_like_pack_comparison",
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
        "label_count",
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

    print("support_v1 zendesk-like pack comparison")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))
    print(f"json_artifact: {project_relative_path(json_artifact_path)}")
    print(f"markdown_artifact: {project_relative_path(markdown_artifact_path)}")


def main() -> None:
    slice_results = [
        evaluate_slice(
            "zendesk_sample_a",
            export_paths=(ZENDESK_SAMPLE_A_PATH,),
            labels_paths=(ZENDESK_SAMPLE_A_LABELS_PATH,),
        ),
        evaluate_slice(
            "zendesk_sample_b",
            export_paths=(ZENDESK_SAMPLE_B_PATH,),
            labels_paths=(ZENDESK_SAMPLE_B_LABELS_PATH,),
        ),
        evaluate_slice(
            "zendesk_sample_c",
            export_paths=(ZENDESK_SAMPLE_C_PATH,),
            labels_paths=(ZENDESK_SAMPLE_C_LABELS_PATH,),
        ),
        evaluate_slice(
            "combined_abc",
            export_paths=(
                ZENDESK_SAMPLE_A_PATH,
                ZENDESK_SAMPLE_B_PATH,
                ZENDESK_SAMPLE_C_PATH,
            ),
            labels_paths=(
                ZENDESK_SAMPLE_A_LABELS_PATH,
                ZENDESK_SAMPLE_B_LABELS_PATH,
                ZENDESK_SAMPLE_C_LABELS_PATH,
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
