from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from convert_support_cases_to_events import SOURCE_PATH, load_support_cases
from evaluate_support_labels import (
    ARTIFACTS_DIR,
    DECAY_GAP_DAYS,
    EVALUATION_STAKES,
    FLAG_FIELDS,
    LABELS_PATH,
    LabelEvaluationResult,
    SupportLabel,
    build_flag_breakdown,
    build_result_payload,
    evaluate_label,
    format_float,
    format_percent,
    load_support_labels,
    make_profile,
    maybe_apply_gap_decay,
    project_relative_path,
    validate_label,
    build_entity_events,
)
from iml.decay import apply_decay
from iml.decision import DecisionContext, route_decision
from iml.models import Event, IntuitionProfile, clamp
from iml.revalidate import RevalidationResult, revalidate_profile
from iml.update_engine import apply_event

EXPORT_PATH = ARTIFACTS_DIR / "support_label_calibration_experiment.json"
CALIBRATION_NAME = "clean_recent_cooperation_confidence_unknownness_v1"
RECENT_WINDOW_DAYS = 14
MAX_LAST_EVENT_AGE_HOURS = 72.0
MAX_CONTRADICTION_LOAD = 0.05
MIN_RECENT_POSITIVE_EVENTS = 3
MIN_RECENT_COOPERATIVE_EVENTS = 2
MIN_RECENT_FULFILLED_EVENTS = 1
MIN_TRUST = 0.60
MIN_COOPERATIVENESS = 0.55
MIN_RECENT_POSITIVE_WEIGHT = 1.90
CONFIDENCE_BOOST_FACTOR = 0.12
CONFIDENCE_BOOST_CAP = 0.24
UNKNOWNNESS_REDUCTION_FACTOR = 0.11
UNKNOWNNESS_REDUCTION_CAP = 0.22


@dataclass(frozen=True)
class ReplaySnapshot:
    visible_events: tuple[Event, ...]
    profile: IntuitionProfile
    revalidation: RevalidationResult
    decay_checkpoints: int
    visible_event_type_counts: dict[str, int]


@dataclass(frozen=True)
class CalibrationAssessment:
    eligible: bool
    condition_checks: dict[str, bool]
    recent_positive_events: int
    recent_cooperative_events: int
    recent_fulfilled_events: int
    recent_negative_events: int
    recent_inactivity_events: int
    total_contradiction_events: int
    total_long_inactivity_events: int
    recent_positive_weight: float
    last_event_age_hours: float


@dataclass(frozen=True)
class CalibrationExperimentResult:
    original: LabelEvaluationResult
    calibrated_predicted_path: str
    calibrated_predicted_reason: str
    calibrated_correct: bool
    calibrated_overall_confidence: float
    calibrated_unknownness: float
    confidence_adjustment: float
    unknownness_reduction: float
    route_changed: bool
    calibration_assessment: CalibrationAssessment


def event_weight(event: Event) -> float:
    return abs(event.polarity) * event.reliability * event.intensity


def replay_visible_history(
    label: SupportLabel,
    entity_events: dict[str, list[Event]],
) -> ReplaySnapshot:
    visible_events = tuple(
        event
        for event in entity_events[label.entity_id]
        if event.timestamp <= label.decision_timestamp
    )
    profile_start_time = visible_events[0].timestamp if visible_events else label.decision_timestamp
    profile = make_profile(label.entity_id, profile_start_time)
    event_type_counts: dict[str, int] = {}
    decay_checkpoints = 0

    for event in visible_events:
        if maybe_apply_gap_decay(profile, event.timestamp):
            decay_checkpoints += 1
        apply_event(profile, event)
        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1

    apply_decay(profile, now=label.decision_timestamp)
    revalidation_result = revalidate_profile(profile, now=label.decision_timestamp)

    return ReplaySnapshot(
        visible_events=visible_events,
        profile=profile,
        revalidation=revalidation_result,
        decay_checkpoints=decay_checkpoints,
        visible_event_type_counts=dict(sorted(event_type_counts.items())),
    )


