from __future__ import annotations

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
    format_float,
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
    assess_calibration_window,
    replay_visible_history,
    summarize_accuracy,
)
from evaluate_support_labels_calibration_ablation import (
    VariantRouteResult,
    build_original_result,
    evaluate_variant,
)

EXPORT_PATH = ARTIFACTS_DIR / "support_label_calibration_sweep.json"
SWEEP_NAME = "support_v1_label_calibration_sweep"
CONFIDENCE_BOOST_CAP_LEVELS: tuple[tuple[str, float], ...] = (
    ("low", 0.20),
    ("medium", CONFIDENCE_BOOST_CAP),
    ("high", 0.28),
)
UNKNOWNNESS_REDUCTION_CAP_LEVELS: tuple[tuple[str, float], ...] = (
    ("low", 0.18),
    ("medium", UNKNOWNNESS_REDUCTION_CAP),
    ("high", 0.26),
)


@dataclass(frozen=True)
class SweepSetting:
    setting_name: str
    confidence_level: str
    unknownness_level: str
    confidence_index: int
    unknownness_index: int
    confidence_boost_cap: float
    unknownness_reduction_cap: float


@dataclass(frozen=True)
class SweepLabelResult:
    original: LabelEvaluationResult
    calibration_assessment: CalibrationAssessment
    setting_results: dict[str, VariantRouteResult]


def build_sweep_settings() -> tuple[SweepSetting, ...]:
    settings: list[SweepSetting] = []

    for confidence_index, (confidence_level, confidence_boost_cap) in enumerate(
        CONFIDENCE_BOOST_CAP_LEVELS
    ):
        for unknownness_index, (
            unknownness_level,
            unknownness_reduction_cap,
        ) in enumerate(UNKNOWNNESS_REDUCTION_CAP_LEVELS):
            settings.append(
                SweepSetting(
                    setting_name=(
                        f"conf_{confidence_level}__unknown_{unknownness_level}"
                    ),
                    confidence_level=confidence_level,
                    unknownness_level=unknownness_level,
                    confidence_index=confidence_index,
                    unknownness_index=unknownness_index,
                    confidence_boost_cap=confidence_boost_cap,
                    unknownness_reduction_cap=unknownness_reduction_cap,
                )
            )

    return tuple(settings)


def compute_adjustments(
    assessment: CalibrationAssessment,
    setting: SweepSetting,
) -> tuple[float, float]:
    if not assessment.eligible:
        return 0.0, 0.0

    confidence_adjustment = min(
        setting.confidence_boost_cap,
        assessment.recent_positive_weight * CONFIDENCE_BOOST_FACTOR,
    )
    unknownness_reduction = min(
        setting.unknownness_reduction_cap,
        assessment.recent_positive_weight * UNKNOWNNESS_REDUCTION_FACTOR,
    )
    return confidence_adjustment, unknownness_reduction


def run_sweep_for_label(
    label: SupportLabel,
    entity_events: dict[str, list[Event]],
    sweep_settings: tuple[SweepSetting, ...],
) -> SweepLabelResult:
    original_result = build_original_result(label, entity_events)
    replay_snapshot = replay_visible_history(label, entity_events)
    assessment = assess_calibration_window(label, replay_snapshot)

    setting_results: dict[str, VariantRouteResult] = {}
    for setting in sweep_settings:
        confidence_adjustment, unknownness_reduction = compute_adjustments(
            assessment,
            setting,
        )
        setting_results[setting.setting_name] = evaluate_variant(
            label,
            original_result,
            replay_snapshot.profile,
            confidence_adjustment,
            unknownness_reduction,
            apply_confidence=assessment.eligible,
            apply_unknownness=assessment.eligible,
            variant_name=setting.setting_name,
        )

    return SweepLabelResult(
        original=original_result,
        calibration_assessment=assessment,
        setting_results=setting_results,
    )


def build_setting_aggregate_results(
    results: list[SweepLabelResult],
    sweep_settings: tuple[SweepSetting, ...],
) -> list[dict[str, Any]]:
    eligible_label_count = sum(
        1 for result in results if result.calibration_assessment.eligible
    )
    aggregate_results: list[dict[str, Any]] = []

    for setting in sweep_settings:
        summary = summarize_accuracy(
            [result.setting_results[setting.setting_name].correct for result in results]
        )
        aggregate_results.append(
            {
                "setting_name": setting.setting_name,
                "confidence_level": setting.confidence_level,
                "unknownness_level": setting.unknownness_level,
                "confidence_boost_cap": setting.confidence_boost_cap,
                "unknownness_reduction_cap": setting.unknownness_reduction_cap,
                "eligible_label_count": eligible_label_count,
                "correct_predictions": summary["correct_predictions"],
                "incorrect_predictions": summary["incorrect_predictions"],
                "accuracy": summary["accuracy"],
                "route_changes": sum(
                    1
                    for result in results
                    if result.setting_results[
                        setting.setting_name
                    ].route_changed_from_original
                ),
            }
        )

    return aggregate_results


