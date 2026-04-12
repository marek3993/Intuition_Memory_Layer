from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from iml.baselines import run_full_history_baseline, run_naive_summary_baseline
from iml.decay import apply_decay
from iml.decision import DecisionContext, route_decision
from iml.metrics import (
    RECOVERY_SCENARIOS,
    EntityEvaluationSummary,
    MethodAggregateMetrics,
    MethodEvaluationSummary,
    TrajectoryPoint,
    contradiction_peak,
    is_false_first_impression_recovered,
    recovery_event_index,
    summarize_method_comparison,
    summarize_metrics,
    trust_trajectory_span,
)
from iml.models import Event, IntuitionProfile
from iml.revalidate import revalidate_profile
from iml.update_engine import apply_event

DATASET_PATH = Path(__file__).parent / "datasets" / "synthetic_entities.json"
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
EVALUATION_EXPORT_PATH = ARTIFACTS_DIR / "latest_evaluation.json"
DECAY_GAP_DAYS = 21
FIRST_IMPRESSION_EVENT_COUNT = 3
FINAL_DECISION_GAP_DAYS = 7
EVALUATION_STAKES = "low"
EXPECTATION_HIGH_FINAL_TRUST_THRESHOLD = 0.80
EXPECTATION_CONTRADICTION_THRESHOLD = 0.35
EXPECTATION_UNKNOWNNESS_THRESHOLD = 0.45
EXPECTATION_FRESHNESS_THRESHOLD = 0.60

SCENARIO_EXPECTATIONS: dict[str, tuple[str, ...]] = {
    "stable_good_actor": (
        "high_final_trust",
        "low_contradiction_peak",
    ),
    "false_positive_first_impression": (
        "recover_by_end",
        "route_to_deep_path",
    ),
    "false_negative_first_impression": ("recover_by_end",),
    "high_contradiction_actor": (
        "high_contradiction_peak",
        "route_to_deep_path",
    ),
    "sparse_data_actor": (
        "high_unknownness_or_low_freshness",
        "route_to_deep_path",
    ),
}


@dataclass(frozen=True)
class BaselineEvaluationResult:
    selected_path: str
    overall_confidence: float
    unknownness: float
    decision_reason: str


@dataclass(frozen=True)
class EntityTrajectoryMetrics:
    recovery_event_index: int | None
    trust_trajectory_span: float
    contradiction_peak: float


@dataclass(frozen=True)
class ScenarioExpectationEvaluation:
    expected: tuple[str, ...]
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    all_expectations_passed: bool


@dataclass(frozen=True)
class ExpectationAggregateSummary:
    entities_with_all_expectations_passed: int
    entities_with_failed_expectations: int


@dataclass(frozen=True)
class EntityEvaluationResult:
    summary: EntityEvaluationSummary
    event_count: int
    decay_checkpoint_count: int
    first_impression_event_index: int
    final_decision_gap_days: int
    freshness: float
    contradiction_load: float
    revalidation_triggered: bool
    revalidation_reasons: tuple[str, ...]
    decision_reason: str
    trajectory: tuple[TrajectoryPoint, ...]
    trajectory_metrics: EntityTrajectoryMetrics
    expectation_evaluation: ScenarioExpectationEvaluation
    naive_summary: BaselineEvaluationResult
    full_history: BaselineEvaluationResult


def print_block(text: str) -> None:
    print()
    print(text)


def format_float(value: float) -> str:
    return f"{value:.2f}"


def format_items(values: tuple[str, ...] | list[str]) -> str:
    return ", ".join(values) if values else "none"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        entities = payload.get("entities")
        if not isinstance(entities, list):
            raise ValueError("Synthetic dataset object must contain an 'entities' list.")
        return entities

    if not isinstance(payload, list):
        raise ValueError("Synthetic dataset must be a JSON list of entities.")

    return payload


def parse_timestamp(raw_timestamp: str) -> datetime:
    return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))