def assess_calibration_window(
    label: SupportLabel,
    replay_snapshot: ReplaySnapshot,
) -> CalibrationAssessment:
    visible_events = replay_snapshot.visible_events
    profile = replay_snapshot.profile
    recent_threshold = label.decision_timestamp - timedelta(days=RECENT_WINDOW_DAYS)
    recent_events = [event for event in visible_events if event.timestamp >= recent_threshold]

    recent_positive_events = [event for event in recent_events if event.polarity > 0]
    recent_negative_events = [event for event in recent_events if event.polarity < 0]
    recent_cooperative_events = [
        event for event in recent_positive_events if event.event_type == "cooperative_response"
    ]
    recent_fulfilled_events = [
        event for event in recent_positive_events if event.event_type == "fulfilled_commitment"
    ]
    recent_inactivity_events = [
        event for event in recent_events if event.event_type == "long_inactivity"
    ]
    contradiction_events = [
        event for event in visible_events if event.event_type == "contradiction_detected"
    ]
    long_inactivity_events = [
        event for event in visible_events if event.event_type == "long_inactivity"
    ]

    if visible_events:
        last_event_age_hours = (
            label.decision_timestamp - visible_events[-1].timestamp
        ).total_seconds() / 3_600
    else:
        last_event_age_hours = float("inf")

    recent_positive_weight = sum(event_weight(event) for event in recent_positive_events)

    condition_checks = {
        "no_contradiction_events": len(contradiction_events) == 0,
        "low_contradiction_load": profile.contradiction_load <= MAX_CONTRADICTION_LOAD,
        "recent_evidence": last_event_age_hours <= MAX_LAST_EVENT_AGE_HOURS,
        "multiple_recent_positive_events": len(recent_positive_events)
        >= MIN_RECENT_POSITIVE_EVENTS,
        "multiple_recent_cooperative_events": len(recent_cooperative_events)
        >= MIN_RECENT_COOPERATIVE_EVENTS,
        "recent_fulfilled_commitment": len(recent_fulfilled_events)
        >= MIN_RECENT_FULFILLED_EVENTS,
        "no_recent_negative_pressure": len(recent_negative_events) == 0,
        "no_inactivity_pressure": len(long_inactivity_events) == 0
        and len(recent_inactivity_events) == 0,
        "supportive_profile_signal": profile.attributes["trust"].value >= MIN_TRUST
        and profile.attributes["cooperativeness"].value >= MIN_COOPERATIVENESS,
        "dense_recent_positive_weight": recent_positive_weight >= MIN_RECENT_POSITIVE_WEIGHT,
    }

    return CalibrationAssessment(
        eligible=all(condition_checks.values()),
        condition_checks=condition_checks,
        recent_positive_events=len(recent_positive_events),
        recent_cooperative_events=len(recent_cooperative_events),
        recent_fulfilled_events=len(recent_fulfilled_events),
        recent_negative_events=len(recent_negative_events),
        recent_inactivity_events=len(recent_inactivity_events),
        total_contradiction_events=len(contradiction_events),
        total_long_inactivity_events=len(long_inactivity_events),
        recent_positive_weight=recent_positive_weight,
        last_event_age_hours=last_event_age_hours,
    )


def apply_calibration(
    profile: IntuitionProfile,
    assessment: CalibrationAssessment,
) -> tuple[IntuitionProfile, float, float]:
    calibrated_profile = copy.deepcopy(profile)

    if not assessment.eligible:
        return calibrated_profile, 0.0, 0.0

    confidence_adjustment = min(
        CONFIDENCE_BOOST_CAP,
        assessment.recent_positive_weight * CONFIDENCE_BOOST_FACTOR,
    )
    unknownness_reduction = min(
        UNKNOWNNESS_REDUCTION_CAP,
        assessment.recent_positive_weight * UNKNOWNNESS_REDUCTION_FACTOR,
    )

    calibrated_profile.overall_confidence = clamp(
        calibrated_profile.overall_confidence + confidence_adjustment
    )
    calibrated_profile.unknownness = clamp(
        calibrated_profile.unknownness - unknownness_reduction
    )

    return calibrated_profile, confidence_adjustment, unknownness_reduction