def build_changed_label_summaries(
    results: list[SweepLabelResult],
    sweep_settings: tuple[SweepSetting, ...],
) -> list[dict[str, Any]]:
    changed_summaries: list[dict[str, Any]] = []

    for setting in sweep_settings:
        changed_labels: list[dict[str, Any]] = []
        for result in results:
            setting_result = result.setting_results[setting.setting_name]
            if not setting_result.route_changed_from_original:
                continue

            changed_labels.append(
                {
                    "label_id": result.original.label.label_id,
                    "ticket_id": result.original.label.ticket_id,
                    "should_route": result.original.label.should_route,
                    "original_path": result.original.predicted_path,
                    "swept_path": setting_result.predicted_path,
                    "original_reason": result.original.predicted_reason,
                    "swept_reason": setting_result.predicted_reason,
                    "confidence_before": result.original.overall_confidence,
                    "confidence_after": setting_result.overall_confidence,
                    "unknownness_before": result.original.unknownness,
                    "unknownness_after": setting_result.unknownness,
                    "confidence_adjustment": setting_result.confidence_adjustment,
                    "unknownness_reduction": setting_result.unknownness_reduction,
                }
            )

        changed_summaries.append(
            {
                "setting_name": setting.setting_name,
                "confidence_level": setting.confidence_level,
                "unknownness_level": setting.unknownness_level,
                "confidence_boost_cap": setting.confidence_boost_cap,
                "unknownness_reduction_cap": setting.unknownness_reduction_cap,
                "changed_label_count": len(changed_labels),
                "changed_labels": changed_labels,
            }
        )

    return changed_summaries


