from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_EXPORT_PATH = SCRIPT_DIR / "zendesk_like_export_sample.json"
OUTPUT_PATH = SCRIPT_DIR / "artifacts" / "normalized_support_cases_from_zendesk_like.json"

USER_ROLE_MAP = {
    "end_user": "requester",
    "agent": "agent",
    "system": "system",
    "qa": "qa",
}

EVENT_TYPE_MAP = {
    "status_change": {
        "source_type": "status_change",
        "raw_action": "confirmed_fix",
        "outcome": "resolution_confirmed",
    },
    "sla_breach": {
        "source_type": "system_timer",
        "raw_action": "request_deadline_missed",
        "outcome": "auto_closed_missing_requested_artifacts",
    },
    "qa_review": {
        "source_type": "qa_review",
        "raw_action": "qa_marked_contradiction",
        "outcome": "claim_conflicts_with_prior_resolution",
    },
}


def load_export(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_user_role(raw_role: str) -> str:
    try:
        return USER_ROLE_MAP[raw_role]
    except KeyError as exc:
        raise ValueError(f"Unsupported user role: {raw_role}") from exc


def build_upstream_ticket_metadata(ticket: dict[str, Any]) -> dict[str, Any]:
    return {
        "upstream_ticket_id": ticket["id"],
        "upstream_ticket_status": ticket["status"],
        "upstream_ticket_tags": ticket.get("tags", []),
        "upstream_ticket_form": ticket.get("ticket_form"),
        "upstream_ticket_custom_fields": ticket.get("custom_fields"),
        "upstream_ticket_channel": ticket.get("via", {}).get("channel"),
        "upstream_requester_id": ticket.get("requester_id"),
        "upstream_organization_id": ticket.get("organization_id"),
        "upstream_assignee_id": ticket.get("assignee_id"),
    }


def normalize_comment(
    raw_comment: dict[str, Any],
    ticket: dict[str, Any],
    author: dict[str, Any],
    comment_index: int,
) -> dict[str, Any]:
    actor_role = normalize_user_role(str(author["role"]))
    metadata = dict(raw_comment.get("metadata", {}))

    if actor_role == "requester" and comment_index == 0:
        raw_action = "ticket_opened"
        outcome = "issue_reported"
    elif actor_role == "requester" and metadata.get("fulfills_request") is True:
        raw_action = "provided_requested_info"
        outcome = "requested_artifacts_uploaded"
    elif actor_role == "requester" and metadata.get("followup_without_requested_info") is True:
        raw_action = "followed_up_without_requested_info"
        outcome = "reply_missing_requested_artifacts"
    elif actor_role == "agent" and metadata.get("request_id"):
        raw_action = "requested_diagnostics"
        outcome = "diagnostics_requested"
    else:
        raise ValueError(
            "Unsupported comment shape for "
            f"ticket {ticket['id']} comment {raw_comment['comment_id']}"
        )

    normalized_metadata = {
        **metadata,
        "upstream_comment_public": bool(raw_comment.get("public", False)),
        **build_upstream_ticket_metadata(ticket),
        "upstream_actor_id": author["user_id"],
        "upstream_actor_name": author["name"],
        "upstream_actor_role": author["role"],
    }

    return {
        "record_id": str(raw_comment["comment_id"]),
        "timestamp": str(raw_comment["created_at"]),
        "source_system": "zendesk_like",
        "source_type": "ticket_comment",
        "actor_role": actor_role,
        "raw_action": raw_action,
        "outcome": outcome,
        "details": str(raw_comment.get("body") or ticket["subject"]),
        "metadata": normalized_metadata,
    }


def normalize_event(
    raw_event: dict[str, Any],
    ticket: dict[str, Any],
    author: dict[str, Any],
) -> dict[str, Any]:
    event_type = str(raw_event["type"])
    try:
        event_mapping = EVENT_TYPE_MAP[event_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported event type: {event_type}") from exc

    actor_role = normalize_user_role(str(author["role"]))
    normalized_metadata = {
        **dict(raw_event.get("metadata", {})),
        "upstream_event_type": event_type,
        **build_upstream_ticket_metadata(ticket),
        "upstream_actor_id": author["user_id"],
        "upstream_actor_name": author["name"],
        "upstream_actor_role": author["role"],
    }

    return {
        "record_id": str(raw_event["event_id"]),
        "timestamp": str(raw_event["created_at"]),
        "source_system": "zendesk_like",
        "source_type": event_mapping["source_type"],
        "actor_role": actor_role,
        "raw_action": event_mapping["raw_action"],
        "outcome": event_mapping["outcome"],
        "details": str(raw_event.get("note") or ticket["subject"]),
        "metadata": normalized_metadata,
    }


def normalize_export(payload: dict[str, Any]) -> dict[str, Any]:
    organizations = payload.get("organizations", [])
    users = payload.get("users", [])
    tickets = payload.get("tickets", [])
    comments = payload.get("comments", [])
    events = payload.get("events", [])

    organizations_by_id = {
        int(organization["organization_id"]): organization
        for organization in organizations
    }
    users_by_id = {
        int(user["user_id"]): user
        for user in users
    }

    comments_by_ticket_id: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw_comment in comments:
        comments_by_ticket_id[int(raw_comment["ticket_id"])].append(raw_comment)

    events_by_ticket_id: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw_event in events:
        events_by_ticket_id[int(raw_event["ticket_id"])].append(raw_event)

    cases_by_entity_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    entity_fields_by_id: dict[str, dict[str, str]] = {}

    for ticket in tickets:
        organization_id = int(ticket["organization_id"])
        requester_id = int(ticket["requester_id"])

        if organization_id not in organizations_by_id:
            raise ValueError(f"Ticket references unknown organization_id: {organization_id}")
        if requester_id not in users_by_id:
            raise ValueError(f"Ticket references unknown requester_id: {requester_id}")

        organization = organizations_by_id[organization_id]
        entity_id = str(organization["entity_id"])
        entity_fields_by_id[entity_id] = {
            "account_name": str(organization["name"]),
            "segment": str(organization.get("details", {}).get("segment", "unknown")),
        }

        normalized_records: list[dict[str, Any]] = []
        ordered_comments = sorted(
            comments_by_ticket_id.get(int(ticket["id"]), []),
            key=lambda item: (str(item["created_at"]), str(item["comment_id"])),
        )
        for comment_index, raw_comment in enumerate(ordered_comments):
            author_id = int(raw_comment["author_id"])
            if author_id not in users_by_id:
                raise ValueError(f"Comment references unknown author_id: {author_id}")
            normalized_records.append(
                normalize_comment(raw_comment, ticket, users_by_id[author_id], comment_index)
            )

        ordered_events = sorted(
            events_by_ticket_id.get(int(ticket["id"]), []),
            key=lambda item: (str(item["created_at"]), str(item["event_id"])),
        )
        for raw_event in ordered_events:
            author_id = int(raw_event["author_id"])
            if author_id not in users_by_id:
                raise ValueError(f"Event references unknown author_id: {author_id}")
            normalized_records.append(
                normalize_event(raw_event, ticket, users_by_id[author_id])
            )

        cases_by_entity_id[entity_id].append(
            {
                "case_id": str(ticket["external_id"]),
                "opened_at": str(ticket["created_at"]),
                "closed_at": str(ticket["closed_at"]),
                "channel": str(ticket.get("via", {}).get("channel", "unknown")),
                "priority": str(ticket.get("priority", "unknown")),
                "summary": str(ticket["subject"]),
                "records": sorted(
                    normalized_records,
                    key=lambda item: (item["timestamp"], item["record_id"]),
                ),
            }
        )

    entities: list[dict[str, Any]] = []
    for entity_id in sorted(cases_by_entity_id):
        entity_fields = entity_fields_by_id[entity_id]
        entities.append(
            {
                "entity_id": entity_id,
                "account_name": entity_fields["account_name"],
                "segment": entity_fields["segment"],
                "cases": sorted(
                    cases_by_entity_id[entity_id],
                    key=lambda item: (item["opened_at"], item["case_id"]),
                ),
            }
        )

    return {
        "dataset_name": "support_v1_zendesk_like_ingest_prototype",
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
    payload = load_export(SOURCE_EXPORT_PATH)
    normalized_payload = normalize_export(payload)
    output_path = write_normalized_cases(normalized_payload, OUTPUT_PATH)
    print(f"source export path: {SOURCE_EXPORT_PATH}")
    print(f"normalized output path: {output_path}")


if __name__ == "__main__":
    main()
