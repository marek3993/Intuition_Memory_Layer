from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from calibration import (
    CALIBRATION_NAME,
    CALIBRATION_VERSION,
    WINNING_SETTINGS,
    SupportV1CalibrationAssessment,
    SupportV1CalibrationResult,
    apply_support_v1_calibration,
)
from convert_support_cases_to_events import SOURCE_PATH, load_support_cases
from evaluate_support_labels import (
    ARTIFACTS_DIR,
    DECAY_GAP_DAYS,
    EVALUATION_STAKES,
    FLAG_FIELDS,
    LABELS_PATH,
    LabelEvaluationResult,
    SupportLabel,
    build_entity_events,
    build_flag_breakdown,
    build_result_payload,
    evaluate_label,
    format_percent,
    load_support_labels,
    make_profile,
    maybe_apply_gap_decay,
    project_relative_path,
    validate_label,
)
from iml.decay import apply_decay
from iml.decision import DecisionContext, route_decision
from iml.models import Event, IntuitionProfile
from iml.revalidate import revalidate_profile
from iml.update_engine import apply_event


EXPORT_PATH = ARTIFACTS_DIR / "latest_support_label_evaluation.json"
REVIEW_EXPORT_PATH = ARTIFACTS_DIR / "latest_support_label_review.csv"
ERRORS_EXPORT_PATH = ARTIFACTS_DIR / "latest_support_label_errors.csv"
ROUTE_CHANGES_EXPORT_PATH = (
    ARTIFACTS_DIR / "latest_support_label_route_changes.csv"
)
REVIEW_FIELDNAMES: tuple[str, ...] = (
    "label_id",
    "entity_id",
    "ticket_id",
    "decision_timestamp",
    "should_route",
    "active_method_name",
    "active_predicted_path",
    "active_correct",
    "original_iml_predicted_path",
    "original_iml_correct",
    "naive_summary_predicted_path",
    "naive_summary_correct",
    "full_history_predicted_path",
    "full_history_correct",
    "contradiction_present",
    "profile_too_stale",
    "wrong_first_impression",
    "visible_event_count",
    "overall_confidence",
    "unknownness",
    "freshness",
    "contradiction_load",
    "calibration_applied",
    "confidence_adjustment",
    "unknownness_reduction",
)
ROUTE_PATHS: tuple[str, ...] = ("fast_path", "deep_path")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the support_v1 labeled decision-point evaluation, with optional "
            "support_v1 calibration applied before the routing decision."
        )
    )
    parser.add_argument(
        "--calibrated",
        action="store_true",
        help="Apply support_v1 calibration before routing each labeled decision point.",
    )
    parser.add_argument(
        "--cases-path",
        type=Path,
        help=(
            "Override the support cases dataset path. Defaults to the current "
            "support_v1 sample pack."
        ),
    )
    parser.add_argument(
        "--labels-path",
        type=Path,
        help=(
            "Override the support label dataset path. Defaults to the current "
            "support_v1 label pack."
        ),
    )
    return parser.parse_args()


def resolve_input_path(path: Path | None, default_path: Path) -> Path:
    candidate = default_path if path is None else path
    return candidate.expanduser().resolve()


def format_dataset_path(path: Path) -> str:
    try:
        return project_relative_path(path)
    except ValueError:
        return str(path)


def replay_visible_history(
    label: SupportLabel,
    entity_events: dict[str, list[Event]],
) -> tuple[tuple[Event, ...], IntuitionProfile]:
    visible_events = tuple(
        event
        for event in entity_events[label.entity_id]
        if event.timestamp <= label.decision_timestamp
    )
    profile_start_time = visible_events[0].timestamp if visible_events else label.decision_timestamp
    profile = make_profile(label.entity_id, profile_start_time)

    for event in visible_events:
        maybe_apply_gap_decay(profile, event.timestamp)
        apply_event(profile, event)

    apply_decay(profile, now=label.decision_timestamp)
    revalidate_profile(profile, now=label.decision_timestamp)
    return visible_events, profile


