from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from iml.models import Event


SOURCE_PATH = Path(__file__).with_name("sample_support_cases.json")
ARTIFACTS_DIR = Path(__file__).with_name("artifacts")
EVENTS_ARTIFACT_PATH = ARTIFACTS_DIR / "support_events.json"
LONG_INACTIVITY_GAP_DAYS = 30

SOURCE_TYPE_TO_BASE_RELIABILITY = {
    "ticket_comment": 0.78,
    "status_change": 0.86,
    "system_timer": 0.92,
    "qa_review": 0.95,
}

QUALITY_TO_INTENSITY = {
    "partial": 0.65,
    "useful": 0.70,
    "complete": 0.85,
}

SEVERITY_TO_INTENSITY = {
    "low": 0.65,
    "medium": 0.85,
    "high": 1.00,
}


@dataclass(frozen=True)
class SupportRecord:
    record_id: str
    timestamp: datetime
    source_system: str
    source_type: str
    actor_role: str
    raw_action: str
    outcome: str
    details: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class SupportCase:
    entity_id: str
    account_name: str
    segment: str
    case_id: str
    opened_at: datetime
    closed_at: datetime
    channel: str
    priority: str
    summary: str
    records: tuple[SupportRecord, ...]


def parse_timestamp(raw_timestamp: str) -> datetime:
    return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def load_support_cases(path: Path = SOURCE_PATH) -> list[SupportCase]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    raw_entities = payload.get("entities")
    if not isinstance(raw_entities, list):
        raise ValueError("Support dataset must contain an 'entities' list.")

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


def base_reliability(source_type: str) -> float:
    try:
        return SOURCE_TYPE_TO_BASE_RELIABILITY[source_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported source_type: {source_type}") from exc


def quality_intensity(value: str | None, fallback: float) -> float:
    if value is None:
        return fallback

    return QUALITY_TO_INTENSITY.get(value, fallback)


def contradiction_intensity(value: str | None) -> float:
    return SEVERITY_TO_INTENSITY.get(value or "medium", 0.85)


def build_event(
    case: SupportCase,
    record: SupportRecord,
    event_type: str,
    reliability: float,
    intensity: float,
    polarity: float,
) -> Event:
    return Event(
        event_id=f"{record.record_id}:{event_type}",
        entity_id=case.entity_id,
        timestamp=record.timestamp,
        event_type=event_type,
        source=f"support_{record.source_type}",
        reliability=clamp(reliability),
        polarity=polarity,
        intensity=clamp(intensity),
        metadata={
            "case_id": case.case_id,
            "record_id": record.record_id,
            "account_name": case.account_name,
            "segment": case.segment,
            "channel": case.channel,
            "priority": case.priority,
            "summary": case.summary,
            "raw_action": record.raw_action,
            "outcome": record.outcome,
            "details": record.details,
            "support_metadata": record.metadata,
        },
    )


def record_to_events(case: SupportCase, record: SupportRecord) -> list[Event]:
    events: list[Event] = []
    reliability = base_reliability(record.source_type)

    if record.raw_action == "ticket_opened":
        context_quality = str(record.metadata.get("initial_context_quality", "")).lower()
        if context_quality in {"useful", "complete"}:
            events.append(
                build_event(
                    case=case,
                    record=record,
                    event_type="cooperative_response",
                    reliability=reliability,
                    intensity=quality_intensity(context_quality, 0.65),
                    polarity=1.0,
                )
            )
        return events

    if record.raw_action == "provided_requested_info":
        response_quality = str(record.metadata.get("response_quality", "useful")).lower()
        intensity = quality_intensity(response_quality, 0.75)
        events.append(
            build_event(
                case=case,
                record=record,
                event_type="cooperative_response",
                reliability=reliability,
                intensity=intensity,
                polarity=1.0,
            )
        )
        if bool(record.metadata.get("fulfills_request")):
            events.append(
                build_event(
                    case=case,
                    record=record,
                    event_type="fulfilled_commitment",
                    reliability=reliability + 0.06,
                    intensity=intensity,
                    polarity=1.0,
                )
            )
        return events

    if record.raw_action == "completed_requested_step":
        events.append(
            build_event(
                case=case,
                record=record,
                event_type="fulfilled_commitment",
                reliability=reliability + 0.05,
                intensity=0.82,
                polarity=1.0,
            )
        )
        return events

    if record.raw_action == "confirmed_fix":
        events.append(
            build_event(
                case=case,
                record=record,
                event_type="fulfilled_commitment",
                reliability=reliability + 0.08,
                intensity=0.92,
                polarity=1.0,
            )
        )
        return events

    if record.raw_action == "followed_up_without_requested_info":
        missing_item_count = int(record.metadata.get("missing_item_count", 1))
        events.append(
            build_event(
                case=case,
                record=record,
                event_type="ignored_request",
                reliability=reliability,
                intensity=0.70 + (0.10 * max(0, missing_item_count - 1)),
                polarity=-1.0,
            )
        )
        return events

    if record.raw_action == "request_deadline_missed":
        missed_request_count = int(record.metadata.get("missed_request_count", 1))
        events.append(
            build_event(
                case=case,
                record=record,
                event_type="ignored_request",
                reliability=reliability,
                intensity=0.70 + (0.15 * max(0, missed_request_count - 1)),
                polarity=-1.0,
            )
        )
        return events

    if record.raw_action in {"qa_marked_contradiction", "reopened_with_conflicting_claim"}:
        severity = str(record.metadata.get("severity", "medium")).lower()
        events.append(
            build_event(
                case=case,
                record=record,
                event_type="contradiction_detected",
                reliability=reliability,
                intensity=contradiction_intensity(severity),
                polarity=-1.0,
            )
        )

    return events


def add_long_inactivity_events(entity_id: str, events: list[Event]) -> list[Event]:
    if not events:
        return []

    ordered_events = sorted(events, key=lambda event: (event.timestamp, event.event_id))
    enriched_events: list[Event] = []
    inactivity_index = 0

    for previous_event, next_event in zip(ordered_events, ordered_events[1:]):
        enriched_events.append(previous_event)
        gap_days = (next_event.timestamp - previous_event.timestamp).total_seconds() / 86_400
        if gap_days < LONG_INACTIVITY_GAP_DAYS:
            continue

        inactivity_index += 1
        enriched_events.append(
            Event(
                event_id=f"{entity_id}:gap:{inactivity_index:02d}",
                entity_id=entity_id,
                timestamp=next_event.timestamp - timedelta(minutes=1),
                event_type="long_inactivity",
                source="support_gap_detector",
                reliability=0.90,
                polarity=-1.0,
                intensity=clamp(gap_days / 60.0, min_value=0.50),
                metadata={
                    "gap_days": round(gap_days, 2),
                    "from_event_id": previous_event.event_id,
                    "to_event_id": next_event.event_id,
                },
            )
        )

    enriched_events.append(ordered_events[-1])
    return sorted(enriched_events, key=lambda event: (event.timestamp, event.event_id))


def serialize_event(event: Event) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "entity_id": event.entity_id,
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "source": event.source,
        "reliability": event.reliability,
        "polarity": event.polarity,
        "intensity": event.intensity,
        "metadata": event.metadata,
    }