def build_event(raw_event: dict[str, Any]) -> Event:
    return Event(
        event_id=raw_event["event_id"],
        entity_id=raw_event["entity_id"],
        timestamp=parse_timestamp(raw_event["timestamp"]),
        event_type=raw_event["event_type"],
        source=raw_event["source"],
        reliability=raw_event["reliability"],
        polarity=raw_event["polarity"],
        intensity=raw_event["intensity"],
        metadata=raw_event.get("metadata", {}),
    )


def make_profile(entity_id: str, start_time: datetime) -> IntuitionProfile:
    profile = IntuitionProfile.new(entity_id)
    profile.created_at = start_time
    profile.updated_at = start_time
    profile.last_revalidated_at = start_time

    for attribute_state in profile.attributes.values():
        attribute_state.last_changed_at = start_time

    return profile


def maybe_apply_gap_decay(profile: IntuitionProfile, next_timestamp: datetime) -> bool:
    elapsed_days = (next_timestamp - profile.updated_at).total_seconds() / 86_400
    if elapsed_days < DECAY_GAP_DAYS:
        return False

    apply_decay(profile, now=next_timestamp)
    return True


def capture_trajectory_point(
    event_index: int,
    event: Event,
    profile: IntuitionProfile,
) -> TrajectoryPoint:
    return TrajectoryPoint(
        event_index=event_index,
        event_id=event.event_id,
        event_type=event.event_type,
        timestamp=event.timestamp.isoformat(),
        trust=profile.attributes["trust"].value,
        overall_confidence=profile.overall_confidence,
        unknownness=profile.unknownness,
        freshness=profile.freshness,
        contradiction_load=profile.contradiction_load,
    )


def evaluate_expectation(expectation: str, result: EntityEvaluationResult) -> bool:
    if expectation == "high_final_trust":
        return result.summary.final_trust >= EXPECTATION_HIGH_FINAL_TRUST_THRESHOLD

    if expectation == "low_contradiction_peak":
        return (
            result.trajectory_metrics.contradiction_peak
            <= EXPECTATION_CONTRADICTION_THRESHOLD
        )

    if expectation == "recover_by_end":
        return is_false_first_impression_recovered(result.summary)

    if expectation == "route_to_deep_path":
        return result.summary.selected_path == "deep_path"

    if expectation == "high_contradiction_peak":
        return (
            result.trajectory_metrics.contradiction_peak
            > EXPECTATION_CONTRADICTION_THRESHOLD
        )

    if expectation == "high_unknownness_or_low_freshness":
        return (
            result.summary.unknownness > EXPECTATION_UNKNOWNNESS_THRESHOLD
            or result.freshness < EXPECTATION_FRESHNESS_THRESHOLD
        )

    raise ValueError(f"Unknown expectation: {expectation}")


def evaluate_scenario_expectations(
    result: EntityEvaluationResult,
) -> ScenarioExpectationEvaluation:
    expected = SCENARIO_EXPECTATIONS.get(result.summary.scenario)
    if expected is None:
        raise ValueError(
            f"No scenario expectations configured for scenario: {result.summary.scenario}"
        )

    passed = tuple(
        expectation for expectation in expected if evaluate_expectation(expectation, result)
    )
    failed = tuple(
        expectation for expectation in expected if expectation not in passed
    )
    return ScenarioExpectationEvaluation(
        expected=expected,
        passed=passed,
        failed=failed,
        all_expectations_passed=not failed,
    )


