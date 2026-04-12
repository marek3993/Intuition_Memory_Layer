from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_RAW_PATH = SCRIPT_DIR / "raw_support_export_sample.json"
OUTPUT_PATH = SCRIPT_DIR / "artifacts" / "normalized_support_cases.json"

SOURCE_TYPE_MAP = {
    "message": "ticket_comment",
    "ticket_status": "status_change",
    "workflow_timer": "system_timer",
    "audit_entry": "qa_review",
}

ACTOR_ROLE_MAP = {
    "customer": "requester",
    "support_agent": "agent",
    "automation": "system",
    "qa_analyst": "qa",
}

EVENT_NAME_TO_RAW_ACTION = {
    "ticket_created": "ticket_opened",
    "agent_requested_logs": "requested_diagnostics",
    "customer_supplied_artifacts": "provided_requested_info",
    "customer_confirmed_resolution": "confirmed_fix",
    "requester_deadline_elapsed": "request_deadline_missed",
    "customer_replied_without_artifacts": "followed_up_without_requested_info",
    "qa_flagged_conflict": "qa_marked_contradiction",
}

EVENT_NAME_TO_OUTCOME = {
    "ticket_created": "issue_reported",
    "agent_requested_logs": "diagnostics_requested",
    "customer_supplied_artifacts": "requested_artifacts_uploaded",
    "customer_confirmed_resolution": "resolution_confirmed",
    "requester_deadline_elapsed": "auto_closed_missing_requested_artifacts",
    "customer_replied_without_artifacts": "reply_missing_requested_artifacts",
    "qa_flagged_conflict": "claim_conflicts_with_prior_resolution",
}


def load_raw_export(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_record(raw_record: dict[str, Any], case_summary: str) -> dict[str, Any]:
    actor = dict(raw_record.get("actor", {}))
    raw_data = dict(raw_record.get("data", {}))
    raw_source_type = str(raw_record["source_type"])
    raw_actor_role = str(actor["role"])
    raw_event_name = str(raw_record["event_name"])

    try:
        source_type = SOURCE_TYPE_MAP[raw_source_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported raw source_type: {raw_source_type}") from exc

    try:
        actor_role = ACTOR_ROLE_MAP[raw_actor_role]
    except KeyError as exc:
        raise ValueError(f"Unsupported raw actor role: {raw_actor_role}") from exc

    try:
        raw_action = EVENT_NAME_TO_RAW_ACTION[raw_event_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported raw event_name: {raw_event_name}") from exc

    outcome = EVENT_NAME_TO_OUTCOME[raw_event_name]
    metadata = {
        **raw_data,
        "upstream_event_name": raw_event_name,
        "upstream_source_type": raw_source_type,
        "upstream_actor_role": raw_actor_role,
        "upstream_actor_id": actor.get("actor_id"),
        "upstream_actor_name": actor.get("display_name"),
        "upstream_ticket_ref": raw_record.get("ticket_ref"),
    }

    return {
        "record_id": str(raw_record["event_ref"]),
        "timestamp": str(raw_record["occurred_at"]),
        "source_system": str(raw_record["source_system"]),
        "source_type": source_type,
        "actor_role": actor_role,
        "raw_action": raw_action,
        "outcome": outcome,
        "details": str(raw_record.get("body") or case_summary),
        "metadata": metadata,
    }


def normalize_export(payload: dict[str, Any]) -> dict[str, Any]:
    accounts = payload.get("accounts", [])
    tickets = payload.get("tickets", [])
    records = payload.get("records", [])

    accounts_by_ref = {
        str(account["account_ref"]): account
        for account in accounts
    }

    records_by_ticket_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw_record in records:
        records_by_ticket_ref[str(raw_record["ticket_ref"])].append(raw_record)

    cases_by_account_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw_ticket in tickets:
        account_ref = str(raw_ticket["account_ref"])
        if account_ref not in accounts_by_ref:
            raise ValueError(f"Ticket references unknown account_ref: {account_ref}")
        case_summary = str(raw_ticket["subject"])
        case_records = [
            normalize_record(raw_record, case_summary)
            for raw_record in sorted(
                records_by_ticket_ref.get(str(raw_ticket["ticket_ref"]), []),
                key=lambda item: (str(item["occurred_at"]), str(item["event_ref"])),
            )
        ]
        cases_by_account_ref[account_ref].append(
            {
                "case_id": str(raw_ticket["case_id"]),
                "opened_at": str(raw_ticket["opened_at"]),
                "closed_at": str(raw_ticket["closed_at"]),
                "channel": str(raw_ticket["channel"]),
                "priority": str(raw_ticket["priority"]),
                "summary": case_summary,
                "records": case_records,
            }
        )

    entities: list[dict[str, Any]] = []
    for account_ref in sorted(cases_by_account_ref):
        raw_account = accounts_by_ref[account_ref]
        cases = sorted(
            cases_by_account_ref[account_ref],
            key=lambda item: (item["opened_at"], item["case_id"]),
        )
        entities.append(
            {
                "entity_id": str(raw_account["entity_id"]),
                "account_name": str(raw_account["display_name"]),
                "segment": str(raw_account["segment"]),
                "cases": cases,
            }
        )

    return {
        "dataset_name": "support_v1_raw_ingest_prototype",
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
    raw_payload = load_raw_export(SOURCE_RAW_PATH)
    normalized_payload = normalize_export(raw_payload)
    output_path = write_normalized_cases(normalized_payload, OUTPUT_PATH)
    print(f"source raw path: {SOURCE_RAW_PATH}")
    print(f"normalized output path: {output_path}")


if __name__ == "__main__":
    main()