def build_calibrated_result(
    original_result: LabelEvaluationResult,
    calibrated_profile: IntuitionProfile,
) -> LabelEvaluationResult:
    calibrated_decision = route_decision(
        calibrated_profile,
        DecisionContext(stakes=EVALUATION_STAKES),
    )
    return replace(
        original_result,
        predicted_path=calibrated_decision.selected_path,
        predicted_reason=calibrated_decision.reason,
        correct=calibrated_decision.selected_path == original_result.label.should_route,
        trust=calibrated_profile.attributes["trust"].value,
        cooperativeness=calibrated_profile.attributes["cooperativeness"].value,
        predictability=calibrated_profile.attributes["predictability"].value,
        stability=calibrated_profile.attributes["stability"].value,
        risk=calibrated_profile.attributes["risk"].value,
        overall_confidence=calibrated_profile.overall_confidence,
        unknownness=calibrated_profile.unknownness,
        freshness=calibrated_profile.freshness,
        contradiction_load=calibrated_profile.contradiction_load,
    )


def summarize_correctness(correct_values: Sequence[bool]) -> dict[str, Any]:
    total = len(correct_values)
    correct_predictions = sum(1 for value in correct_values if value)
    incorrect_predictions = total - correct_predictions
    return {
        "correct_predictions": correct_predictions,
        "incorrect_predictions": incorrect_predictions,
        "accuracy": (correct_predictions / total) if total else 0.0,
    }


def safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def summarize_route_quality(
    labeled_paths: Sequence[str],
    predicted_paths: Sequence[str],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}

    for route_path in ROUTE_PATHS:
        correct_predictions = sum(
            1
            for labeled_path, predicted_path in zip(labeled_paths, predicted_paths)
            if labeled_path == route_path and predicted_path == route_path
        )
        predicted_count = sum(
            1 for predicted_path in predicted_paths if predicted_path == route_path
        )
        labeled_count = sum(1 for labeled_path in labeled_paths if labeled_path == route_path)
        metrics[f"{route_path}_precision"] = safe_ratio(
            correct_predictions,
            predicted_count,
        )
        metrics[f"{route_path}_recall"] = safe_ratio(
            correct_predictions,
            labeled_count,
        )

    return metrics


def summarize_method_predictions(
    labeled_paths: Sequence[str],
    predicted_paths: Sequence[str],
) -> dict[str, Any]:
    correctness_summary = summarize_correctness(
        [
            predicted_path == labeled_path
            for labeled_path, predicted_path in zip(labeled_paths, predicted_paths)
        ]
    )
    correctness_summary.update(
        summarize_route_quality(
            labeled_paths=labeled_paths,
            predicted_paths=predicted_paths,
        )
    )
    return correctness_summary


def build_method_summaries(
    active_results: list[LabelEvaluationResult],
    original_results: list[LabelEvaluationResult],
    use_calibration: bool,
) -> dict[str, Any]:
    active_method_name = "calibrated_iml" if use_calibration else "iml"
    labeled_paths = [result.label.should_route for result in active_results]
    method_summaries = {
        active_method_name: summarize_method_predictions(
            labeled_paths=labeled_paths,
            predicted_paths=[result.predicted_path for result in active_results],
        ),
        "naive_summary": summarize_method_predictions(
            labeled_paths=labeled_paths,
            predicted_paths=[
                result.naive_summary_predicted_path for result in active_results
            ],
        ),
        "full_history": summarize_method_predictions(
            labeled_paths=labeled_paths,
            predicted_paths=[
                result.full_history_predicted_path for result in active_results
            ],
        ),
    }

    if use_calibration:
        method_summaries["original_iml"] = summarize_method_predictions(
            labeled_paths=labeled_paths,
            predicted_paths=[result.predicted_path for result in original_results],
        )

    return method_summaries


def build_assessment_payload(
    assessment: SupportV1CalibrationAssessment | None,
) -> dict[str, Any] | None:
    if assessment is None:
        return None

    return {
        "eligible": assessment.eligible,
        "condition_checks": assessment.condition_checks,
        "recent_positive_events": assessment.recent_positive_events,
        "recent_cooperative_events": assessment.recent_cooperative_events,
        "recent_fulfilled_events": assessment.recent_fulfilled_events,
        "recent_negative_events": assessment.recent_negative_events,
        "recent_inactivity_events": assessment.recent_inactivity_events,
        "total_contradiction_events": assessment.total_contradiction_events,
        "total_long_inactivity_events": assessment.total_long_inactivity_events,
        "recent_positive_weight": assessment.recent_positive_weight,
        "last_event_age_hours": assessment.last_event_age_hours,
    }