def replay_entity(entity_record: dict[str, Any]) -> EntityEvaluationResult:
    raw_events = entity_record["events"]
    events = sorted(
        (build_event(raw_event) for raw_event in raw_events),
        key=lambda event: event.timestamp,
    )
    if not events:
        raise ValueError(f"Entity {entity_record['entity_id']} has no events.")

    naive_summary_result = run_naive_summary_baseline(events)
    full_history_result = run_full_history_baseline(events)
    profile = make_profile(entity_record["entity_id"], events[0].timestamp)
    first_impression_trust = profile.attributes["trust"].value
    first_impression_event_index = min(FIRST_IMPRESSION_EVENT_COUNT, len(events))
    decay_checkpoint_count = 0
    trajectory: list[TrajectoryPoint] = []

    for index, event in enumerate(events, start=1):
        if maybe_apply_gap_decay(profile, event.timestamp):
            decay_checkpoint_count += 1

        apply_event(profile, event)
        trajectory.append(capture_trajectory_point(index, event, profile))

        if index == first_impression_event_index:
            first_impression_trust = profile.attributes["trust"].value

    trajectory_metrics = EntityTrajectoryMetrics(
        recovery_event_index=recovery_event_index(
            entity_record["scenario"],
            trajectory,
            first_impression_event_index=first_impression_event_index,
        ),
        trust_trajectory_span=trust_trajectory_span(trajectory),
        contradiction_peak=contradiction_peak(trajectory),
    )

    decision_time = profile.updated_at + timedelta(days=FINAL_DECISION_GAP_DAYS)
    apply_decay(profile, now=decision_time)
    revalidation_result = revalidate_profile(profile, now=decision_time)
    decision_result = route_decision(profile, DecisionContext(stakes=EVALUATION_STAKES))
    summary = EntityEvaluationSummary(
        entity_id=entity_record["entity_id"],
        scenario=entity_record["scenario"],
        selected_path=decision_result.selected_path,
        overall_confidence=profile.overall_confidence,
        unknownness=profile.unknownness,
        first_impression_trust=first_impression_trust,
        final_trust=profile.attributes["trust"].value,
    )

    placeholder_expectations = ScenarioExpectationEvaluation(
        expected=(),
        passed=(),
        failed=(),
        all_expectations_passed=True,
    )
    result = EntityEvaluationResult(
        summary=summary,
        event_count=len(events),
        decay_checkpoint_count=decay_checkpoint_count,
        first_impression_event_index=first_impression_event_index,
        final_decision_gap_days=FINAL_DECISION_GAP_DAYS,
        freshness=profile.freshness,
        contradiction_load=profile.contradiction_load,
        revalidation_triggered=revalidation_result.triggered,
        revalidation_reasons=tuple(revalidation_result.reasons),
        decision_reason=decision_result.reason,
        trajectory=tuple(trajectory),
        trajectory_metrics=trajectory_metrics,
        expectation_evaluation=placeholder_expectations,
        naive_summary=BaselineEvaluationResult(
            selected_path=str(naive_summary_result["selected_path"]),
            overall_confidence=float(naive_summary_result["overall_confidence"]),
            unknownness=float(naive_summary_result["unknownness"]),
            decision_reason=str(naive_summary_result["decision_reason"]),
        ),
        full_history=BaselineEvaluationResult(
            selected_path=str(full_history_result["selected_path"]),
            overall_confidence=float(full_history_result["overall_confidence"]),
            unknownness=float(full_history_result["unknownness"]),
            decision_reason=str(full_history_result["decision_reason"]),
        ),
    )
    return replace(
        result,
        expectation_evaluation=evaluate_scenario_expectations(result),
    )


