from __future__ import annotations

from typing import Any, Sequence

from convert_support_cases_to_events import SupportCase, SupportRecord, parse_timestamp
from evaluate_support_labels import SupportLabel, load_support_labels


def assert_unique_values(
    values: Sequence[str],
    *,
    label: str,
    slice_name: str,
) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []

    for value in values:
        if value in seen:
            duplicates.append(value)
            continue
        seen.add(value)

    if duplicates:
        duplicate_list = ", ".join(sorted(set(duplicates)))
        raise ValueError(
            f"Slice {slice_name} contains duplicate {label} values: {duplicate_list}."
        )


def load_support_cases_from_payload(payload: dict[str, Any]) -> list[SupportCase]:
    raw_entities = payload.get("entities")
    if not isinstance(raw_entities, list):
        raise ValueError("Normalized support payload must contain an 'entities' list.")

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


def load_combined_labels(
    labels_paths: Sequence[object],
    *,
    slice_name: str,
) -> list[SupportLabel]:
    labels: list[SupportLabel] = []
    for labels_path in labels_paths:
        labels.extend(load_support_labels(labels_path))

    assert_unique_values(
        [label.label_id for label in labels],
        label="label_id",
        slice_name=slice_name,
    )
    return labels