def build_label_payload(
    active_result: LabelEvaluationResult,
    original_result: LabelEvaluationResult,
    calibration_result: SupportV1CalibrationResult | None,
    use_calibration: bool,
) -> dict[str, Any]:
    payload = build_result_payload(active_result)
    prediction_payload = dict(payload["prediction"])

    payload["prediction"] = {
        "active_method_name": "calibrated_iml" if use_calibration else "iml",
        "predicted_path": prediction_payload["predicted_path"],
        "predicted_reason": prediction_payload["predicted_reason"],
        "correct": prediction_payload["correct"],
    }
    payload["baseline_comparison"] = {
        "naive_summary": {
            "predicted_path": prediction_payload["naive_summary_predicted_path"],
            "decision_reason": prediction_payload["naive_summary_decision_reason"],
            "correct": prediction_payload["naive_summary_correct"],
        },
        "full_history": {
            "predicted_path": prediction_payload["full_history_predicted_path"],
            "decision_reason": prediction_payload["full_history_decision_reason"],
            "correct": prediction_payload["full_history_correct"],
        },
    }
    payload["original_iml_prediction"] = {
        "predicted_path": original_result.predicted_path,
        "predicted_reason": original_result.predicted_reason,
        "correct": original_result.correct,
        "overall_confidence": original_result.overall_confidence,
        "unknownness": original_result.unknownness,
    }
    payload["calibration"] = {
        "enabled_for_run": use_calibration,
        "name": CALIBRATION_NAME,
        "version": CALIBRATION_VERSION,
        "applied": calibration_result.applied if calibration_result else False,
        "route_changed": active_result.predicted_path != original_result.predicted_path,
        "confidence_adjustment": (
            calibration_result.confidence_adjustment if calibration_result else 0.0
        ),
        "unknownness_reduction": (
            calibration_result.unknownness_reduction if calibration_result else 0.0
        ),
        "assessment": build_assessment_payload(
            calibration_result.assessment if calibration_result else None
        ),
    }
    return payload


def build_aggregate_summary(
    active_results: list[LabelEvaluationResult],
    original_results: list[LabelEvaluationResult],
    calibration_results: list[SupportV1CalibrationResult | None],
    use_calibration: bool,
) -> dict[str, Any]:
    active_method_name = "calibrated_iml" if use_calibration else "iml"
    method_summaries = build_method_summaries(
        active_results=active_results,
        original_results=original_results,
        use_calibration=use_calibration,
    )
    active_summary = method_summaries[active_method_name]
    return {
        "total_labels": len(active_results),
        "active_method_name": active_method_name,
        "calibration_enabled": use_calibration,
        "correct_predictions": active_summary["correct_predictions"],
        "incorrect_predictions": active_summary["incorrect_predictions"],
        "accuracy": active_summary["accuracy"],
        "methods": method_summaries,
        "comparison_diagnostics": build_comparison_diagnostics(active_results),
        "calibration_applied_count": sum(
            1
            for calibration_result in calibration_results
            if calibration_result is not None and calibration_result.applied
        ),
    }


def build_comparison_diagnostics(
    active_results: Sequence[LabelEvaluationResult],
) -> dict[str, int]:
    iml_only_correct_vs_baselines = 0
    baselines_only_correct_vs_iml = 0
    all_methods_correct = 0
    all_methods_wrong = 0

    for result in active_results:
        active_correct = result.correct
        naive_correct = result.naive_summary_correct
        full_history_correct = result.full_history_correct

        if active_correct and not naive_correct and not full_history_correct:
            iml_only_correct_vs_baselines += 1
        if not active_correct and (naive_correct or full_history_correct):
            baselines_only_correct_vs_iml += 1
        if active_correct and naive_correct and full_history_correct:
            all_methods_correct += 1
        if not active_correct and not naive_correct and not full_history_correct:
            all_methods_wrong += 1

    return {
        "iml_only_correct_vs_baselines": iml_only_correct_vs_baselines,
        "baselines_only_correct_vs_iml": baselines_only_correct_vs_iml,
        "all_methods_correct": all_methods_correct,
        "all_methods_wrong": all_methods_wrong,
    }