def print_entity_summary(result: EntityEvaluationResult) -> None:
    reasons = format_items(result.revalidation_reasons)
    trajectory_metrics_parts = [
        f"contradiction_peak={format_float(result.trajectory_metrics.contradiction_peak)}",
        (
            "trust_trajectory_span="
            f"{format_float(result.trajectory_metrics.trust_trajectory_span)}"
        ),
    ]
    if result.summary.scenario in RECOVERY_SCENARIOS:
        recovery_value = result.trajectory_metrics.recovery_event_index
        trajectory_metrics_parts.insert(
            0,
            f"recovery_event_index={recovery_value if recovery_value is not None else 'none'}",
        )

    lines = [
        f"=== Entity Summary: {result.summary.entity_id} ===",
        f"scenario: {result.summary.scenario}",
        f"event_count: {result.event_count}",
        f"decay_checkpoints: {result.decay_checkpoint_count}",
        f"final_decision_gap_days: {result.final_decision_gap_days}",
        f"first_impression_trust: {format_float(result.summary.first_impression_trust)}",
        f"final_trust: {format_float(result.summary.final_trust)}",
        f"overall_confidence: {format_float(result.summary.overall_confidence)}",
        f"unknownness: {format_float(result.summary.unknownness)}",
        f"freshness: {format_float(result.freshness)}",
        f"contradiction_load: {format_float(result.contradiction_load)}",
        f"trajectory_metrics: {', '.join(trajectory_metrics_parts)}",
        f"passed_expectations: {format_items(result.expectation_evaluation.passed)}",
        f"failed_expectations: {format_items(result.expectation_evaluation.failed)}",
        (
            "all_expectations_passed: "
            f"{result.expectation_evaluation.all_expectations_passed}"
        ),
        f"revalidation_triggered: {result.revalidation_triggered}",
        f"revalidation_reasons: {reasons}",
        f"iml_selected_path: {result.summary.selected_path}",
        f"naive_summary_selected_path: {result.naive_summary.selected_path}",
        f"naive_summary_decision_reason: {result.naive_summary.decision_reason}",
        f"full_history_selected_path: {result.full_history.selected_path}",
        f"full_history_decision_reason: {result.full_history.decision_reason}",
        f"iml_decision_reason: {result.decision_reason}",
    ]
    print_block("\n".join(lines))


def summarize_expectation_results(
    results: list[EntityEvaluationResult],
) -> ExpectationAggregateSummary:
    passed_count = sum(
        1 for result in results if result.expectation_evaluation.all_expectations_passed
    )
    return ExpectationAggregateSummary(
        entities_with_all_expectations_passed=passed_count,
        entities_with_failed_expectations=len(results) - passed_count,
    )


def print_aggregate_summary(results: list[EntityEvaluationResult]) -> None:
    aggregate = summarize_metrics([result.summary for result in results])
    lines = [
        "=== Aggregate Metrics ===",
        f"entities_evaluated: {len(results)}",
        f"total_events_replayed: {sum(result.event_count for result in results)}",
        f"decay_checkpoints_applied: {sum(result.decay_checkpoint_count for result in results)}",
        f"revalidations_triggered: {sum(1 for result in results if result.revalidation_triggered)}",
        f"fast_path_count: {aggregate.fast_path_count}",
        f"deep_path_count: {aggregate.deep_path_count}",
        f"average_overall_confidence: {format_float(aggregate.average_overall_confidence)}",
        f"average_unknownness: {format_float(aggregate.average_unknownness)}",
        (
            "false_first_impression_recovery_proxy: "
            f"{format_float(aggregate.false_first_impression_recovery_proxy)}"
        ),
    ]
    print_block("\n".join(lines))


def print_expectation_summary(results: list[EntityEvaluationResult]) -> None:
    aggregate = summarize_expectation_results(results)
    lines = [
        "=== Scenario Expectations v1 ===",
        (
            "entities_with_all_expectations_passed: "
            f"{aggregate.entities_with_all_expectations_passed}"
        ),
        f"entities_with_failed_expectations: {aggregate.entities_with_failed_expectations}",
    ]
    print_block("\n".join(lines))


def summarize_method_results(results: list[EntityEvaluationResult]) -> list[MethodAggregateMetrics]:
    return summarize_method_comparison(
        iml_summaries=[
            MethodEvaluationSummary(
                method="IML",
                selected_path=result.summary.selected_path,
                overall_confidence=result.summary.overall_confidence,
                unknownness=result.summary.unknownness,
            )
            for result in results
        ],
        naive_summary_summaries=[
            MethodEvaluationSummary(
                method="naive_summary",
                selected_path=result.naive_summary.selected_path,
                overall_confidence=result.naive_summary.overall_confidence,
                unknownness=result.naive_summary.unknownness,
            )
            for result in results
        ],
        full_history_summaries=[
            MethodEvaluationSummary(
                method="full_history",
                selected_path=result.full_history.selected_path,
                overall_confidence=result.full_history.overall_confidence,
                unknownness=result.full_history.unknownness,
            )
            for result in results
        ],
    )