def convert_cases_to_entity_event_payload(
    cases: list[SupportCase],
    source_path: Path = SOURCE_PATH,
) -> dict[str, Any]:
    grouped_cases: dict[str, list[SupportCase]] = {}
    for case in cases:
        grouped_cases.setdefault(case.entity_id, []).append(case)

    entities_payload: list[dict[str, Any]] = []
    for entity_id in sorted(grouped_cases):
        entity_cases = grouped_cases[entity_id]
        raw_events: list[Event] = []
        for case in entity_cases:
            for record in sorted(case.records, key=lambda item: (item.timestamp, item.record_id)):
                raw_events.extend(record_to_events(case, record))

        entity_events = add_long_inactivity_events(entity_id, raw_events)
        entities_payload.append(
            {
                "entity_id": entity_id,
                "account_name": entity_cases[0].account_name,
                "segment": entity_cases[0].segment,
                "case_ids": [case.case_id for case in entity_cases],
                "event_count": len(entity_events),
                "events": [serialize_event(event) for event in entity_events],
            }
        )

    return {
        "run_metadata": {
            "generated_at": datetime.now().astimezone().isoformat(),
            "source_path": str(source_path),
            "event_mapping_version": "support_v1",
            "long_inactivity_gap_days": LONG_INACTIVITY_GAP_DAYS,
        },
        "entity_type": "support_account",
        "entities": entities_payload,
    }


def export_events(
    payload: dict[str, Any],
    output_path: Path = EVENTS_ARTIFACT_PATH,
) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return output_path


def main() -> None:
    cases = load_support_cases(SOURCE_PATH)
    payload = convert_cases_to_entity_event_payload(cases, SOURCE_PATH)
    output_path = export_events(payload, EVENTS_ARTIFACT_PATH)
    print(f"support_events_export: {output_path}")


if __name__ == "__main__":
    main()
