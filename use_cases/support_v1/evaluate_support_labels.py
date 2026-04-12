from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
LABELS_PATH = SCRIPT_DIR / "sample_support_labels.json"
EXPORT_PATH = ARTIFACTS_DIR / "support_label_evaluation.json"
DECAY_GAP_DAYS = 21
EVALUATION_STAKES = "low"

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from convert_support_cases_to_events import (
    SOURCE_PATH,
    SupportCase,
    convert_cases_to_entity_event_payload,
    load_support_cases,
)
from iml.decay import apply_decay
from iml.decision import DecisionContext, route_decision
from iml.models import Event, IntuitionProfile
from iml.revalidate import revalidate_profile
from iml.update_engine import apply_event


@dataclass(frozen=True)
class SupportLabel:
    label_id: str
    entity_id: str
    ticket_id: str
    decision_timestamp: datetime
    should_route: str
    note: str
    contradiction_present: bool = False
    profile_too_stale: bool = False
    wrong_first_impression: bool = False


@dataclass(frozen=True)
class LabelEvaluationResult:
    label: SupportLabel
    predicted_path: str
    predicted_reason: str
    correct: bool
    visible_case_ids: tuple[str, ...]
    visible_event_count: int
    visible_event_type_counts: dict[str, int]
    decay_checkpoints: int
    trust: float
    cooperativeness: float
    predictability: float
    stability: float
    risk: float
    overall_confidence: float
    unknownness: float
    freshness: float
    contradiction_load: float
    revalidation_triggered: bool
    revalidation_reasons: tuple[str, ...]


def parse_timestamp(raw_timestamp: str) -> datetime:
    return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))


def project_relative_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def build_event(raw_event: dict[str, Any]) -> Event:
    return Event(
        event_id=str(raw_event["event_id"]),
        entity_id=str(raw_event["entity_id"]),
        timestamp=parse_timestamp(str(raw_event["timestamp"])),
        event_type=str(raw_event["event_type"]),
        source=str(raw_event["source"]),
        reliability=float(raw_event["reliability"]),
        polarity=float(raw_event["polarity"]),
        intensity=float(raw_event["intensity"]),
        metadata=dict(raw_event.get("metadata", {})),
    )


def build_events_by_entity_from_payload(
    payload: dict[str, Any],
) -> dict[str, list[Event]]:
    entity_events: dict[str, list[Event]] = {}

    for raw_entity in payload["entities"]:
        events = [build_event(raw_event) for raw_event in raw_entity["events"]]
        entity_events[str(raw_entity["entity_id"])] = sorted(
            events,
            key=lambda event: (event.timestamp, event.event_id),
        )

    return entity_events


def build_events_by_entity(cases: list[SupportCase]) -> dict[str, list[Event]]:
    payload = convert_cases_to_entity_event_payload(cases, SOURCE_PATH)
    return build_events_by_entity_from_payload(payload)


def load_support_labels(path: Path = LABELS_PATH) -> list[SupportLabel]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    raw_labels = payload.get("labels")
    if not isinstance(raw_labels, list):
        raise ValueError("Support label payload must contain a 'labels' list.")

    labels: list[SupportLabel] = []
    for raw_label in raw_labels:
        labels.append(
            SupportLabel(
                label_id=str(raw_label["label_id"]),
                entity_id=str(raw_label["entity_id"]),
                ticket_id=str(raw_label["ticket_id"]),
                decision_timestamp=parse_timestamp(str(raw_label["decision_timestamp"])),
                should_route=str(raw_label["should_route"]),
                note=str(raw_label["note"]),
                contradiction_present=bool(raw_label.get("contradiction_present", False)),
                profile_too_stale=bool(raw_label.get("profile_too_stale", False)),
                wrong_first_impression=bool(
                    raw_label.get("wrong_first_impression", False)
                ),
            )
        )

    return labels


def build_entity_events(cases: list[SupportCase]) -> tuple[dict[str, list[Event]], str]:
    payload = convert_cases_to_entity_event_payload(cases, SOURCE_PATH)
    entity_events = build_events_by_entity_from_payload(payload)
    event_mapping_version = str(payload["run_metadata"]["event_mapping_version"])
    return entity_events, event_mapping_version


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