def print_comparison_summary(results: list[EntityEvaluationResult]) -> None:
    comparison = summarize_method_results(results)
    lines = ["=== Baseline Comparison v2 ==="]
    for method_metrics in comparison:
        lines.append(
            (
                f"{method_metrics.method}: "
                f"fast_path_count={method_metrics.fast_path_count}, "
                f"deep_path_count={method_metrics.deep_path_count}, "
                "average_overall_confidence="
                f"{format_float(method_metrics.average_overall_confidence)}, "
                f"average_unknownness={format_float(method_metrics.average_unknownness)}"
            )
        )

    print_block("\n".join(lines))


def print_per_scenario_comparison(results: list[EntityEvaluationResult]) -> None:
    results_by_scenario: dict[str, list[EntityEvaluationResult]] = {}
    for result in results:
        results_by_scenario.setdefault(result.summary.scenario, []).append(result)

    lines = ["=== Per-Scenario Comparison ==="]
    for scenario in sorted(results_by_scenario):
        lines.append(f"scenario: {scenario}")
        for result in results_by_scenario[scenario]:
            lines.append(
                (
                    f"  {result.summary.entity_id}: "
                    f"IML={result.summary.selected_path}, "
                    f"naive_summary={result.naive_summary.selected_path}, "
                    f"full_history={result.full_history.selected_path}"
                )
            )

    print_block("\n".join(lines))


def build_entity_summary_payload(result: EntityEvaluationResult) -> dict[str, Any]:
    return {
        "entity_id": result.summary.entity_id,
        "scenario": result.summary.scenario,
        "event_count": result.event_count,
        "decay_checkpoint_count": result.decay_checkpoint_count,
        "first_impression_event_index": result.first_impression_event_index,
        "final_decision_gap_days": result.final_decision_gap_days,
        "first_impression_trust": result.summary.first_impression_trust,
        "final_trust": result.summary.final_trust,
        "overall_confidence": result.summary.overall_confidence,
        "unknownness": result.summary.unknownness,
        "freshness": result.freshness,
        "contradiction_load": result.contradiction_load,
        "revalidation_triggered": result.revalidation_triggered,
        "revalidation_reasons": list(result.revalidation_reasons),
        "scenario_expectations": {
            "version": "v1",
            "expected": list(result.expectation_evaluation.expected),
            "passed": list(result.expectation_evaluation.passed),
            "failed": list(result.expectation_evaluation.failed),
            "all_expectations_passed": (
                result.expectation_evaluation.all_expectations_passed
            ),
        },
        "iml": {
            "selected_path": result.summary.selected_path,
            "decision_reason": result.decision_reason,
        },
        "naive_summary": asdict(result.naive_summary),
        "full_history": asdict(result.full_history),
    }


def build_trajectory_metrics_payload(result: EntityEvaluationResult) -> dict[str, Any]:
    return {
        "entity_id": result.summary.entity_id,
        "scenario": result.summary.scenario,
        "first_impression_event_index": result.first_impression_event_index,
        "recovery_event_index": result.trajectory_metrics.recovery_event_index,
        "trust_trajectory_span": result.trajectory_metrics.trust_trajectory_span,
        "contradiction_peak": result.trajectory_metrics.contradiction_peak,
    }


