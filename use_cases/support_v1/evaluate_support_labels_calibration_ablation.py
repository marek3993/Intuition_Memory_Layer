from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from datetime import datetime
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
    LABELS_PATH,
    Event,
    LabelEvaluationResult,
    SupportLabel,
    build_entity_events,
    evaluate_label,
    format_percent,
    load_support_labels,
    project_relative_path,
    validate_label,
)
from evaluate_support_labels_calibration import (
    CALIBRATION_NAME,
    CONFIDENCE_BOOST_CAP,
    CONFIDENCE_BOOST_FACTOR,
    CalibrationAssessment,
    MAX_CONTRADICTION_LOAD,
    MAX_LAST_EVENT_AGE_HOURS,
    MIN_COOPERATIVENESS,
    MIN_RECENT_COOPERATIVE_EVENTS,
    MIN_RECENT_FULFILLED_EVENTS,
    MIN_RECENT_POSITIVE_EVENTS,
    MIN_RECENT_POSITIVE_WEIGHT,
    MIN_TRUST,
    RECENT_WINDOW_DAYS,
    UNKNOWNNESS_REDUCTION_CAP,
    UNKNOWNNESS_REDUCTION_FACTOR,
    apply_calibration,
    assess_calibration_window,
    build_original_iml_payload,
    replay_visible_history,
    summarize_accuracy,
)
from iml.decision import DecisionContext, route_decision
from iml.models import IntuitionProfile, clamp

EXPORT_PATH = ARTIFACTS_DIR / "support_label_calibration_ablation.json"
ABLATION_NAME = "support_v1_label_calibration_ablation"
VARIANT_NAMES: tuple[str, ...] = (
    "original_iml",
    "confidence_only",
    "unknownness_only",
    "confidence_and_unknownness",
)


@dataclass(frozen=True)
class VariantRouteResult:
    variant_name: str
    predicted_path: str
    predicted_reason: str
    correct: bool
    overall_confidence: float
    unknownness: float
    confidence_adjustment: float
    unknownness_reduction: float
    route_changed_from_original: bool


@dataclass(frozen=True)
class AblationLabelResult:
    original: LabelEvaluationResult
    calibration_assessment: CalibrationAssessment
    variant_results: dict[str, VariantRouteResult]


def evaluate_variant(
    label: SupportLabel,
    original_result: LabelEvaluationResult,
    profile: IntuitionProfile,
    confidence_adjustment: float,
    unknownness_reduction: float,
    *,
    apply_confidence: bool,
    apply_unknownness: bool,
    variant_name: str,
) -> VariantRouteResult:
    variant_profile = copy.deepcopy(profile)

    if apply_confidence:
        variant_profile.overall_confidence = clamp(
            variant_profile.overall_confidence + confidence_adjustment
        )

    if apply_unknownness:
        variant_profile.unknownness = clamp(
            variant_profile.unknownness - unknownness_reduction
        )

    decision = route_decision(
        variant_profile,
        DecisionContext(stakes=EVALUATION_STAKES),
    )

    return VariantRouteResult(
        variant_name=variant_name,
        predicted_path=decision.selected_path,
        predicted_reason=decision.reason,
        correct=decision.selected_path == label.should_route,
        overall_confidence=variant_profile.overall_confidence,
        unknownness=variant_profile.unknownness,
        confidence_adjustment=confidence_adjustment if apply_confidence else 0.0,
        unknownness_reduction=unknownness_reduction if apply_unknownness else 0.0,
        route_changed_from_original=decision.selected_path != original_result.predicted_path,
    )


def run_ablation_for_label(
    label: SupportLabel,
    entity_events: dict[str, list[Event]],
) -> AblationLabelResult:
    original_result = build_original_result(label, entity_events)
    replay_snapshot = replay_visible_history(label, entity_events)
    assessment = assess_calibration_window(label, replay_snapshot)
    _, confidence_adjustment, unknownness_reduction = apply_calibration(
        replay_snapshot.profile,
        assessment,
    )

    variant_results = {
        "original_iml": evaluate_variant(
            label,
            original_result,
            replay_snapshot.profile,
            confidence_adjustment,
            unknownness_reduction,
            apply_confidence=False,
            apply_unknownness=False,
            variant_name="original_iml",
        ),
        "confidence_only": evaluate_variant(
            label,
            original_result,
            replay_snapshot.profile,
            confidence_adjustment,
            unknownness_reduction,
            apply_confidence=assessment.eligible,
            apply_unknownness=False,
            variant_name="confidence_only",
        ),
        "unknownness_only": evaluate_variant(
            label,
            original_result,
            replay_snapshot.profile,
            confidence_adjustment,
            unknownness_reduction,
            apply_confidence=False,
            apply_unknownness=assessment.eligible,
            variant_name="unknownness_only",
        ),
        "confidence_and_unknownness": evaluate_variant(
            label,
            original_result,
            replay_snapshot.profile,
            confidence_adjustment,
            unknownness_reduction,
            apply_confidence=assessment.eligible,
            apply_unknownness=assessment.eligible,
            variant_name="confidence_and_unknownness",
        ),
    }

    return AblationLabelResult(
        original=original_result,
        calibration_assessment=assessment,
        variant_results=variant_results,
    )


def build_original_result(
    label: SupportLabel,
    entity_events: dict[str, list[Event]],
) -> LabelEvaluationResult:
    return evaluate_label(label, entity_events)


def build_variant_aggregate_results(
    results: list[AblationLabelResult],
) -> dict[str, Any]:
    aggregates: dict[str, Any] = {}

    for variant_name in VARIANT_NAMES:
        summary = summarize_accuracy(
            [result.variant_results[variant_name].correct for result in results]
        )
        aggregates[variant_name] = {
            **summary,
            "labels_with_route_change": sum(
                1
                for result in results
                if result.variant_results[variant_name].route_changed_from_original
            ),
        }

    return aggregates