def validate_label(
    label: SupportLabel,
    cases_by_ticket_id: dict[str, SupportCase],
    entity_events: dict[str, list[Event]],
) -> None:
    case = cases_by_ticket_id.get(label.ticket_id)
    if case is None:
        raise ValueError(f"Label {label.label_id} references unknown ticket {label.ticket_id}.")

    if case.entity_id != label.entity_id:
        raise ValueError(
            f"Label {label.label_id} has entity_id={label.entity_id}, "
            f"but ticket {label.ticket_id} belongs to {case.entity_id}."
        )

    if label.should_route not in {"fast_path", "deep_path"}:
        raise ValueError(
            f"Label {label.label_id} has invalid should_route={label.should_route}."
        )

    if not (case.opened_at <= label.decision_timestamp <= case.closed_at):
        raise ValueError(
            f"Label {label.label_id} has decision_timestamp outside the ticket window "
            f"for {label.ticket_id}."
        )

    if label.entity_id not in entity_events:
        raise ValueError(f"Label {label.label_id} references entity with no derived events.")

    visible_ticket_events = [
        event
        for event in entity_events[label.entity_id]
        if event.timestamp <= label.decision_timestamp
        and str(event.metadata.get("case_id", "")) == label.ticket_id
    ]
    if not visible_ticket_events:
        raise ValueError(
            f"Label {label.label_id} has decision_timestamp={label.decision_timestamp.isoformat()}, "
            f"but no visible events exist for entity {label.entity_id} and ticket {label.ticket_id} "
            "at or before that timestamp."
        )


def evaluate_label(
    label: SupportLabel,
    entity_events: dict[str, list[Event]],
) -> LabelEvaluationResult:
    visible_events = [
        event
        for event in entity_events[label.entity_id]
        if event.timestamp <= label.decision_timestamp
    ]
    profile_start_time = visible_events[0].timestamp if visible_events else label.decision_timestamp
    profile = make_profile(label.entity_id, profile_start_time)
    event_type_counts: Counter[str] = Counter()
    decay_checkpoints = 0

    for event in visible_events:
        if maybe_apply_gap_decay(profile, event.timestamp):
            decay_checkpoints += 1
        apply_event(profile, event)
        event_type_counts[event.event_type] += 1

    apply_decay(profile, now=label.decision_timestamp)
    revalidation_result = revalidate_profile(profile, now=label.decision_timestamp)
    decision_result = route_decision(profile, DecisionContext(stakes=EVALUATION_STAKES))

    visible_case_ids = tuple(
        sorted(
            {
                str(event.metadata["case_id"])
                for event in visible_events
                if "case_id" in event.metadata
            }
        )
    )

    return LabelEvaluationResult(
        label=label,
        predicted_path=decision_result.selected_path,
        predicted_reason=decision_result.reason,
        correct=decision_result.selected_path == label.should_route,
        visible_case_ids=visible_case_ids,
        visible_event_count=len(visible_events),
        visible_event_type_counts=dict(sorted(event_type_counts.items())),
        decay_checkpoints=decay_checkpoints,
        trust=profile.attributes["trust"].value,
        cooperativeness=profile.attributes["cooperativeness"].value,
        predictability=profile.attributes["predictability"].value,
        stability=profile.attributes["stability"].value,
        risk=profile.attributes["risk"].value,
        overall_confidence=profile.overall_confidence,
        unknownness=profile.unknownness,
        freshness=profile.freshness,
        contradiction_load=profile.contradiction_load,
        revalidation_triggered=revalidation_result.triggered,
        revalidation_reasons=tuple(revalidation_result.reasons),
    )


