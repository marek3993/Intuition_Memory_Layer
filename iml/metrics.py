from __future__ import annotations

from dataclasses import dataclass


TRUST_MIDPOINT = 0.50
RECOVERY_SCENARIOS = {
    "false_positive_first_impression",
    "false_negative_first_impression",
}


@dataclass(frozen=True)
class EntityEvaluationSummary:
    entity_id: str
    scenario: str
    selected_path: str
    overall_confidence: float
    unknownness: float
    first_impression_trust: float
    final_trust: float


@dataclass(frozen=True)
class AggregateMetrics:
    fast_path_count: int
    deep_path_count: int
    average_overall_confidence: float
    average_unknownness: float
    false_first_impression_recovery_proxy: float


@dataclass(frozen=True)
class TrajectoryPoint:
    event_index: int
    event_id: str
    event_type: str
    timestamp: str
    trust: float
    overall_confidence: float
    unknownness: float
    freshness: float
    contradiction_load: float


@dataclass(frozen=True)
class MethodEvaluationSummary:
    method: str
    selected_path: str
    overall_confidence: float
    unknownness: float


@dataclass(frozen=True)
class MethodAggregateMetrics:
    method: str
    fast_path_count: int
    deep_path_count: int
    average_overall_confidence: float
    average_unknownness: float


@dataclass(frozen=True)
class EvaluationRecord:
    entity_id: str
    scenario: str
    selected_path: str
    overall_confidence: float
    unknownness: float
    initial_trust: float
    final_trust: float


def _as_summary(
    summary_or_record: EntityEvaluationSummary | EvaluationRecord,
) -> EntityEvaluationSummary:
    if isinstance(summary_or_record, EntityEvaluationSummary):
        return summary_or_record

    return EntityEvaluationSummary(
        entity_id=summary_or_record.entity_id,
        scenario=summary_or_record.scenario,
        selected_path=summary_or_record.selected_path,
        overall_confidence=summary_or_record.overall_confidence,
        unknownness=summary_or_record.unknownness,
        first_impression_trust=summary_or_record.initial_trust,
        final_trust=summary_or_record.final_trust,
    )


def fast_path_count(entity_summaries: list[EntityEvaluationSummary]) -> int:
    return sum(1 for summary in entity_summaries if summary.selected_path == "fast_path")


def deep_path_count(entity_summaries: list[EntityEvaluationSummary]) -> int:
    return sum(1 for summary in entity_summaries if summary.selected_path == "deep_path")


def average_overall_confidence(entity_summaries: list[EntityEvaluationSummary]) -> float:
    if not entity_summaries:
        return 0.0

    total = sum(summary.overall_confidence for summary in entity_summaries)
    return total / len(entity_summaries)


def average_unknownness(entity_summaries: list[EntityEvaluationSummary]) -> float:
    if not entity_summaries:
        return 0.0

    total = sum(summary.unknownness for summary in entity_summaries)
    return total / len(entity_summaries)


def is_false_first_impression_recovered(
    summary_or_record: EntityEvaluationSummary | EvaluationRecord,
) -> bool:
    summary = _as_summary(summary_or_record)

    if summary.scenario == "false_positive_first_impression":
        return (
            summary.first_impression_trust > TRUST_MIDPOINT
            and summary.final_trust < TRUST_MIDPOINT
        )

    if summary.scenario == "false_negative_first_impression":
        return (
            summary.first_impression_trust < TRUST_MIDPOINT
            and summary.final_trust > TRUST_MIDPOINT
        )

    return False


def false_first_impression_recovery_proxy(
    entity_summaries: list[EntityEvaluationSummary],
) -> float:
    relevant_summaries = [
        summary for summary in entity_summaries if summary.scenario in RECOVERY_SCENARIOS
    ]
    if not relevant_summaries:
        return 0.0

    recovered_count = sum(
        1 for summary in relevant_summaries if is_false_first_impression_recovered(summary)
    )
    return recovered_count / len(relevant_summaries)


def recovery_event_index(
    scenario: str,
    trajectory: list[TrajectoryPoint],
    *,
    first_impression_event_index: int,
) -> int | None:
    if scenario == "false_positive_first_impression":
        for point in trajectory:
            if point.event_index <= first_impression_event_index:
                continue
            if point.trust < TRUST_MIDPOINT:
                return point.event_index
        return None

    if scenario == "false_negative_first_impression":
        for point in trajectory:
            if point.event_index <= first_impression_event_index:
                continue
            if point.trust > TRUST_MIDPOINT:
                return point.event_index
        return None

    return None


def trust_trajectory_span(trajectory: list[TrajectoryPoint]) -> float:
    if not trajectory:
        return 0.0

    trust_values = [point.trust for point in trajectory]
    return max(trust_values) - min(trust_values)


def contradiction_peak(trajectory: list[TrajectoryPoint]) -> float:
    if not trajectory:
        return 0.0

    return max(point.contradiction_load for point in trajectory)


def summarize_metrics(entity_summaries: list[EntityEvaluationSummary]) -> AggregateMetrics:
    return AggregateMetrics(
        fast_path_count=fast_path_count(entity_summaries),
        deep_path_count=deep_path_count(entity_summaries),
        average_overall_confidence=average_overall_confidence(entity_summaries),
        average_unknownness=average_unknownness(entity_summaries),
        false_first_impression_recovery_proxy=false_first_impression_recovery_proxy(
            entity_summaries
        ),
    )


def summarize_method_metrics(
    method: str,
    method_summaries: list[MethodEvaluationSummary],
) -> MethodAggregateMetrics:
    return MethodAggregateMetrics(
        method=method,
        fast_path_count=sum(
            1 for summary in method_summaries if summary.selected_path == "fast_path"
        ),
        deep_path_count=sum(
            1 for summary in method_summaries if summary.selected_path == "deep_path"
        ),
        average_overall_confidence=_average_method_confidence(method_summaries),
        average_unknownness=_average_method_unknownness(method_summaries),
    )


def summarize_method_comparison(
    *,
    iml_summaries: list[MethodEvaluationSummary],
    naive_summary_summaries: list[MethodEvaluationSummary],
    full_history_summaries: list[MethodEvaluationSummary],
) -> list[MethodAggregateMetrics]:
    return [
        summarize_method_metrics("IML", iml_summaries),
        summarize_method_metrics("naive_summary", naive_summary_summaries),
        summarize_method_metrics("full_history", full_history_summaries),
    ]


def summarize_records(records: list[EvaluationRecord]) -> dict[str, float | int]:
    aggregate = summarize_metrics([_as_summary(record) for record in records])
    return {
        "fast_path_selections": aggregate.fast_path_count,
        "deep_path_selections": aggregate.deep_path_count,
        "average_overall_confidence": aggregate.average_overall_confidence,
        "average_unknownness": aggregate.average_unknownness,
        "false_first_impression_recovery_proxy": aggregate.false_first_impression_recovery_proxy,
    }


def _average_method_confidence(method_summaries: list[MethodEvaluationSummary]) -> float:
    if not method_summaries:
        return 0.0

    total = sum(summary.overall_confidence for summary in method_summaries)
    return total / len(method_summaries)


def _average_method_unknownness(method_summaries: list[MethodEvaluationSummary]) -> float:
    if not method_summaries:
        return 0.0

    total = sum(summary.unknownness for summary in method_summaries)
    return total / len(method_summaries)