def run_calibration_experiment_for_label(
    label: SupportLabel,
    entity_events: dict[str, list[Event]],
) -> CalibrationExperimentResult:
    original_result = evaluate_label(label, entity_events)
    replay_snapshot = replay_visible_history(label, entity_events)
    assessment = assess_calibration_window(label, replay_snapshot)
    calibrated_profile, confidence_adjustment, unknownness_reduction = apply_calibration(
        replay_snapshot.profile,
        assessment,
    )
    calibrated_decision = route_decision(
        calibrated_profile,
        DecisionContext(stakes=EVALUATION_STAKES),
    )

    return CalibrationExperimentResult(
        original=original_result,
        calibrated_predicted_path=calibrated_decision.selected_path,
        calibrated_predicted_reason=calibrated_decision.reason,
        calibrated_correct=calibrated_decision.selected_path == label.should_route,
        calibrated_overall_confidence=calibrated_profile.overall_confidence,
        calibrated_unknownness=calibrated_profile.unknownness,
        confidence_adjustment=confidence_adjustment,
        unknownness_reduction=unknownness_reduction,
        route_changed=calibrated_decision.selected_path != original_result.predicted_path,
        calibration_assessment=assessment,
    )


def summarize_accuracy(correct_values: list[bool]) -> dict[str, Any]:
    total = len(correct_values)
    correct_predictions = sum(1 for value in correct_values if value)
    incorrect_predictions = total - correct_predictions
    return {
        "correct_predictions": correct_predictions,
        "incorrect_predictions": incorrect_predictions,
        "accuracy": (correct_predictions / total) if total else 0.0,
    }


def build_calibrated_flag_breakdown(
    results: list[CalibrationExperimentResult],
) -> dict[str, Any]:
    breakdown: dict[str, Any] = {}

    for flag_name in FLAG_FIELDS:
        flagged_results = [
            result for result in results if bool(getattr(result.original.label, flag_name))
        ]
        summary = summarize_accuracy(
            [result.calibrated_correct for result in flagged_results]
        )
        breakdown[flag_name] = {
            "flagged_labels": len(flagged_results),
            "correct_predictions": summary["correct_predictions"],
            "incorrect_predictions": summary["incorrect_predictions"],
            "accuracy": summary["accuracy"] if flagged_results else None,
        }

    return breakdown


def build_original_iml_payload(result: LabelEvaluationResult) -> dict[str, Any]:
    payload = build_result_payload(result)
    return {
        "label": payload["label"],
        "prediction": {
            "predicted_path": result.predicted_path,
            "predicted_reason": result.predicted_reason,
            "correct": result.correct,
        },
        "visible_history": payload["visible_history"],
        "profile_snapshot": payload["profile_snapshot"],
        "revalidation": payload["revalidation"],
    }


def build_calibrated_payload(result: CalibrationExperimentResult) -> dict[str, Any]:
    assessment = result.calibration_assessment
    return {
        "label": {
            "label_id": result.original.label.label_id,
            "entity_id": result.original.label.entity_id,
            "ticket_id": result.original.label.ticket_id,
            "decision_timestamp": result.original.label.decision_timestamp.isoformat(),
            "should_route": result.original.label.should_route,
            "note": result.original.label.note,
        },
        "original_prediction": {
            "predicted_path": result.original.predicted_path,
            "predicted_reason": result.original.predicted_reason,
            "overall_confidence": result.original.overall_confidence,
            "unknownness": result.original.unknownness,
            "correct": result.original.correct,
        },
        "calibrated_prediction": {
            "predicted_path": result.calibrated_predicted_path,
            "predicted_reason": result.calibrated_predicted_reason,
            "overall_confidence": result.calibrated_overall_confidence,
            "unknownness": result.calibrated_unknownness,
            "correct": result.calibrated_correct,
        },
        "calibration": {
            "applied": assessment.eligible,
            "confidence_adjustment": result.confidence_adjustment,
            "unknownness_reduction": result.unknownness_reduction,
            "route_changed": result.route_changed,
            "condition_checks": assessment.condition_checks,
            "recent_window_days": RECENT_WINDOW_DAYS,
            "recent_positive_events": assessment.recent_positive_events,
            "recent_cooperative_events": assessment.recent_cooperative_events,
            "recent_fulfilled_events": assessment.recent_fulfilled_events,
            "recent_negative_events": assessment.recent_negative_events,
            "recent_inactivity_events": assessment.recent_inactivity_events,
            "total_contradiction_events": assessment.total_contradiction_events,
            "total_long_inactivity_events": assessment.total_long_inactivity_events,
            "recent_positive_weight": assessment.recent_positive_weight,
            "last_event_age_hours": assessment.last_event_age_hours,
        },
    }