def format_float(value: float) -> str:
    return f"{value:.2f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def build_result_payload(result: LabelEvaluationResult) -> dict[str, Any]:
    return {
        "label": {
            "label_id": result.label.label_id,
            "entity_id": result.label.entity_id,
            "ticket_id": result.label.ticket_id,
            "decision_timestamp": result.label.decision_timestamp.isoformat(),
            "should_route": result.label.should_route,
            "note": result.label.note,
            "contradiction_present": result.label.contradiction_present,
            "profile_too_stale": result.label.profile_too_stale,
            "wrong_first_impression": result.label.wrong_first_impression,
        },
        "prediction": {
            "predicted_path": result.predicted_path,
            "predicted_reason": result.predicted_reason,
            "correct": result.correct,
        },
        "visible_history": {
            "case_ids": list(result.visible_case_ids),
            "event_count": result.visible_event_count,
            "event_type_counts": result.visible_event_type_counts,
            "decay_checkpoints": result.decay_checkpoints,
        },
        "profile_snapshot": {
            "trust": result.trust,
            "cooperativeness": result.cooperativeness,
            "predictability": result.predictability,
            "stability": result.stability,
            "risk": result.risk,
            "overall_confidence": result.overall_confidence,
            "unknownness": result.unknownness,
            "freshness": result.freshness,
            "contradiction_load": result.contradiction_load,
        },
        "revalidation": {
            "triggered": result.revalidation_triggered,
            "reasons": list(result.revalidation_reasons),
        },
    }


def build_aggregate_summary(results: list[LabelEvaluationResult]) -> dict[str, Any]:
    total_labels = len(results)
    correct_predictions = sum(1 for result in results if result.correct)
    incorrect_predictions = total_labels - correct_predictions

    return {
        "total_labels": total_labels,
        "correct_predictions": correct_predictions,
        "incorrect_predictions": incorrect_predictions,
        "accuracy": (correct_predictions / total_labels) if total_labels else 0.0,
    }


def build_export_payload(
    results: list[LabelEvaluationResult],
    event_mapping_version: str,
) -> dict[str, Any]:
    return {
        "run_metadata": {
            "evaluation_name": "support_v1_label_evaluation",
            "dataset_path": project_relative_path(SOURCE_PATH),
            "labels_path": project_relative_path(LABELS_PATH),
            "export_path": project_relative_path(EXPORT_PATH),
            "event_mapping_version": event_mapping_version,
            "stakes": EVALUATION_STAKES,
            "decay_gap_days": DECAY_GAP_DAYS,
            "label_count": len(results),
        },
        "per_label_results": [build_result_payload(result) for result in results],
        "aggregate_summary": build_aggregate_summary(results),
    }


def export_results(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with EXPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return EXPORT_PATH


def print_label_summary(result: LabelEvaluationResult) -> None:
    print(
        " | ".join(
            [
                f"label={result.label.label_id}",
                f"ticket={result.label.ticket_id}",
                f"labeled={result.label.should_route}",
                f"predicted={result.predicted_path}",
                f"correct={result.correct}",
                f"visible_events={result.visible_event_count}",
                f"confidence={format_float(result.overall_confidence)}",
                f"freshness={format_float(result.freshness)}",
                f"unknownness={format_float(result.unknownness)}",
                f"contradiction={format_float(result.contradiction_load)}",
            ]
        )
    )


def print_aggregate_summary(summary: dict[str, Any], export_path: Path) -> None:
    print()
    print(
        " | ".join(
            [
                f"total_labels={summary['total_labels']}",
                f"correct_predictions={summary['correct_predictions']}",
                f"incorrect_predictions={summary['incorrect_predictions']}",
                f"accuracy={format_percent(float(summary['accuracy']))}",
            ]
        )
    )
    print(f"evaluation_export: {project_relative_path(export_path)}")


def main() -> None:
    cases = load_support_cases(SOURCE_PATH)
    labels = load_support_labels(LABELS_PATH)
    entity_events, event_mapping_version = build_entity_events(cases)
    cases_by_ticket_id = {case.case_id: case for case in cases}

    print("support_v1 label evaluation")
    print(f"dataset: {project_relative_path(SOURCE_PATH)}")
    print(f"labels: {project_relative_path(LABELS_PATH)}")
    print(f"artifact: {project_relative_path(EXPORT_PATH)}")
    print(f"stakes: {EVALUATION_STAKES}")
    print()

    results: list[LabelEvaluationResult] = []
    for label in labels:
        validate_label(label, cases_by_ticket_id, entity_events)
        result = evaluate_label(label, entity_events)
        results.append(result)
        print_label_summary(result)

    export_payload = build_export_payload(results, event_mapping_version)
    export_path = export_results(export_payload)
    print_aggregate_summary(export_payload["aggregate_summary"], export_path)


if __name__ == "__main__":
    main()