def build_aggregate_payload(results: list[EntityEvaluationResult]) -> dict[str, Any]:
    aggregate = summarize_metrics([result.summary for result in results])
    expectation_aggregate = summarize_expectation_results(results)
    return {
        "entities_evaluated": len(results),
        "total_events_replayed": sum(result.event_count for result in results),
        "decay_checkpoints_applied": sum(
            result.decay_checkpoint_count for result in results
        ),
        "revalidations_triggered": sum(
            1 for result in results if result.revalidation_triggered
        ),
        "fast_path_count": aggregate.fast_path_count,
        "deep_path_count": aggregate.deep_path_count,
        "average_overall_confidence": aggregate.average_overall_confidence,
        "average_unknownness": aggregate.average_unknownness,
        "entities_with_all_expectations_passed": (
            expectation_aggregate.entities_with_all_expectations_passed
        ),
        "entities_with_failed_expectations": (
            expectation_aggregate.entities_with_failed_expectations
        ),
        "false_first_impression_recovery_proxy": (
            aggregate.false_first_impression_recovery_proxy
        ),
    }


def build_trajectory_metrics_export(results: list[EntityEvaluationResult]) -> dict[str, Any]:
    per_entity_metrics = [build_trajectory_metrics_payload(result) for result in results]
    recovery_values = [
        metrics["recovery_event_index"]
        for metrics in per_entity_metrics
        if metrics["recovery_event_index"] is not None
    ]

    return {
        "aggregate": {
            "average_trust_trajectory_span": average_value(
                [result.trajectory_metrics.trust_trajectory_span for result in results]
            ),
            "average_contradiction_peak": average_value(
                [result.trajectory_metrics.contradiction_peak for result in results]
            ),
            "recoverable_entity_count": sum(
                1 for result in results if result.summary.scenario in RECOVERY_SCENARIOS
            ),
            "recovered_entity_count": len(recovery_values),
            "average_recovery_event_index": average_value(recovery_values),
        },
        "per_entity": per_entity_metrics,
    }


def build_export_payload(results: list[EntityEvaluationResult]) -> dict[str, Any]:
    return {
        "run_metadata": {
            "generated_at": datetime.now().astimezone().isoformat(),
            "dataset_path": str(DATASET_PATH),
            "export_path": str(EVALUATION_EXPORT_PATH),
            "scenario_expectations_version": "v1",
            "stakes": EVALUATION_STAKES,
            "decay_gap_days": DECAY_GAP_DAYS,
            "first_impression_event_count": FIRST_IMPRESSION_EVENT_COUNT,
            "final_decision_gap_days": FINAL_DECISION_GAP_DAYS,
        },
        "aggregate_metrics": build_aggregate_payload(results),
        "baseline_comparison": [
            asdict(method_metrics) for method_metrics in summarize_method_results(results)
        ],
        "entity_summaries": [build_entity_summary_payload(result) for result in results],
        "entity_trajectories": [
            {
                "entity_id": result.summary.entity_id,
                "scenario": result.summary.scenario,
                "trajectory": [asdict(point) for point in result.trajectory],
            }
            for result in results
        ],
        "trajectory_metrics": build_trajectory_metrics_export(results),
    }


def export_evaluation(results: list[EntityEvaluationResult]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_export_payload(results)
    with EVALUATION_EXPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return EVALUATION_EXPORT_PATH


def average_value(values: list[int | float]) -> float | None:
    if not values:
        return None

    return sum(values) / len(values)


def main() -> None:
    dataset = load_dataset(DATASET_PATH)
    results: list[EntityEvaluationResult] = []

    print("Intuition Memory Layer synthetic evaluation")
    print(f"dataset: {DATASET_PATH}")
    print(f"stakes: {EVALUATION_STAKES}")
    print(f"decay_gap_days: {DECAY_GAP_DAYS}")
    print(f"final_decision_gap_days: {FINAL_DECISION_GAP_DAYS}")

    for entity_record in dataset:
        result = replay_entity(entity_record)
        results.append(result)
        print_entity_summary(result)

    print_aggregate_summary(results)
    print_expectation_summary(results)
    print_comparison_summary(results)
    print_per_scenario_comparison(results)
    export_path = export_evaluation(results)
    print()
    print(f"evaluation_export: {export_path}")


if __name__ == "__main__":
    main()