def build_best_settings_summary(
    aggregate_results: list[dict[str, Any]],
    sweep_settings: tuple[SweepSetting, ...],
) -> dict[str, Any]:
    settings_by_name = {setting.setting_name: setting for setting in sweep_settings}
    current_setting = next(
        setting
        for setting in sweep_settings
        if setting.confidence_level == "medium"
        and setting.unknownness_level == "medium"
    )
    current_result = next(
        result
        for result in aggregate_results
        if result["setting_name"] == current_setting.setting_name
    )

    best_accuracy = max(result["accuracy"] for result in aggregate_results)
    best_settings = [
        result for result in aggregate_results if result["accuracy"] == best_accuracy
    ]
    best_route_changes = max(result["route_changes"] for result in best_settings)
    best_settings = [
        result for result in best_settings if result["route_changes"] == best_route_changes
    ]

    current_neighbors = [
        result
        for result in aggregate_results
        if result["setting_name"] != current_setting.setting_name
        and max(
            abs(
                settings_by_name[result["setting_name"]].confidence_index
                - current_setting.confidence_index
            ),
            abs(
                settings_by_name[result["setting_name"]].unknownness_index
                - current_setting.unknownness_index
            ),
        )
        == 1
    ]
    matching_neighbors = [
        result
        for result in current_neighbors
        if result["accuracy"] == current_result["accuracy"]
        and result["route_changes"] == current_result["route_changes"]
    ]
    degraded_neighbors = [
        result
        for result in current_neighbors
        if result["accuracy"] < current_result["accuracy"]
        or result["route_changes"] < current_result["route_changes"]
    ]
    non_decreasing_neighbors = [
        result
        for result in current_neighbors
        if settings_by_name[result["setting_name"]].confidence_boost_cap
        >= current_setting.confidence_boost_cap
        and settings_by_name[result["setting_name"]].unknownness_reduction_cap
        >= current_setting.unknownness_reduction_cap
    ]
    matching_non_decreasing_neighbors = [
        result
        for result in non_decreasing_neighbors
        if result["accuracy"] == current_result["accuracy"]
        and result["route_changes"] == current_result["route_changes"]
    ]

    best_region_min_confidence_boost_cap = min(
        result["confidence_boost_cap"] for result in best_settings
    )
    best_region_min_unknownness_reduction_cap = min(
        result["unknownness_reduction_cap"] for result in best_settings
    )
    plateau_settings = [
        result
        for result in aggregate_results
        if result["confidence_boost_cap"] >= best_region_min_confidence_boost_cap
        and result["unknownness_reduction_cap"] >= best_region_min_unknownness_reduction_cap
    ]
    plateau_matches_best = [
        result
        for result in plateau_settings
        if result["accuracy"] == best_accuracy
        and result["route_changes"] == best_route_changes
    ]
    outside_plateau = [
        result for result in aggregate_results if result not in plateau_settings
    ]
    outside_plateau_degrades = [
        result
        for result in outside_plateau
        if result["accuracy"] < best_accuracy or result["route_changes"] < best_route_changes
    ]
    plateau_is_stable = len(plateau_matches_best) == len(plateau_settings)
    outside_plateau_is_weaker = len(outside_plateau_degrades) == len(outside_plateau)

    if plateau_is_stable and outside_plateau_is_weaker:
        stability_classification = "threshold_plateau"
        stability_summary = (
            "Winning behavior forms a small plateau: every setting with "
            f"confidence_boost_cap >= {format_float(best_region_min_confidence_boost_cap)} "
            "and "
            f"unknownness_reduction_cap >= {format_float(best_region_min_unknownness_reduction_cap)} "
            f"matches the best {best_settings[0]['correct_predictions']}/{best_settings[0]['correct_predictions'] + best_settings[0]['incorrect_predictions']} "
            "result, while every lower setting is worse."
        )
    elif matching_neighbors:
        stability_classification = "partial_local_stability"
        stability_summary = (
            "Winning behavior persists for some nearby settings, but not across the "
            "full local neighborhood."
        )
    else:
        stability_classification = "narrow_optimum"
        stability_summary = "Winning behavior does not persist across nearby settings."

    return {
        "best_accuracy": best_accuracy,
        "best_correct_predictions": max(
            result["correct_predictions"] for result in best_settings
        ),
        "best_incorrect_predictions": min(
            result["incorrect_predictions"] for result in best_settings
        ),
        "best_settings": best_settings,
        "current_winning_setting": current_result,
        "winning_behavior_stability": {
            "classification": stability_classification,
            "current_setting_name": current_setting.setting_name,
            "current_neighbor_count": len(current_neighbors),
            "matching_neighbor_settings": [
                result["setting_name"] for result in matching_neighbors
            ],
            "degraded_neighbor_settings": [
                result["setting_name"] for result in degraded_neighbors
            ],
            "stable_across_all_neighbors": len(degraded_neighbors) == 0,
            "stable_across_non_decreasing_neighbors": (
                len(matching_non_decreasing_neighbors) == len(non_decreasing_neighbors)
            ),
            "non_decreasing_neighbor_settings": [
                result["setting_name"] for result in non_decreasing_neighbors
            ],
            "matching_non_decreasing_neighbor_settings": [
                result["setting_name"] for result in matching_non_decreasing_neighbors
            ],
            "best_region_min_confidence_boost_cap": best_region_min_confidence_boost_cap,
            "best_region_min_unknownness_reduction_cap": (
                best_region_min_unknownness_reduction_cap
            ),
            "plateau_setting_names": [
                result["setting_name"] for result in plateau_settings
            ],
            "plateau_matches_best_setting_names": [
                result["setting_name"] for result in plateau_matches_best
            ],
            "outside_plateau_setting_names": [
                result["setting_name"] for result in outside_plateau
            ],
            "outside_plateau_degraded_setting_names": [
                result["setting_name"] for result in outside_plateau_degrades
            ],
            "summary": stability_summary,
        },
    }


def build_export_payload(
    results: list[SweepLabelResult],
    sweep_settings: tuple[SweepSetting, ...],
    event_mapping_version: str,
) -> dict[str, Any]:
    aggregate_results = build_setting_aggregate_results(results, sweep_settings)
    changed_label_summaries = build_changed_label_summaries(results, sweep_settings)
    original_iml_summary = summarize_accuracy(
        [result.original.correct for result in results]
    )

    return {
        "run_metadata": {
            "evaluation_name": SWEEP_NAME,
            "calibration_name": CALIBRATION_NAME,
            "generated_at": datetime.now().astimezone().isoformat(),
            "dataset_path": project_relative_path(SOURCE_PATH),
            "labels_path": project_relative_path(LABELS_PATH),
            "export_path": project_relative_path(EXPORT_PATH),
            "event_mapping_version": event_mapping_version,
            "stakes": EVALUATION_STAKES,
            "decay_gap_days": DECAY_GAP_DAYS,
            "label_count": len(results),
            "source_scripts": [
                project_relative_path(
                    SCRIPT_DIR / "evaluate_support_labels_calibration.py"
                ),
                project_relative_path(
                    SCRIPT_DIR / "evaluate_support_labels_calibration_ablation.py"
                ),
            ],
        },
        "parameter_grid": {
            "grid_size": len(sweep_settings),
            "confidence_boost_caps": [
                value for _, value in CONFIDENCE_BOOST_CAP_LEVELS
            ],
            "unknownness_reduction_caps": [
                value for _, value in UNKNOWNNESS_REDUCTION_CAP_LEVELS
            ],
            "sweep_settings": [
                {
                    "setting_name": setting.setting_name,
                    "confidence_level": setting.confidence_level,
                    "unknownness_level": setting.unknownness_level,
                    "confidence_boost_cap": setting.confidence_boost_cap,
                    "unknownness_reduction_cap": setting.unknownness_reduction_cap,
                }
                for setting in sweep_settings
            ],
            "unchanged_eligibility_gate": {
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
                "unknownness_reduction_factor": UNKNOWNNESS_REDUCTION_FACTOR,
                "current_winning_confidence_boost_cap": CONFIDENCE_BOOST_CAP,
                "current_winning_unknownness_reduction_cap": (
                    UNKNOWNNESS_REDUCTION_CAP
                ),
            },
        },
        "baseline_reference": {
            "original_iml": {
                **original_iml_summary,
                "route_changes": 0,
            }
        },
        "per_setting_aggregate_results": aggregate_results,
        "changed_label_summaries_per_setting": changed_label_summaries,
        "best_settings_summary": build_best_settings_summary(
            aggregate_results,
            sweep_settings,
        ),
    }