def build_changed_label_summaries(
    results: list[AblationLabelResult],
) -> dict[str, list[dict[str, Any]]]:
    summaries: dict[str, list[dict[str, Any]]] = {}

    for variant_name in VARIANT_NAMES:
        changed_labels: list[dict[str, Any]] = []
        for result in results:
            variant_result = result.variant_results[variant_name]
            if not variant_result.route_changed_from_original:
                continue

            changed_labels.append(
                {
                    "label_id": result.original.label.label_id,
                    "ticket_id": result.original.label.ticket_id,
                    "should_route": result.original.label.should_route,
                    "original_path": result.original.predicted_path,
                    "variant_path": variant_result.predicted_path,
                    "original_reason": result.original.predicted_reason,
                    "variant_reason": variant_result.predicted_reason,
                    "confidence_before": result.original.overall_confidence,
                    "confidence_after": variant_result.overall_confidence,
                    "unknownness_before": result.original.unknownness,
                    "unknownness_after": variant_result.unknownness,
                    "confidence_adjustment": variant_result.confidence_adjustment,
                    "unknownness_reduction": variant_result.unknownness_reduction,
                }
            )

        summaries[variant_name] = changed_labels

    return summaries


def build_per_label_route_outputs(
    results: list[AblationLabelResult],
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []

    for result in results:
        original_payload = build_original_iml_payload(result.original)
        assessment = result.calibration_assessment

        payloads.append(
            {
                "label": original_payload["label"],
                "visible_history": original_payload["visible_history"],
                "profile_snapshot": original_payload["profile_snapshot"],
                "revalidation": original_payload["revalidation"],
                "calibration_assessment": {
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
                },
                "variants": {
                    variant_name: {
                        "predicted_path": variant_result.predicted_path,
                        "predicted_reason": variant_result.predicted_reason,
                        "correct": variant_result.correct,
                        "overall_confidence": variant_result.overall_confidence,
                        "unknownness": variant_result.unknownness,
                        "confidence_adjustment": variant_result.confidence_adjustment,
                        "unknownness_reduction": variant_result.unknownness_reduction,
                        "route_changed_from_original": (
                            variant_result.route_changed_from_original
                        ),
                    }
                    for variant_name, variant_result in result.variant_results.items()
                },
            }
        )

    return payloads


def build_export_payload(
    results: list[AblationLabelResult],
    event_mapping_version: str,
) -> dict[str, Any]:
    return {
        "run_metadata": {
            "evaluation_name": ABLATION_NAME,
            "calibration_name": CALIBRATION_NAME,
            "generated_at": datetime.now().astimezone().isoformat(),
            "dataset_path": project_relative_path(SOURCE_PATH),
            "labels_path": project_relative_path(LABELS_PATH),
            "export_path": project_relative_path(EXPORT_PATH),
            "event_mapping_version": event_mapping_version,
            "stakes": EVALUATION_STAKES,
            "decay_gap_days": DECAY_GAP_DAYS,
            "label_count": len(results),
            "variants": list(VARIANT_NAMES),
            "calibration_source_script": project_relative_path(
                SCRIPT_DIR / "evaluate_support_labels_calibration.py"
            ),
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
        "per_variant_aggregate_results": build_variant_aggregate_results(results),
        "per_label_route_outputs": build_per_label_route_outputs(results),
        "changed_label_summaries": build_changed_label_summaries(results),
    }


def export_results(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with EXPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return EXPORT_PATH


def print_comparison_table(results: list[AblationLabelResult]) -> None:
    aggregates = build_variant_aggregate_results(results)

    print("variant_comparison:")
    print("variant | correct | incorrect | accuracy")
    for variant_name in VARIANT_NAMES:
        summary = aggregates[variant_name]
        print(
            " | ".join(
                [
                    variant_name,
                    str(summary["correct_predictions"]),
                    str(summary["incorrect_predictions"]),
                    format_percent(float(summary["accuracy"])),
                ]
            )
        )


def print_changed_label_summary(results: list[AblationLabelResult]) -> None:
    changed_summaries = build_changed_label_summaries(results)

    print()
    print("changed_labels_by_variant:")
    for variant_name in VARIANT_NAMES:
        changed_labels = changed_summaries[variant_name]
        if not changed_labels:
            print(f"{variant_name}: none")
            continue

        label_summary = ", ".join(
            [
                (
                    f"{item['label_id']}({item['ticket_id']}: "
                    f"{item['original_path']}->{item['variant_path']})"
                )
                for item in changed_labels
            ]
        )
        print(f"{variant_name}: {label_summary}")


def main() -> None:
    cases = load_support_cases(SOURCE_PATH)
    labels = load_support_labels(LABELS_PATH)
    entity_events, event_mapping_version = build_entity_events(cases)
    cases_by_ticket_id = {case.case_id: case for case in cases}

    print("support_v1 label calibration ablation")
    print(f"dataset: {project_relative_path(SOURCE_PATH)}")
    print(f"labels: {project_relative_path(LABELS_PATH)}")
    print(f"artifact: {project_relative_path(EXPORT_PATH)}")
    print(f"calibration_name: {CALIBRATION_NAME}")
    print()

    results: list[AblationLabelResult] = []
    for label in labels:
        validate_label(label, cases_by_ticket_id, entity_events)
        results.append(run_ablation_for_label(label, entity_events))

    print_comparison_table(results)
    print_changed_label_summary(results)

    export_payload = build_export_payload(results, event_mapping_version)
    export_path = export_results(export_payload)

    print()
    print(f"evaluation_export: {project_relative_path(export_path)}")


if __name__ == "__main__":
    main()
