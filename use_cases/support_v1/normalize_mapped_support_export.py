from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_CSV_PATH = SCRIPT_DIR / "helpdesk_export_sample_generic.csv"
MAPPING_PATH = SCRIPT_DIR / "helpdesk_export_mapping_template.json"
OUTPUT_PATH = SCRIPT_DIR / "artifacts" / "normalized_support_cases_from_mapping.json"

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

SUPPORTED_METADATA_TYPES = {"string", "bool", "int", "pipe_list"}


def load_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        mapping = json.load(handle)

    columns = mapping.get("columns")
    if not isinstance(columns, dict):
        raise ValueError("Mapping file must define a 'columns' object.")

    missing_columns = [
        column_name
        for column_name in REQUIRED_COLUMNS
        if not isinstance(columns.get(column_name), str) or not columns[column_name].strip()
    ]
    if missing_columns:
        raise ValueError(
            "Mapping file is missing required column mappings: "
            + ", ".join(missing_columns)
        )

    metadata_columns = mapping.get("metadata_columns", {})
    if not isinstance(metadata_columns, dict):
        raise ValueError("Mapping file 'metadata_columns' must be an object when provided.")

    for metadata_field, spec in metadata_columns.items():
        if not isinstance(spec, dict):
            raise ValueError(
                f"Metadata mapping for '{metadata_field}' must be an object."
            )

        column_name = spec.get("column")
        if not isinstance(column_name, str) or not column_name.strip():
            raise ValueError(
                f"Metadata mapping for '{metadata_field}' must define a non-empty column."
            )

        value_type = spec.get("type", "string")
        if value_type not in SUPPORTED_METADATA_TYPES:
            raise ValueError(
                f"Metadata mapping for '{metadata_field}' uses unsupported type '{value_type}'."
            )

    return mapping


def load_flat_export(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if reader.fieldnames is None:
        raise ValueError("CSV export is missing a header row.")

    return rows, reader.fieldnames


def validate_mapping_against_csv(fieldnames: list[str], mapping: dict[str, Any]) -> None:
    referenced_columns = set(mapping["columns"].values())
    for spec in mapping.get("metadata_columns", {}).values():
        referenced_columns.add(spec["column"])

    missing_columns = sorted(column for column in referenced_columns if column not in fieldnames)
    if missing_columns:
        raise ValueError(
            "CSV export is missing mapped columns: " + ", ".join(missing_columns)
        )


def require_value(row: dict[str, str], column: str, field_name: str, row_number: int) -> str:
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(
            f"Row {row_number} is missing required field '{field_name}' from column '{column}'."
        )
    return value


def parse_metadata_value(
    raw_value: str | None,
    value_type: str,
    list_delimiter: str,
) -> Any:
    value = (raw_value or "").strip()
    if not value:
        return None

    if value_type == "string":
        return value

    if value_type == "bool":
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        raise ValueError(f"Unsupported boolean value: {raw_value!r}")

    if value_type == "int":
        return int(value)

    if value_type == "pipe_list":
        values = [item.strip() for item in value.split(list_delimiter) if item.strip()]
        return values or None

    raise ValueError(f"Unsupported metadata type: {value_type}")


def build_metadata(row: dict[str, str], mapping: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    list_delimiter = mapping.get("list_delimiter", "|")

    for metadata_field, spec in mapping.get("metadata_columns", {}).items():
        parsed_value = parse_metadata_value(
            row.get(spec["column"]),
            spec.get("type", "string"),
            list_delimiter,
        )
        if parsed_value is not None:
            metadata[metadata_field] = parsed_value

    return metadata


def normalize_rows(rows: list[dict[str, str]], mapping: dict[str, Any]) -> dict[str, Any]:
    column_mapping = mapping["columns"]
    entities_by_id: dict[str, dict[str, Any]] = {}

    for index, row in enumerate(rows, start=2):
        row_values = {
            field_name: require_value(row, column_mapping[field_name], field_name, index)
            for field_name in REQUIRED_COLUMNS
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
                "metadata": build_metadata(row, mapping),
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
        "dataset_name": mapping.get("dataset_name", "support_v1_mapped_csv_ingest_prototype"),
        "entity_type": mapping.get("entity_type", "support_account"),
        "entities": entities,
    }


def write_normalized_cases(payload: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return output_path


def main() -> None:
    mapping = load_mapping(MAPPING_PATH)
    rows, fieldnames = load_flat_export(SOURCE_CSV_PATH)
    validate_mapping_against_csv(fieldnames, mapping)
    normalized_payload = normalize_rows(rows, mapping)
    output_path = write_normalized_cases(normalized_payload, OUTPUT_PATH)
    print(f"source CSV path: {SOURCE_CSV_PATH}")
    print(f"mapping path: {MAPPING_PATH}")
    print(f"normalized output path: {output_path}")


if __name__ == "__main__":
    main()