def export_results(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with EXPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return EXPORT_PATH


def print_comparison_table(
    aggregate_results: list[dict[str, Any]],
) -> None:
    print("parameter_sweep_comparison:")
    print(
        "setting | conf_cap | unknown_cap | correct | incorrect | accuracy | route_changes"
    )

    for result in aggregate_results:
        print(
            " | ".join(
                [
                    str(result["setting_name"]),
                    format_float(float(result["confidence_boost_cap"])),
                    format_float(float(result["unknownness_reduction_cap"])),
                    str(result["correct_predictions"]),
                    str(result["incorrect_predictions"]),
                    format_percent(float(result["accuracy"])),
                    str(result["route_changes"]),
                ]
            )
        )


def print_best_settings_summary(best_settings_summary: dict[str, Any]) -> None:
    print()
    print("best_settings:")
    for result in best_settings_summary["best_settings"]:
        print(
            " | ".join(
                [
                    str(result["setting_name"]),
                    f"conf_cap={format_float(float(result['confidence_boost_cap']))}",
                    (
                        "unknown_cap="
                        f"{format_float(float(result['unknownness_reduction_cap']))}"
                    ),
                    f"accuracy={format_percent(float(result['accuracy']))}",
                    f"route_changes={result['route_changes']}",
                ]
            )
        )

    print()
    print(
        "winning_behavior_stability: "
        f"{best_settings_summary['winning_behavior_stability']['summary']}"
    )


def print_changed_label_summary(
    changed_label_summaries: list[dict[str, Any]],
) -> None:
    print()
    print("changed_labels_by_setting:")

    for setting_summary in changed_label_summaries:
        changed_labels = setting_summary["changed_labels"]
        if not changed_labels:
            print(f"{setting_summary['setting_name']}: none")
            continue

        label_summary = ", ".join(
            [
                (
                    f"{item['label_id']}({item['ticket_id']}: "
                    f"{item['original_path']}->{item['swept_path']})"
                )
                for item in changed_labels
            ]
        )
        print(f"{setting_summary['setting_name']}: {label_summary}")


def main() -> None:
    cases = load_support_cases(SOURCE_PATH)
    labels = load_support_labels(LABELS_PATH)
    entity_events, event_mapping_version = build_entity_events(cases)
    cases_by_ticket_id = {case.case_id: case for case in cases}
    sweep_settings = build_sweep_settings()

    print("support_v1 label calibration sweep")
    print(f"dataset: {project_relative_path(SOURCE_PATH)}")
    print(f"labels: {project_relative_path(LABELS_PATH)}")
    print(f"artifact: {project_relative_path(EXPORT_PATH)}")
    print(f"calibration_name: {CALIBRATION_NAME}")
    print()

    results: list[SweepLabelResult] = []
    for label in labels:
        validate_label(label, cases_by_ticket_id, entity_events)
        results.append(run_sweep_for_label(label, entity_events, sweep_settings))

    aggregate_results = build_setting_aggregate_results(results, sweep_settings)
    changed_label_summaries = build_changed_label_summaries(results, sweep_settings)
    best_settings_summary = build_best_settings_summary(
        aggregate_results,
        sweep_settings,
    )

    print_comparison_table(aggregate_results)
    print_best_settings_summary(best_settings_summary)
    print_changed_label_summary(changed_label_summaries)

    export_payload = build_export_payload(
        results,
        sweep_settings,
        event_mapping_version,
    )
    export_path = export_results(export_payload)

    print()
    print(f"evaluation_export: {project_relative_path(export_path)}")


if __name__ == "__main__":
    main()
