from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from calibration import SupportV1CalibrationResult, apply_support_v1_calibration
from convert_support_cases_to_events import load_support_cases
from evaluate_support_labels import LabelEvaluationResult, build_entity_events, evaluate_label
from helpdesk_adapter_zendesk_like import (
    OUTPUT_PATH as DEFAULT_NORMALIZED_OUTPUT_PATH,
    SOURCE_EXPORT_PATH as DEFAULT_EXPORT_PATH,
    load_export,
    normalize_export,
    write_normalized_cases,
)
from run_support_label_evaluation import (
    build_calibrated_result,
    build_export_payload,
    build_label_payload,
    build_review_row,
    export_review_results,
    format_dataset_path,
    replay_visible_history,
    resolve_input_path,
)
from run_support_raw_ingest_label_evaluation import (
    export_json_results,
    load_and_validate_label_set,
    resolve_output_path,
    summarize_correctness,
)


ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
DEFAULT_LABELS_PATH = SCRIPT_DIR / "zendesk_like_export_sample_labels.json"
ZENDESK_LIKE_EVALUATION_PATH = (
    ARTIFACTS_DIR / "latest_support_zendesk_like_label_evaluation.json"
)
ZENDESK_LIKE_REVIEW_PATH = (
    ARTIFACTS_DIR / "latest_support_zendesk_like_label_review.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize a Zendesk-like support export into the support_v1 case schema "
            "and then run the existing labeled decision-point evaluation flow on the "
            "normalized output."
        )
    )
    parser.add_argument(
        "--export-path",
        type=Path,
        help="Override the Zendesk-like support export path.",
    )
    parser.add_argument(
        "--labels-path",
        type=Path,
        help=(
            "Override the support label dataset path. Defaults to the native label "
            "set for the Zendesk-like export sample."
        ),
    )
    parser.add_argument(
        "--normalized-output-path",
        type=Path,
        help="Override the normalized support case output path.",
    )
    parser.add_argument(
        "--evaluation-output-path",
        type=Path,
        help="Override the labeled evaluation JSON artifact path.",
    )
    parser.add_argument(
        "--review-output-path",
        type=Path,
        help="Override the labeled evaluation CSV review artifact path.",
    )
    parser.add_argument(
        "--calibrated",
        action="store_true",
        help="Apply support_v1 calibration before routing each labeled decision point.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_path = resolve_input_path(args.export_path, DEFAULT_EXPORT_PATH)
    labels_path = resolve_input_path(args.labels_path, DEFAULT_LABELS_PATH)
    normalized_output_path = resolve_output_path(
        args.normalized_output_path,
        DEFAULT_NORMALIZED_OUTPUT_PATH,
    )
    evaluation_output_path = resolve_output_path(
        args.evaluation_output_path,
        ZENDESK_LIKE_EVALUATION_PATH,
    )
    review_output_path = resolve_output_path(
        args.review_output_path,
        ZENDESK_LIKE_REVIEW_PATH,
    )

    raw_payload = load_export(export_path)
    normalized_payload = normalize_export(raw_payload)
    write_normalized_cases(normalized_payload, normalized_output_path)

    cases = load_support_cases(normalized_output_path)
    entity_events, event_mapping_version = build_entity_events(cases)
    cases_by_ticket_id = {case.case_id: case for case in cases}

    labels = load_and_validate_label_set(
        labels_path,
        cases_by_ticket_id,
        entity_events,
    )

    active_results: list[LabelEvaluationResult] = []
    original_results: list[LabelEvaluationResult] = []
    calibration_results: list[SupportV1CalibrationResult | None] = []
    per_label_results: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []

    for label in labels:
        original_result = evaluate_label(label, entity_events)
        calibration_result: SupportV1CalibrationResult | None = None
        active_result = original_result

        if args.calibrated:
            visible_events, replayed_profile = replay_visible_history(label, entity_events)
            calibration_result = apply_support_v1_calibration(
                profile=replayed_profile,
                visible_events=visible_events,
                decision_time=label.decision_timestamp,
            )
            active_result = build_calibrated_result(
                original_result=original_result,
                calibrated_profile=calibration_result.profile,
            )

        original_results.append(original_result)
        active_results.append(active_result)
        calibration_results.append(calibration_result)
        per_label_results.append(
            build_label_payload(
                active_result=active_result,
                original_result=original_result,
                calibration_result=calibration_result,
                use_calibration=args.calibrated,
            )
        )
        review_rows.append(
            build_review_row(
                active_result=active_result,
                original_result=original_result,
                calibration_result=calibration_result,
                use_calibration=args.calibrated,
            )
        )

    export_payload = build_export_payload(
        active_results=active_results,
        original_results=original_results,
        calibration_results=calibration_results,
        per_label_results=per_label_results,
        event_mapping_version=event_mapping_version,
        use_calibration=args.calibrated,
        cases_path=normalized_output_path,
        labels_path=labels_path,
    )
    export_payload["run_metadata"]["evaluation_name"] = (
        "support_v1_zendesk_like_label_evaluation"
    )
    export_payload["run_metadata"]["source_export_path"] = format_dataset_path(export_path)
    export_payload["run_metadata"]["normalized_output_path"] = format_dataset_path(
        normalized_output_path
    )
    export_payload["run_metadata"]["runner_path"] = format_dataset_path(Path(__file__))
    export_payload["run_metadata"]["export_path"] = format_dataset_path(
        evaluation_output_path
    )

    json_export_path = export_json_results(evaluation_output_path, export_payload)
    review_export_path = export_review_results(review_output_path, review_rows)

    print("support_v1 zendesk-like label evaluation")
    print(f"mode: {'calibrated' if args.calibrated else 'default'}")
    print(summarize_correctness(active_results))
    print(f"review output path: {format_dataset_path(review_export_path)}")
    print(f"source export path: {format_dataset_path(export_path)}")
    print(f"labels path: {format_dataset_path(labels_path)}")
    print(f"normalized output path: {format_dataset_path(normalized_output_path)}")
    print(f"evaluation output path: {format_dataset_path(json_export_path)}")


if __name__ == "__main__":
    main()