def build_baseline_comparison(
    active_results: list[LabelEvaluationResult],
    original_results: list[LabelEvaluationResult],
    use_calibration: bool,
) -> dict[str, Any]:
    active_method_name = "calibrated_iml" if use_calibration else "iml"
    method_summaries = build_method_summaries(
        active_results=active_results,
        original_results=original_results,
        use_calibration=use_calibration,
    )
    active_summary = method_summaries[active_method_name]
    naive_summary = method_summaries["naive_summary"]
    full_history_summary = method_summaries["full_history"]

    comparison = {
        "active_method_name": active_method_name,
        "active_method": active_summary,
        "naive_summary": naive_summary,
        "full_history": full_history_summary,
        "accuracy_delta_vs_naive_summary": (
            active_summary["accuracy"] - naive_summary["accuracy"]
        ),
        "accuracy_delta_vs_full_history": (
            active_summary["accuracy"] - full_history_summary["accuracy"]
        ),
    }

    if use_calibration:
        original_iml_summary = method_summaries["original_iml"]
        comparison["original_iml"] = original_iml_summary
        comparison["accuracy_delta_vs_original_iml"] = (
            active_summary["accuracy"] - original_iml_summary["accuracy"]
        )

    return comparison


def build_export_payload(
    active_results: list[LabelEvaluationResult],
    original_results: list[LabelEvaluationResult],
    calibration_results: list[SupportV1CalibrationResult | None],
    per_label_results: list[dict[str, Any]],
    event_mapping_version: str,
    use_calibration: bool,
    cases_path: Path,
    labels_path: Path,
) -> dict[str, Any]:
    aggregate_summary = build_aggregate_summary(
        active_results=active_results,
        original_results=original_results,
        calibration_results=calibration_results,
        use_calibration=use_calibration,
    )
    baseline_comparison = build_baseline_comparison(
        active_results=active_results,
        original_results=original_results,
        use_calibration=use_calibration,
    )
    flag_breakdown = build_flag_breakdown(active_results)

    return {
        "run_metadata": {
            "evaluation_name": "support_v1_label_evaluation",
            "generated_at": datetime.now().astimezone().isoformat(),
            "runner_path": project_relative_path(Path(__file__).resolve()),
            "dataset_path": format_dataset_path(cases_path),
            "labels_path": format_dataset_path(labels_path),
            "export_path": project_relative_path(EXPORT_PATH),
            "event_mapping_version": event_mapping_version,
            "mode": "calibrated" if use_calibration else "default",
            "calibration_enabled": use_calibration,
            "stakes": EVALUATION_STAKES,
            "decay_gap_days": DECAY_GAP_DAYS,
            "label_count": len(active_results),
            "calibration": {
                "enabled": use_calibration,
                "name": CALIBRATION_NAME,
                "version": CALIBRATION_VERSION,
                "settings": asdict(WINNING_SETTINGS) if use_calibration else None,
            },
        },
        "aggregate_summary": aggregate_summary,
        "baseline_comparison": baseline_comparison,
        "flag_breakdown": flag_breakdown,
        "per_label_results": per_label_results,
    }


def format_review_bool(value: bool) -> str:
    return "true" if value else "false"


def format_review_float(value: float) -> str:
    return f"{value:.6f}"