def build_baseline_payload(results: list[CalibrationExperimentResult]) -> dict[str, Any]:
    return {
        "naive_summary": [
            {
                "label_id": result.original.label.label_id,
                "predicted_path": result.original.naive_summary_predicted_path,
                "decision_reason": result.original.naive_summary_decision_reason,
                "correct": result.original.naive_summary_correct,
            }
            for result in results
        ],
        "full_history": [
            {
                "label_id": result.original.label.label_id,
                "predicted_path": result.original.full_history_predicted_path,
                "decision_reason": result.original.full_history_decision_reason,
                "correct": result.original.full_history_correct,
            }
            for result in results
        ],
    }


def build_changed_route_payload(
    results: list[CalibrationExperimentResult],
) -> list[dict[str, Any]]:
    changed_routes: list[dict[str, Any]] = []

    for result in results:
        if not result.route_changed:
            continue

        changed_routes.append(
            {
                "label_id": result.original.label.label_id,
                "ticket_id": result.original.label.ticket_id,
                "should_route": result.original.label.should_route,
                "original_path": result.original.predicted_path,
                "calibrated_path": result.calibrated_predicted_path,
                "original_reason": result.original.predicted_reason,
                "calibrated_reason": result.calibrated_predicted_reason,
                "confidence_before": result.original.overall_confidence,
                "confidence_after": result.calibrated_overall_confidence,
                "unknownness_before": result.original.unknownness,
                "unknownness_after": result.calibrated_unknownness,
                "confidence_adjustment": result.confidence_adjustment,
                "unknownness_reduction": result.unknownness_reduction,
                "condition_checks": result.calibration_assessment.condition_checks,
            }
        )

    return changed_routes


def build_aggregate_comparison(
    results: list[CalibrationExperimentResult],
) -> dict[str, Any]:
    original_summary = summarize_accuracy([result.original.correct for result in results])
    calibrated_summary = summarize_accuracy([result.calibrated_correct for result in results])
    naive_summary = summarize_accuracy(
        [result.original.naive_summary_correct for result in results]
    )
    full_history_summary = summarize_accuracy(
        [result.original.full_history_correct for result in results]
    )

    return {
        "total_labels": len(results),
        "methods": {
            "original_iml": original_summary,
            "calibrated_iml": calibrated_summary,
            "naive_summary": naive_summary,
            "full_history": full_history_summary,
        },
        "accuracy_delta": calibrated_summary["accuracy"] - original_summary["accuracy"],
        "labels_with_route_change": sum(1 for result in results if result.route_changed),
        "original_iml_flag_breakdown": build_flag_breakdown(
            [result.original for result in results]
        ),
        "calibrated_iml_flag_breakdown": build_calibrated_flag_breakdown(results),
    }


