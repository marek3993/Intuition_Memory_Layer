from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from iml.baselines import run_full_history_baseline, run_naive_summary_baseline
from iml.decay import apply_decay
from iml.decision import DecisionContext, route_decision
from iml.metrics import (
    EntityEvaluationSummary,
    MethodEvaluationSummary,
    summarize_method_comparison,
    summarize_metrics,
)
from iml.models import Event, IntuitionProfile
from iml.revalidate import revalidate_profile
from iml.update_engine import apply_event

DATASET_PATH = Path(__file__).parent / "datasets" / "synthetic_entities.json"
DECAY_GAP_DAYS = 21
FIRST_IMPRESSION_EVENT_COUNT = 3
FINAL_DECISION_GAP_DAYS = 7
EVALUATION_STAKES = "low"


@dataclass(frozen=True)
class BaselineEvaluationResult:
    selected_path: str
    overall_confidence: float
    unknownness: float
    decision_reason: str


@dataclass(frozen=True)
class EntityEvaluationResult:
    summary: EntityEvaluationSummary
    event_count: int
    decay_checkpoint_count: int
    final_decision_gap_days: int
    freshness: float
    contradiction_load: float
    revalidation_triggered: bool
    revalidation_reasons: tuple[str, ...]
    decision_reason: str
    naive_summary: BaselineEvaluationResult
    full_history: BaselineEvaluationResult


def print_block(text: str) -> None:
    print()
    print(text)


def format_float(value: float) -> str:
    return f"{value:.2f}"


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
    first_impression_index = min(FIRST_IMPRESSION_EVENT_COUNT, len(events))
    decay_checkpoint_count = 0

    for index, event in enumerate(events, start=1):
        if maybe_apply_gap_decay(profile, event.timestamp):
            decay_checkpoint_count += 1

        apply_event(profile, event)

        if index == first_impression_index:
            first_impression_trust = profile.attributes["trust"].value

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

    return EntityEvaluationResult(
        summary=summary,
        event_count=len(events),
        decay_checkpoint_count=decay_checkpoint_count,
        final_decision_gap_days=FINAL_DECISION_GAP_DAYS,
        freshness=profile.freshness,
        contradiction_load=profile.contradiction_load,
        revalidation_triggered=revalidation_result.triggered,
        revalidation_reasons=tuple(revalidation_result.reasons),
        decision_reason=decision_result.reason,
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


def print_entity_summary(result: EntityEvaluationResult) -> None:
    reasons = ", ".join(result.revalidation_reasons) if result.revalidation_reasons else "none"
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


def print_comparison_summary(results: list[EntityEvaluationResult]) -> None:
    comparison = summarize_method_comparison(
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
    print_comparison_summary(results)
    print_per_scenario_comparison(results)


if __name__ == "__main__":
    main()