def build_review_row(
    active_result: LabelEvaluationResult,
    original_result: LabelEvaluationResult,
    calibration_result: SupportV1CalibrationResult | None,
    use_calibration: bool,
) -> dict[str, Any]:
    active_method_name = "calibrated_iml" if use_calibration else "iml"
    confidence_adjustment = (
        calibration_result.confidence_adjustment if calibration_result else 0.0
    )
    unknownness_reduction = (
        calibration_result.unknownness_reduction if calibration_result else 0.0
    )
    calibration_applied = (
        calibration_result.applied if calibration_result is not None else False
    )

    return {
        "label_id": active_result.label.label_id,
        "entity_id": active_result.label.entity_id,
        "ticket_id": active_result.label.ticket_id,
        "decision_timestamp": active_result.label.decision_timestamp.isoformat(),
        "should_route": active_result.label.should_route,
        "active_method_name": active_method_name,
        "active_predicted_path": active_result.predicted_path,
        "active_correct": format_review_bool(active_result.correct),
        "original_iml_predicted_path": original_result.predicted_path,
        "original_iml_correct": format_review_bool(original_result.correct),
        "naive_summary_predicted_path": active_result.naive_summary_predicted_path,
        "naive_summary_correct": format_review_bool(active_result.naive_summary_correct),
        "full_history_predicted_path": active_result.full_history_predicted_path,
        "full_history_correct": format_review_bool(active_result.full_history_correct),
        "contradiction_present": format_review_bool(
            active_result.label.contradiction_present
        ),
        "profile_too_stale": format_review_bool(active_result.label.profile_too_stale),
        "wrong_first_impression": format_review_bool(
            active_result.label.wrong_first_impression
        ),
        "visible_event_count": active_result.visible_event_count,
        "overall_confidence": format_review_float(active_result.overall_confidence),
        "unknownness": format_review_float(active_result.unknownness),
        "freshness": format_review_float(active_result.freshness),
        "contradiction_load": format_review_float(active_result.contradiction_load),
        "calibration_applied": format_review_bool(calibration_applied),
        "confidence_adjustment": format_review_float(confidence_adjustment),
        "unknownness_reduction": format_review_float(unknownness_reduction),
    }