def build_export_payload(
    results: list[CalibrationExperimentResult],
    event_mapping_version: str,
) -> dict[str, Any]:
    changed_routes = build_changed_route_payload(results)

    return {
        "run_metadata": {
            "evaluation_name": "support_v1_label_calibration_experiment",
            "calibration_name": CALIBRATION_NAME,
            "generated_at": datetime.now().astimezone().isoformat(),
            "dataset_path": project_relative_path(SOURCE_PATH),
            "labels_path": project_relative_path(LABELS_PATH),
            "export_path": project_relative_path(EXPORT_PATH),
            "event_mapping_version": event_mapping_version,
            "stakes": EVALUATION_STAKES,
            "decay_gap_days": DECAY_GAP_DAYS,
            "label_count": len(results),
            "calibration_rule": {
                "recent_window_days": RECENT_WINDOW_DAYS,
                "max_last_event_age_hours": MAX_LAST_EVENT_AGE_HOURS,
                "max_contradiction_load": MAX_CONTRADICTION_LOAD,
                "min_recent_positive_events": MIN_RECENT_POSITIVE_EVENTS,
                "min_recent_cooperative_events": MIN_RECENT_COOPERATIVE_EVENTS,
                "min_recent_fulfilled_events": MIN_RECENT_FULFILLED_EVENTS,
                "min_recent_positive_weight": MIN_RECENT_POSITIVE_WEIGHT,
                "min_trust": MIN_TRUST,
                "min_cooperativeness": MIN_COOPERATIVENESS,
                "confidence_boost_factor": CONFIDENCE_BOOST_FACTOR,
                "confidence_boost_cap": CONFIDENCE_BOOST_CAP,
                "unknownness_reduction_factor": UNKNOWNNESS_REDUCTION_FACTOR,
                "unknownness_reduction_cap": UNKNOWNNESS_REDUCTION_CAP,
            },
        },
        "original_iml_results": [
            build_original_iml_payload(result.original) for result in results
        ],
        "calibrated_iml_results": [
            build_calibrated_payload(result) for result in results
        ],
        "baseline_results": build_baseline_payload(results),
        "labels_with_route_change": changed_routes,
        "aggregate_comparison": build_aggregate_comparison(results),
    }


def export_results(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with EXPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return EXPORT_PATH


def print_accuracy_summary(results: list[CalibrationExperimentResult]) -> None:
    original_accuracy = summarize_accuracy([result.original.correct for result in results])
    calibrated_accuracy = summarize_accuracy(
        [result.calibrated_correct for result in results]
    )
    naive_accuracy = summarize_accuracy(
        [result.original.naive_summary_correct for result in results]
    )
    full_history_accuracy = summarize_accuracy(
        [result.original.full_history_correct for result in results]
    )

    print(
        f"original_iml_accuracy: {format_percent(float(original_accuracy['accuracy']))}"
    )
    print(
        f"calibrated_iml_accuracy: {format_percent(float(calibrated_accuracy['accuracy']))}"
    )
    print(
        f"naive_summary_accuracy: {format_percent(float(naive_accuracy['accuracy']))}"
    )
    print(
        f"full_history_accuracy: {format_percent(float(full_history_accuracy['accuracy']))}"
    )


def print_changed_routes(results: list[CalibrationExperimentResult]) -> None:
    changed_routes = [result for result in results if result.route_changed]
    print("changed_routes:")

    if not changed_routes:
        print("none")
        return

    for result in changed_routes:
        print(
            " | ".join(
                [
                    f"label={result.original.label.label_id}",
                    f"ticket={result.original.label.ticket_id}",
                    f"should_route={result.original.label.should_route}",
                    f"original={result.original.predicted_path}",
                    f"calibrated={result.calibrated_predicted_path}",
                    f"confidence={format_float(result.original.overall_confidence)}->{format_float(result.calibrated_overall_confidence)}",
                    f"unknownness={format_float(result.original.unknownness)}->{format_float(result.calibrated_unknownness)}",
                    f"positive_weight={format_float(result.calibration_assessment.recent_positive_weight)}",
                ]
            )
        )


def main() -> None:
    cases = load_support_cases(SOURCE_PATH)
    labels = load_support_labels(LABELS_PATH)
    entity_events, event_mapping_version = build_entity_events(cases)
    cases_by_ticket_id = {case.case_id: case for case in cases}

    print("support_v1 label calibration experiment")
    print(f"dataset: {project_relative_path(SOURCE_PATH)}")
    print(f"labels: {project_relative_path(LABELS_PATH)}")
    print(f"artifact: {project_relative_path(EXPORT_PATH)}")
    print(f"calibration_name: {CALIBRATION_NAME}")
    print()

    results: list[CalibrationExperimentResult] = []
    for label in labels:
        validate_label(label, cases_by_ticket_id, entity_events)
        results.append(run_calibration_experiment_for_label(label, entity_events))

    print_accuracy_summary(results)
    print()
    print_changed_routes(results)

    export_payload = build_export_payload(results, event_mapping_version)
    export_path = export_results(export_payload)

    print()
    print(f"evaluation_export: {project_relative_path(export_path)}")


if __name__ == "__main__":
    main()
