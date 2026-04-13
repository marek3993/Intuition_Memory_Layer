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
from calibration import SupportV1CalibrationResult, apply_support_v1_calibration
from convert_support_cases_to_events import SupportCase, SupportRecord, parse_timestamp
from evaluate_support_labels import (
    LabelEvaluationResult,
    SupportLabel,
    build_entity_events,
    evaluate_label,
    format_percent,
    load_support_labels,
    project_relative_path,
    validate_label,
)
from normalize_raw_support_export import load_raw_export, normalize_export
from run_support_label_evaluation import (
    build_aggregate_summary,
    build_baseline_comparison,
    build_calibrated_result,
    format_dataset_path,
    replay_visible_history,
)


ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
RAW_SAMPLE_A_PATH = SCRIPT_DIR / "raw_support_export_sample.json"
RAW_SAMPLE_A_LABELS_PATH = SCRIPT_DIR / "raw_support_export_sample_labels.json"
RAW_SAMPLE_B_PATH = SCRIPT_DIR / "raw_support_export_sample_b.json"
RAW_SAMPLE_B_LABELS_PATH = SCRIPT_DIR / "raw_support_export_sample_b_labels.json"
RAW_SAMPLE_C_PATH = SCRIPT_DIR / "raw_support_export_sample_c.json"
RAW_SAMPLE_C_LABELS_PATH = SCRIPT_DIR / "raw_support_export_sample_c_labels.json"
EXPORT_PATH = ARTIFACTS_DIR / "support_raw_ingest_pack_comparison.json"
MARKDOWN_EXPORT_PATH = ARTIFACTS_DIR / "support_raw_ingest_pack_comparison.md"


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


def load_support_cases_from_payload(payload: dict[str, Any]) -> list[SupportCase]:
    raw_entities = payload.get("entities")
    if not isinstance(raw_entities, list):
        raise ValueError("Normalized support payload must contain an 'entities' list.")

    cases: list[SupportCase] = []
    for raw_entity in raw_entities:
        entity_id = str(raw_entity["entity_id"])
        account_name = str(raw_entity["account_name"])
        segment = str(raw_entity["segment"])

        for raw_case in raw_entity.get("cases", []):
            records = tuple(
                SupportRecord(
                    record_id=str(raw_record["record_id"]),
                    timestamp=parse_timestamp(str(raw_record["timestamp"])),
                    source_system=str(raw_record["source_system"]),
                    source_type=str(raw_record["source_type"]),
                    actor_role=str(raw_record["actor_role"]),
                    raw_action=str(raw_record["raw_action"]),
                    outcome=str(raw_record["outcome"]),
                    details=str(raw_record["details"]),
                    metadata=dict(raw_record.get("metadata", {})),
                )
                for raw_record in raw_case.get("records", [])
            )
            cases.append(
                SupportCase(
                    entity_id=entity_id,
                    account_name=account_name,
                    segment=segment,
                    case_id=str(raw_case["case_id"]),
                    opened_at=parse_timestamp(str(raw_case["opened_at"])),
                    closed_at=parse_timestamp(str(raw_case["closed_at"])),
                    channel=str(raw_case["channel"]),
                    priority=str(raw_case["priority"]),
                    summary=str(raw_case["summary"]),
                    records=records,
                )
            )

    return sorted(cases, key=lambda case: (case.entity_id, case.opened_at, case.case_id))


def merge_raw_exports(
    raw_payloads: Sequence[dict[str, Any]],
    *,
    slice_name: str,
) -> dict[str, Any]:
    accounts: list[dict[str, Any]] = []
    tickets: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    for raw_payload in raw_payloads:
        accounts.extend(dict(account) for account in raw_payload.get("accounts", []))
        tickets.extend(dict(ticket) for ticket in raw_payload.get("tickets", []))
        records.extend(dict(record) for record in raw_payload.get("records", []))

    assert_unique_values(
        [str(account["account_ref"]) for account in accounts],
        label="account_ref",
        slice_name=slice_name,
    )
    assert_unique_values(
        [str(account["entity_id"]) for account in accounts],
        label="entity_id",
        slice_name=slice_name,
    )
    assert_unique_values(
        [str(ticket["ticket_ref"]) for ticket in tickets],
        label="ticket_ref",
        slice_name=slice_name,
    )
    assert_unique_values(
        [str(ticket["case_id"]) for ticket in tickets],
        label="case_id",
        slice_name=slice_name,
    )
    assert_unique_values(
        [str(record["event_ref"]) for record in records],
        label="event_ref",
        slice_name=slice_name,
    )

    return {
        "export_name": f"support_raw_ingest_{slice_name}",
        "exported_at": datetime.now().astimezone().isoformat(),
        "accounts": accounts,
        "tickets": tickets,
        "records": records,
    }


def load_combined_labels(
    labels_paths: Sequence[Path],
    *,
    slice_name: str,
) -> list[SupportLabel]:
    labels: list[SupportLabel] = []
    for labels_path in labels_paths:
        labels.extend(load_support_labels(labels_path))

    assert_unique_values(
        [label.label_id for label in labels],
        label="label_id",
        slice_name=slice_name,
    )
    return labels


def evaluate_slice(
    slice_name: str,
    *,
    raw_paths: Sequence[Path],
    labels_paths: Sequence[Path],
) -> dict[str, Any]:
    raw_payload = merge_raw_exports(
        [load_raw_export(raw_path) for raw_path in raw_paths],
        slice_name=slice_name,
    )
    normalized_payload = normalize_export(raw_payload)
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
            "raw_paths": [format_dataset_path(path) for path in raw_paths],
            "labels_paths": [format_dataset_path(path) for path in labels_paths],
        },
        "normalized_dataset": {
            "dataset_name": str(normalized_payload["dataset_name"]),
            "entity_count": len(normalized_payload["entities"]),
            "case_count": len(cases),
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
        "# Support Raw Ingest Pack Comparison",
        "",
        (
            "Compares `raw_sample_a`, `raw_sample_b`, `raw_sample_c`, and "
            "`combined_abc` by running the existing raw normalization and "
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
                "- This comparison shows whether the existing support_v1 raw-ingest path "
                "holds up consistently across each raw sample alone and when all three "
                "samples are evaluated as one combined labeled slice."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def build_export_payload(slice_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_metadata": {
            "evaluation_name": "support_v1_raw_ingest_pack_comparison",
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

    print("support_v1 raw-ingest pack comparison")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))
    print(f"json_artifact: {project_relative_path(json_artifact_path)}")
    print(f"markdown_artifact: {project_relative_path(markdown_artifact_path)}")


def main() -> None:
    slice_results = [
        evaluate_slice(
            "raw_sample_a",
            raw_paths=(RAW_SAMPLE_A_PATH,),
            labels_paths=(RAW_SAMPLE_A_LABELS_PATH,),
        ),
        evaluate_slice(
            "raw_sample_b",
            raw_paths=(RAW_SAMPLE_B_PATH,),
            labels_paths=(RAW_SAMPLE_B_LABELS_PATH,),
        ),
        evaluate_slice(
            "raw_sample_c",
            raw_paths=(RAW_SAMPLE_C_PATH,),
            labels_paths=(RAW_SAMPLE_C_LABELS_PATH,),
        ),
        evaluate_slice(
            "combined_abc",
            raw_paths=(RAW_SAMPLE_A_PATH, RAW_SAMPLE_B_PATH, RAW_SAMPLE_C_PATH),
            labels_paths=(
                RAW_SAMPLE_A_LABELS_PATH,
                RAW_SAMPLE_B_LABELS_PATH,
                RAW_SAMPLE_C_LABELS_PATH,
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