def export_json_results(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_export_path = EXPORT_PATH.with_name(
        f"{EXPORT_PATH.stem}.{uuid4().hex}.tmp"
    )
    with temp_export_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_export_path.replace(EXPORT_PATH)
    return EXPORT_PATH


def export_review_results(
    export_path: Path,
    review_rows: Sequence[dict[str, Any]],
) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_export_path = export_path.with_name(f"{export_path.stem}.{uuid4().hex}.tmp")
    with temp_export_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(review_rows)
    temp_export_path.replace(export_path)
    return export_path


def print_method_summary(label: str, summary: dict[str, Any]) -> None:
    print(
        " | ".join(
            [
                f"method={label}",
                f"correct={summary['correct_predictions']}",
                f"incorrect={summary['incorrect_predictions']}",
                f"accuracy={format_percent(float(summary['accuracy']))}",
            ]
        )
    )


def format_optional_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return format_percent(value)


def print_route_quality_summary(label: str, summary: dict[str, Any]) -> None:
    print(
        " | ".join(
            [
                f"method={label}",
                (
                    "fast_path_precision="
                    f"{format_optional_percent(summary['fast_path_precision'])}"
                ),
                (
                    "fast_path_recall="
                    f"{format_optional_percent(summary['fast_path_recall'])}"
                ),
                (
                    "deep_path_precision="
                    f"{format_optional_percent(summary['deep_path_precision'])}"
                ),
                (
                    "deep_path_recall="
                    f"{format_optional_percent(summary['deep_path_recall'])}"
                ),
            ]
        )
    )


def print_comparison_diagnostics(summary: dict[str, int]) -> None:
    for key, value in summary.items():
        print(f"{key}={value}")


def print_summary(
    payload: dict[str, Any],
    json_export_path: Path,
    review_export_path: Path,
    errors_export_path: Path,
    route_changes_export_path: Path,
    use_calibration: bool,
    cases_path: Path,
    labels_path: Path,
) -> None:
    aggregate_summary = payload["aggregate_summary"]
    method_summaries = aggregate_summary["methods"]
    comparison_diagnostics = aggregate_summary["comparison_diagnostics"]
    flag_breakdown = payload["flag_breakdown"]

    print("support_v1 decision-point label evaluation")
    print(f"mode: {'calibrated' if use_calibration else 'default'}")
    print(f"calibration_enabled: {use_calibration}")
    print(f"cases_path: {format_dataset_path(cases_path)}")
    print(f"labels_path: {format_dataset_path(labels_path)}")
    print(
        " | ".join(
            [
                f"total_labels={aggregate_summary['total_labels']}",
                f"correct={aggregate_summary['correct_predictions']}",
                f"incorrect={aggregate_summary['incorrect_predictions']}",
                f"accuracy={format_percent(float(aggregate_summary['accuracy']))}",
                (
                    "calibration_applied="
                    f"{aggregate_summary['calibration_applied_count']}"
                ),
            ]
        )
    )
    print("method_comparison:")
    print_method_summary(
        aggregate_summary["active_method_name"],
        method_summaries[aggregate_summary["active_method_name"]],
    )
    print_method_summary("naive_summary", method_summaries["naive_summary"])
    print_method_summary("full_history", method_summaries["full_history"])
    if use_calibration:
        print_method_summary("original_iml", method_summaries["original_iml"])
    print("route_quality:")
    print_route_quality_summary(
        aggregate_summary["active_method_name"],
        method_summaries[aggregate_summary["active_method_name"]],
    )
    print_route_quality_summary("naive_summary", method_summaries["naive_summary"])
    print_route_quality_summary("full_history", method_summaries["full_history"])
    if use_calibration:
        print_route_quality_summary("original_iml", method_summaries["original_iml"])
    print("comparison_diagnostics:")
    print_comparison_diagnostics(comparison_diagnostics)
    print("flag_breakdown:")
    for flag_name in FLAG_FIELDS:
        flag_summary = flag_breakdown[flag_name]
        accuracy = flag_summary["accuracy"]
        accuracy_text = format_percent(float(accuracy)) if accuracy is not None else "n/a"
        print(
            " | ".join(
                [
                    f"{flag_name}=true",
                    f"labels={flag_summary['flagged_labels']}",
                    f"correct={flag_summary['correct_predictions']}",
                    f"incorrect={flag_summary['incorrect_predictions']}",
                    f"accuracy={accuracy_text}",
                ]
            )
        )
    print(f"json_artifact: {project_relative_path(json_export_path)}")
    print(f"csv_review_artifact: {project_relative_path(review_export_path)}")
    print(f"csv_errors_artifact: {project_relative_path(errors_export_path)}")
    print(
        "csv_route_changes_artifact: "
        f"{project_relative_path(route_changes_export_path)}"
    )


def main() -> None:
    args = parse_args()
    cases_path = resolve_input_path(args.cases_path, SOURCE_PATH)
    labels_path = resolve_input_path(args.labels_path, LABELS_PATH)

    print(f"cases_path: {format_dataset_path(cases_path)}")
    print(f"labels_path: {format_dataset_path(labels_path)}")

    cases = load_support_cases(cases_path)
    labels = load_support_labels(labels_path)
    entity_events, event_mapping_version = build_entity_events(cases)
    cases_by_ticket_id = {case.case_id: case for case in cases}

    active_results: list[LabelEvaluationResult] = []
    original_results: list[LabelEvaluationResult] = []
    calibration_results: list[SupportV1CalibrationResult | None] = []
    per_label_results: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    error_review_rows: list[dict[str, Any]] = []
    route_change_review_rows: list[dict[str, Any]] = []

    for label in labels:
        validate_label(label, cases_by_ticket_id, entity_events)
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
        review_row = build_review_row(
            active_result=active_result,
            original_result=original_result,
            calibration_result=calibration_result,
            use_calibration=args.calibrated,
        )
        review_rows.append(review_row)
        if not active_result.correct:
            error_review_rows.append(review_row)
        if (
            args.calibrated
            and active_result.predicted_path != original_result.predicted_path
        ):
            route_change_review_rows.append(review_row)

    export_payload = build_export_payload(
        active_results=active_results,
        original_results=original_results,
        calibration_results=calibration_results,
        per_label_results=per_label_results,
        event_mapping_version=event_mapping_version,
        use_calibration=args.calibrated,
        cases_path=cases_path,
        labels_path=labels_path,
    )
    json_export_path = export_json_results(export_payload)
    review_export_path = export_review_results(REVIEW_EXPORT_PATH, review_rows)
    errors_export_path = export_review_results(ERRORS_EXPORT_PATH, error_review_rows)
    route_changes_export_path = export_review_results(
        ROUTE_CHANGES_EXPORT_PATH,
        route_change_review_rows,
    )
    print_summary(
        payload=export_payload,
        json_export_path=json_export_path,
        review_export_path=review_export_path,
        errors_export_path=errors_export_path,
        route_changes_export_path=route_changes_export_path,
        use_calibration=args.calibrated,
        cases_path=cases_path,
        labels_path=labels_path,
    )


if __name__ == "__main__":
    main()
