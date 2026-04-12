from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_CSV_PATH = SCRIPT_DIR / "raw_support_export_sample.csv"
OUTPUT_PATH = SCRIPT_DIR / "artifacts" / "normalized_support_cases_from_csv.json"

REQUIRED_COLUMNS = (
    "entity_id",
    "account_name",
    "segment",
    "ticket_ref",
    "case_id",
    "opened_at",
    "closed_at",
    "channel",
    "priority",
    "summary",
    "record_id",
    "record_timestamp",
    "source_system",
    "source_type",
    "actor_role",
    "raw_action",
    "outcome",
    "details",
)


def require_value(row: dict[str, str], column: str, row_number: int) -> str:
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(f"Row {row_number} is missing required column '{column}'.")
    return value


def parse_optional_int(raw_value: str | None) -> int | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    return int(value)


def parse_optional_bool(raw_value: str | None) -> bool | None:
    value = (raw_value or "").strip().lower()
    if not value:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"Unsupported boolean value: {raw_value!r}")


def parse_pipe_list(raw_value: str | None) -> list[str] | None:
    values = [item.strip() for item in (raw_value or "").split("|") if item.strip()]
    return values or None


def build_metadata(row: dict[str, str]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    initial_context_quality = (row.get("initial_context_quality") or "").strip()
    if initial_context_quality:
        metadata["initial_context_quality"] = initial_context_quality

    response_quality = (row.get("response_quality") or "").strip()
    if response_quality:
        metadata["response_quality"] = response_quality

    fulfills_request = parse_optional_bool(row.get("fulfills_request", ""))
    if fulfills_request is not None:
        metadata["fulfills_request"] = fulfills_request

    request_id = (row.get("request_id") or "").strip()
    if request_id:
        metadata["request_id"] = request_id

    missed_request_count = parse_optional_int(row.get("missed_request_count", ""))
    if missed_request_count is not None:
        metadata["missed_request_count"] = missed_request_count

    missing_item_count = parse_optional_int(row.get("missing_item_count", ""))
    if missing_item_count is not None:
        metadata["missing_item_count"] = missing_item_count

    severity = (row.get("severity") or "").strip()
    if severity:
        metadata["severity"] = severity

    due_at = (row.get("due_at") or "").strip()
    if due_at:
        metadata["due_at"] = due_at

    missing_items = parse_pipe_list(row.get("missing_items", ""))
    if missing_items is not None:
        metadata["missing_items"] = missing_items

    attachments = parse_pipe_list(row.get("attachments", ""))
    if attachments is not None:
        metadata["attachments"] = attachments

    return metadata


def load_flat_export(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if reader.fieldnames is None:
        raise ValueError("CSV export is missing a header row.")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
    if missing_columns:
        raise ValueError(f"CSV export is missing required columns: {', '.join(missing_columns)}")

    return rows


def normalize_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    entities_by_id: dict[str, dict[str, Any]] = {}

    for index, row in enumerate(rows, start=2):
        row_values = {
            column: require_value(row, column, index)
            for column in REQUIRED_COLUMNS
        }

        entity = entities_by_id.setdefault(
            row_values["entity_id"],
            {
                "entity_id": row_values["entity_id"],
                "account_name": row_values["account_name"],
                "segment": row_values["segment"],
                "cases_by_ticket_ref": {},
            },
        )

        if entity["account_name"] != row_values["account_name"] or entity["segment"] != row_values["segment"]:
            raise ValueError(
                "Inconsistent entity fields for "
                f"{row_values['entity_id']} on row {index}."
            )

        case = entity["cases_by_ticket_ref"].setdefault(
            row_values["ticket_ref"],
            {
                "case_id": row_values["case_id"],
                "opened_at": row_values["opened_at"],
                "closed_at": row_values["closed_at"],
                "channel": row_values["channel"],
                "priority": row_values["priority"],
                "summary": row_values["summary"],
                "records": [],
            },
        )

        expected_case_fields = (
            ("case_id", row_values["case_id"]),
            ("opened_at", row_values["opened_at"]),
            ("closed_at", row_values["closed_at"]),
            ("channel", row_values["channel"]),
            ("priority", row_values["priority"]),
            ("summary", row_values["summary"]),
        )
        for field_name, expected_value in expected_case_fields:
            if case[field_name] != expected_value:
                raise ValueError(
                    "Inconsistent case fields for "
                    f"{row_values['ticket_ref']} on row {index}: {field_name}."
                )

        case["records"].append(
            {
                "record_id": row_values["record_id"],
                "timestamp": row_values["record_timestamp"],
                "source_system": row_values["source_system"],
                "source_type": row_values["source_type"],
                "actor_role": row_values["actor_role"],
                "raw_action": row_values["raw_action"],
                "outcome": row_values["outcome"],
                "details": row_values["details"],
                "metadata": build_metadata(row),
            }
        )

    entities: list[dict[str, Any]] = []
    for entity_id in sorted(entities_by_id):
        raw_entity = entities_by_id[entity_id]
        cases = []
        for raw_case in sorted(
            raw_entity["cases_by_ticket_ref"].values(),
            key=lambda item: (item["opened_at"], item["case_id"]),
        ):
            ordered_records = sorted(
                raw_case["records"],
                key=lambda item: (item["timestamp"], item["record_id"]),
            )
            cases.append(
                {
                    "case_id": raw_case["case_id"],
                    "opened_at": raw_case["opened_at"],
                    "closed_at": raw_case["closed_at"],
                    "channel": raw_case["channel"],
                    "priority": raw_case["priority"],
                    "summary": raw_case["summary"],
                    "records": ordered_records,
                }
            )

        entities.append(
            {
                "entity_id": raw_entity["entity_id"],
                "account_name": raw_entity["account_name"],
                "segment": raw_entity["segment"],
                "cases": cases,
            }
        )

    return {
        "dataset_name": "support_v1_csv_ingest_prototype",
        "entity_type": "support_account",
        "entities": entities,
    }


def write_normalized_cases(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return output_path


def main() -> None:
    rows = load_flat_export(SOURCE_CSV_PATH)
    normalized_payload = normalize_rows(rows)
    output_path = write_normalized_cases(normalized_payload, OUTPUT_PATH)
    print(f"source CSV path: {SOURCE_CSV_PATH}")
    print(f"normalized output path: {output_path}")


if __name__ == "__main__":
    main()
