from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACT_PATH = SCRIPT_DIR / "artifacts" / "helpdesk_export_contract_validation.json"
DEFAULT_INPUT_PATHS = (
    SCRIPT_DIR / "raw_support_export_sample.json",
    SCRIPT_DIR / "zendesk_like_export_sample.json",
    SCRIPT_DIR / "helpdesk_export_sample_generic.csv",
)

RAW_SOURCE_TYPES = {"message", "ticket_status", "workflow_timer", "audit_entry"}
RAW_ACTOR_ROLES = {"customer", "support_agent", "automation", "qa_analyst"}
RAW_EVENT_NAMES = {
    "ticket_created",
    "agent_requested_logs",
    "customer_supplied_artifacts",
    "customer_confirmed_resolution",
    "requester_deadline_elapsed",
    "customer_replied_without_artifacts",
    "qa_flagged_conflict",
}
ZENDESK_USER_ROLES = {"end_user", "agent", "system", "qa"}
ZENDESK_EVENT_TYPES = {"status_change", "sla_breach", "qa_review"}
CSV_REQUIRED_COLUMNS = (
    "customer_account_key",
    "customer_name",
    "customer_tier",
    "helpdesk_ticket_ref",
    "case_code",
    "case_opened_ts",
    "case_closed_ts",
    "intake_channel",
    "case_priority",
    "case_subject",
    "activity_id",
    "event_occurred_ts",
    "platform_name",
    "activity_kind",
    "performed_by_role",
    "normalized_action",
    "normalized_outcome",
    "activity_detail",
)
CSV_ALLOWED_ROLES = {"requester", "agent", "system", "qa"}


@dataclass
class ValidationResult:
    input_path: str
    detected_format: str = "unknown"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    entity_count: int = 0
    ticket_count: int = 0
    record_count: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_path": self.input_path,
            "detected_format": self.detected_format,
            "passed": self.passed,
            "warning_count": len(self.warnings),
            "error_count": len(self.errors),
            "entity_count": self.entity_count,
            "ticket_count": self.ticket_count,
            "record_count": self.record_count,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def parse_timestamp(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is missing.")

    raw_value = value.strip()
    normalized = raw_value[:-1] + "+00:00" if raw_value.endswith("Z") else raw_value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not valid ISO-8601: {raw_value!r}") from exc

    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} is missing a timezone offset: {raw_value!r}")
    return parsed


def require_non_empty_string(container: dict[str, Any], field_name: str) -> str | None:
    value = container.get(field_name)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def require_list(payload: dict[str, Any], key: str, result: ValidationResult) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        result.error(f"Top-level field '{key}' must be a list.")
        return []
    return value


def parse_json(path: Path, result: ValidationResult) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        result.error(f"JSON parse error: {exc}")
        return None
    if not isinstance(payload, dict):
        result.error("JSON export must be an object at the top level.")
        return None
    return payload


def detect_json_format(payload: dict[str, Any]) -> str:
    if {"accounts", "tickets", "records"}.issubset(payload):
        return "raw_json"
    if {"organizations", "users", "tickets", "comments", "events"}.issubset(payload):
        return "zendesk_like_json"
    return "unknown_json"


def validate_common_exported_at(payload: dict[str, Any], result: ValidationResult) -> None:
    exported_at = payload.get("exported_at")
    if exported_at is None:
        result.warn("Top-level 'exported_at' is missing.")
        return
    try:
        parse_timestamp(exported_at, "exported_at")
    except ValueError as exc:
        result.error(str(exc))


def validate_raw_json(path: Path, payload: dict[str, Any], result: ValidationResult) -> None:
    del path
    result.detected_format = "raw_json"
    validate_common_exported_at(payload, result)

    accounts = require_list(payload, "accounts", result)
    tickets = require_list(payload, "tickets", result)
    records = require_list(payload, "records", result)

    accounts_by_ref: dict[str, dict[str, Any]] = {}
    entity_ids: set[str] = set()
    for index, account in enumerate(accounts, start=1):
        if not isinstance(account, dict):
            result.error(f"accounts[{index}] must be an object.")
            continue
        account_ref = require_non_empty_string(account, "account_ref")
        entity_id = require_non_empty_string(account, "entity_id")
        display_name = require_non_empty_string(account, "display_name")
        segment = require_non_empty_string(account, "segment")

        if account_ref is None:
            result.error(f"accounts[{index}] is missing 'account_ref'.")
            continue
        if entity_id is None:
            result.error(f"accounts[{index}] ({account_ref}) is missing 'entity_id'.")
        if display_name is None:
            result.error(f"accounts[{index}] ({account_ref}) is missing 'display_name'.")
        if segment is None:
            result.error(f"accounts[{index}] ({account_ref}) is missing 'segment'.")
        if account_ref in accounts_by_ref:
            result.error(f"Duplicate account_ref: {account_ref}")
            continue
        if entity_id and entity_id in entity_ids:
            result.error(f"Duplicate entity_id across accounts: {entity_id}")
        accounts_by_ref[account_ref] = account
        if entity_id:
            entity_ids.add(entity_id)

    tickets_by_ref: dict[str, dict[str, Any]] = {}
    ticket_windows: dict[str, tuple[datetime, datetime]] = {}
    case_ids: defaultdict[str, list[str]] = defaultdict(list)
    for index, ticket in enumerate(tickets, start=1):
        if not isinstance(ticket, dict):
            result.error(f"tickets[{index}] must be an object.")
            continue
        ticket_ref = require_non_empty_string(ticket, "ticket_ref")
        case_id = require_non_empty_string(ticket, "case_id")
        account_ref = require_non_empty_string(ticket, "account_ref")
        opened_at = require_non_empty_string(ticket, "opened_at")
        closed_at = require_non_empty_string(ticket, "closed_at")
        channel = require_non_empty_string(ticket, "channel")
        priority = require_non_empty_string(ticket, "priority")
        subject = require_non_empty_string(ticket, "subject")

        if ticket_ref is None:
            result.error(f"tickets[{index}] is missing 'ticket_ref'.")
            continue
        if case_id is None:
            result.error(f"tickets[{index}] ({ticket_ref}) is missing 'case_id'.")
        if account_ref is None:
            result.error(f"tickets[{index}] ({ticket_ref}) is missing 'account_ref'.")
        elif account_ref not in accounts_by_ref:
            result.error(f"tickets[{index}] ({ticket_ref}) references unknown account_ref: {account_ref}")
        if opened_at is None:
            result.error(f"tickets[{index}] ({ticket_ref}) is missing 'opened_at'.")
        if closed_at is None:
            result.error(f"tickets[{index}] ({ticket_ref}) is missing 'closed_at'.")
        if channel is None:
            result.error(f"tickets[{index}] ({ticket_ref}) is missing 'channel'.")
        if priority is None:
            result.error(f"tickets[{index}] ({ticket_ref}) is missing 'priority'.")
        if subject is None:
            result.error(f"tickets[{index}] ({ticket_ref}) is missing 'subject'.")
        if ticket_ref in tickets_by_ref:
            result.error(f"Duplicate ticket_ref: {ticket_ref}")
            continue

        opened_dt: datetime | None = None
        closed_dt: datetime | None = None
        if opened_at is not None:
            try:
                opened_dt = parse_timestamp(opened_at, f"tickets[{index}].opened_at")
            except ValueError as exc:
                result.error(str(exc))
        if closed_at is not None:
            try:
                closed_dt = parse_timestamp(closed_at, f"tickets[{index}].closed_at")
            except ValueError as exc:
                result.error(str(exc))
        if opened_dt and closed_dt:
            if closed_dt < opened_dt:
                result.error(f"tickets[{index}] ({ticket_ref}) closes before it opens.")
            else:
                ticket_windows[ticket_ref] = (opened_dt, closed_dt)

        tickets_by_ref[ticket_ref] = ticket
        if case_id:
            case_ids[case_id].append(ticket_ref)

    for case_id, ticket_refs in case_ids.items():
        if len(ticket_refs) > 1:
            result.warn(f"Repeated case_id across ticket refs: {case_id} -> {', '.join(sorted(ticket_refs))}")

    seen_record_ids_by_ticket: defaultdict[str, set[str]] = defaultdict(set)
    record_count_by_ticket: defaultdict[str, int] = defaultdict(int)
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            result.error(f"records[{index}] must be an object.")
            continue
        event_ref = require_non_empty_string(record, "event_ref")
        ticket_ref = require_non_empty_string(record, "ticket_ref")
        occurred_at = require_non_empty_string(record, "occurred_at")
        source_system = require_non_empty_string(record, "source_system")
        source_type = require_non_empty_string(record, "source_type")
        event_name = require_non_empty_string(record, "event_name")

        if event_ref is None:
            result.error(f"records[{index}] is missing 'event_ref'.")
        if ticket_ref is None:
            result.error(f"records[{index}] is missing 'ticket_ref'.")
            continue
        if ticket_ref not in tickets_by_ref:
            result.error(f"records[{index}] references unknown ticket_ref: {ticket_ref}")
            continue
        if event_ref and event_ref in seen_record_ids_by_ticket[ticket_ref]:
            result.error(f"Duplicate event_ref within ticket {ticket_ref}: {event_ref}")
        if event_ref:
            seen_record_ids_by_ticket[ticket_ref].add(event_ref)
        if occurred_at is None:
            result.error(f"records[{index}] ({ticket_ref}) is missing 'occurred_at'.")
        if source_system is None:
            result.error(f"records[{index}] ({ticket_ref}) is missing 'source_system'.")
        if source_type is None:
            result.error(f"records[{index}] ({ticket_ref}) is missing 'source_type'.")
        elif source_type not in RAW_SOURCE_TYPES:
            result.error(f"records[{index}] ({ticket_ref}) uses unsupported source_type: {source_type}")
        if event_name is None:
            result.error(f"records[{index}] ({ticket_ref}) is missing 'event_name'.")
        elif event_name not in RAW_EVENT_NAMES:
            result.error(f"records[{index}] ({ticket_ref}) uses unsupported event_name: {event_name}")

        actor = record.get("actor")
        if not isinstance(actor, dict):
            result.error(f"records[{index}] ({ticket_ref}) is missing 'actor' object.")
        else:
            actor_role = require_non_empty_string(actor, "role")
            if actor_role is None:
                result.error(f"records[{index}] ({ticket_ref}) actor is missing 'role'.")
            elif actor_role not in RAW_ACTOR_ROLES:
                result.error(f"records[{index}] ({ticket_ref}) uses unsupported actor role: {actor_role}")
            if not require_non_empty_string(actor, "actor_id") and not require_non_empty_string(actor, "display_name"):
                result.warn(
                    f"records[{index}] ({ticket_ref}) is missing optional actor identity fields "
                    "(actor_id/display_name)."
                )

        if occurred_at is not None:
            try:
                occurred_dt = parse_timestamp(occurred_at, f"records[{index}].occurred_at")
                if ticket_ref in ticket_windows:
                    opened_dt, closed_dt = ticket_windows[ticket_ref]
                    if occurred_dt < opened_dt or occurred_dt > closed_dt:
                        result.warn(f"records[{index}] ({ticket_ref}) timestamp falls outside the ticket open/close window.")
            except ValueError as exc:
                result.error(str(exc))

        body = record.get("body")
        if (not isinstance(body, str) or not body.strip()) and not require_non_empty_string(tickets_by_ref[ticket_ref], "subject"):
            result.error(f"records[{index}] ({ticket_ref}) has no detail text and the ticket subject is also missing.")
        elif not isinstance(body, str) or not body.strip():
            result.warn(f"records[{index}] ({ticket_ref}) has blank body; adapter will fall back to ticket subject.")

        record_count_by_ticket[ticket_ref] += 1

    for ticket_ref in sorted(tickets_by_ref):
        if record_count_by_ticket[ticket_ref] == 0:
            result.error(f"Ticket {ticket_ref} has zero records.")

    result.entity_count = len(accounts_by_ref)
    result.ticket_count = len(tickets_by_ref)
    result.record_count = sum(record_count_by_ticket.values())


def classify_zendesk_comment(comment: dict[str, Any], author_role: str, comment_index: int) -> str | None:
    metadata = comment.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}

    if author_role == "end_user" and comment_index == 0:
        return "ticket_opened"
    if author_role == "end_user" and metadata.get("fulfills_request") is True:
        return "provided_requested_info"
    if author_role == "end_user" and metadata.get("followup_without_requested_info") is True:
        return "followed_up_without_requested_info"
    if author_role == "agent" and isinstance(metadata.get("request_id"), str) and metadata["request_id"].strip():
        return "requested_diagnostics"
    return None


def validate_zendesk_like_json(path: Path, payload: dict[str, Any], result: ValidationResult) -> None:
    del path
    result.detected_format = "zendesk_like_json"
    validate_common_exported_at(payload, result)

    organizations = require_list(payload, "organizations", result)
    users = require_list(payload, "users", result)
    tickets = require_list(payload, "tickets", result)
    comments = require_list(payload, "comments", result)
    events = require_list(payload, "events", result)

    organizations_by_id: dict[int, dict[str, Any]] = {}
    entity_ids: set[str] = set()
    for index, organization in enumerate(organizations, start=1):
        if not isinstance(organization, dict):
            result.error(f"organizations[{index}] must be an object.")
            continue
        raw_org_id = organization.get("organization_id")
        if raw_org_id is None:
            result.error(f"organizations[{index}] is missing 'organization_id'.")
            continue
        try:
            organization_id = int(raw_org_id)
        except (TypeError, ValueError):
            result.error(f"organizations[{index}].organization_id must be an integer-like value.")
            continue

        entity_id = require_non_empty_string(organization, "entity_id")
        name = require_non_empty_string(organization, "name")
        if entity_id is None:
            result.error(f"organizations[{index}] ({organization_id}) is missing 'entity_id'.")
        if name is None:
            result.error(f"organizations[{index}] ({organization_id}) is missing 'name'.")
        if organization_id in organizations_by_id:
            result.error(f"Duplicate organization_id: {organization_id}")
            continue
        if entity_id and entity_id in entity_ids:
            result.error(f"Duplicate entity_id across organizations: {entity_id}")

        details = organization.get("details")
        segment = require_non_empty_string(details, "segment") if isinstance(details, dict) else None
        if segment is None:
            result.warn(f"organizations[{index}] ({organization_id}) is missing optional details.segment.")

        organizations_by_id[organization_id] = organization
        if entity_id:
            entity_ids.add(entity_id)

    users_by_id: dict[int, dict[str, Any]] = {}
    referenced_user_ids: set[int] = set()
    for index, user in enumerate(users, start=1):
        if not isinstance(user, dict):
            result.error(f"users[{index}] must be an object.")
            continue
        raw_user_id = user.get("user_id")
        if raw_user_id is None:
            result.error(f"users[{index}] is missing 'user_id'.")
            continue
        try:
            user_id = int(raw_user_id)
        except (TypeError, ValueError):
            result.error(f"users[{index}].user_id must be an integer-like value.")
            continue

        role = require_non_empty_string(user, "role")
        name = require_non_empty_string(user, "name")
        if role is None:
            result.error(f"users[{index}] ({user_id}) is missing 'role'.")
        if name is None:
            result.error(f"users[{index}] ({user_id}) is missing 'name'.")
        if user_id in users_by_id:
            result.error(f"Duplicate user_id: {user_id}")
            continue
        users_by_id[user_id] = user

    tickets_by_id: dict[int, dict[str, Any]] = {}
    ticket_windows: dict[int, tuple[datetime, datetime]] = {}
    external_ids: defaultdict[str, list[int]] = defaultdict(list)
    for index, ticket in enumerate(tickets, start=1):
        if not isinstance(ticket, dict):
            result.error(f"tickets[{index}] must be an object.")
            continue
        raw_ticket_id = ticket.get("id")
        if raw_ticket_id is None:
            result.error(f"tickets[{index}] is missing 'id'.")
            continue
        try:
            ticket_id = int(raw_ticket_id)
        except (TypeError, ValueError):
            result.error(f"tickets[{index}].id must be an integer-like value.")
            continue

        external_id = require_non_empty_string(ticket, "external_id")
        subject = require_non_empty_string(ticket, "subject")
        status = require_non_empty_string(ticket, "status")
        created_at = require_non_empty_string(ticket, "created_at")
        closed_at = require_non_empty_string(ticket, "closed_at")
        raw_org_id = ticket.get("organization_id")
        raw_requester_id = ticket.get("requester_id")

        if external_id is None:
            result.error(f"tickets[{index}] ({ticket_id}) is missing 'external_id'.")
        if subject is None:
            result.error(f"tickets[{index}] ({ticket_id}) is missing 'subject'.")
        if status is None:
            result.error(f"tickets[{index}] ({ticket_id}) is missing 'status'.")
        if created_at is None:
            result.error(f"tickets[{index}] ({ticket_id}) is missing 'created_at'.")
        if closed_at is None:
            result.error(f"tickets[{index}] ({ticket_id}) is missing 'closed_at'.")
        if ticket_id in tickets_by_id:
            result.error(f"Duplicate ticket id: {ticket_id}")
            continue

        organization_id: int | None = None
        requester_id: int | None = None
        try:
            organization_id = int(raw_org_id)
        except (TypeError, ValueError):
            result.error(f"tickets[{index}] ({ticket_id}) has invalid organization_id.")
        try:
            requester_id = int(raw_requester_id)
        except (TypeError, ValueError):
            result.error(f"tickets[{index}] ({ticket_id}) has invalid requester_id.")

        if organization_id is not None and organization_id not in organizations_by_id:
            result.error(f"tickets[{index}] ({ticket_id}) references unknown organization_id: {organization_id}")
        if requester_id is not None:
            referenced_user_ids.add(requester_id)
            if requester_id not in users_by_id:
                result.error(f"tickets[{index}] ({ticket_id}) references unknown requester_id: {requester_id}")

        via = ticket.get("via")
        channel = require_non_empty_string(via, "channel") if isinstance(via, dict) else None
        if channel is None:
            result.warn(f"tickets[{index}] ({ticket_id}) is missing optional via.channel.")
        if require_non_empty_string(ticket, "priority") is None:
            result.warn(f"tickets[{index}] ({ticket_id}) is missing optional priority.")

        created_dt: datetime | None = None
        closed_dt: datetime | None = None
        if created_at is not None:
            try:
                created_dt = parse_timestamp(created_at, f"tickets[{index}].created_at")
            except ValueError as exc:
                result.error(str(exc))
        if closed_at is not None:
            try:
                closed_dt = parse_timestamp(closed_at, f"tickets[{index}].closed_at")
            except ValueError as exc:
                result.error(str(exc))
        if created_dt and closed_dt:
            if closed_dt < created_dt:
                result.error(f"tickets[{index}] ({ticket_id}) closes before it opens.")
            else:
                ticket_windows[ticket_id] = (created_dt, closed_dt)

        tickets_by_id[ticket_id] = ticket
        if external_id:
            external_ids[external_id].append(ticket_id)

    for external_id, ticket_ids in external_ids.items():
        if len(ticket_ids) > 1:
            joined = ", ".join(str(ticket_id) for ticket_id in sorted(ticket_ids))
            result.warn(f"Repeated external_id across tickets: {external_id} -> {joined}")

    comments_by_ticket_id: defaultdict[int, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    seen_comment_ids_by_ticket: defaultdict[int, set[str]] = defaultdict(set)
    for index, comment in enumerate(comments, start=1):
        if not isinstance(comment, dict):
            result.error(f"comments[{index}] must be an object.")
            continue
        comment_id = comment.get("comment_id")
        ticket_id_raw = comment.get("ticket_id")
        author_id_raw = comment.get("author_id")
        created_at = comment.get("created_at")

        if not isinstance(comment_id, str) or not comment_id.strip():
            result.error(f"comments[{index}] is missing 'comment_id'.")
            continue
        try:
            ticket_id = int(ticket_id_raw)
        except (TypeError, ValueError):
            result.error(f"comments[{index}] ({comment_id}) has invalid ticket_id.")
            continue
        try:
            author_id = int(author_id_raw)
        except (TypeError, ValueError):
            result.error(f"comments[{index}] ({comment_id}) has invalid author_id.")
            continue
        if ticket_id not in tickets_by_id:
            result.error(f"comments[{index}] ({comment_id}) references unknown ticket_id: {ticket_id}")
            continue
        if author_id not in users_by_id:
            result.error(f"comments[{index}] ({comment_id}) references unknown author_id: {author_id}")
            continue
        referenced_user_ids.add(author_id)
        if comment_id in seen_comment_ids_by_ticket[ticket_id]:
            result.error(f"Duplicate comment_id within ticket {ticket_id}: {comment_id}")
        seen_comment_ids_by_ticket[ticket_id].add(comment_id)

        try:
            comment_dt = parse_timestamp(created_at, f"comments[{index}].created_at")
            if ticket_id in ticket_windows:
                opened_dt, closed_dt = ticket_windows[ticket_id]
                if comment_dt < opened_dt or comment_dt > closed_dt:
                    result.warn(f"comments[{index}] ({comment_id}) timestamp falls outside the ticket open/close window.")
        except ValueError as exc:
            result.error(str(exc))

        comments_by_ticket_id[ticket_id].append((index, comment))

    events_by_ticket_id: defaultdict[int, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    seen_event_ids_by_ticket: defaultdict[int, set[str]] = defaultdict(set)
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            result.error(f"events[{index}] must be an object.")
            continue
        event_id = event.get("event_id")
        ticket_id_raw = event.get("ticket_id")
        author_id_raw = event.get("author_id")
        created_at = event.get("created_at")
        event_type = event.get("type")

        if not isinstance(event_id, str) or not event_id.strip():
            result.error(f"events[{index}] is missing 'event_id'.")
            continue
        try:
            ticket_id = int(ticket_id_raw)
        except (TypeError, ValueError):
            result.error(f"events[{index}] ({event_id}) has invalid ticket_id.")
            continue
        try:
            author_id = int(author_id_raw)
        except (TypeError, ValueError):
            result.error(f"events[{index}] ({event_id}) has invalid author_id.")
            continue
        if ticket_id not in tickets_by_id:
            result.error(f"events[{index}] ({event_id}) references unknown ticket_id: {ticket_id}")
            continue
        if author_id not in users_by_id:
            result.error(f"events[{index}] ({event_id}) references unknown author_id: {author_id}")
            continue
        referenced_user_ids.add(author_id)
        if event_id in seen_event_ids_by_ticket[ticket_id]:
            result.error(f"Duplicate event_id within ticket {ticket_id}: {event_id}")
        seen_event_ids_by_ticket[ticket_id].add(event_id)

        if not isinstance(event_type, str) or not event_type.strip():
            result.error(f"events[{index}] ({event_id}) is missing 'type'.")
        elif event_type not in ZENDESK_EVENT_TYPES:
            result.error(f"events[{index}] ({event_id}) uses unsupported event type: {event_type}")

        try:
            event_dt = parse_timestamp(created_at, f"events[{index}].created_at")
            if ticket_id in ticket_windows:
                opened_dt, closed_dt = ticket_windows[ticket_id]
                if event_dt < opened_dt or event_dt > closed_dt:
                    result.warn(f"events[{index}] ({event_id}) timestamp falls outside the ticket open/close window.")
        except ValueError as exc:
            result.error(str(exc))

        events_by_ticket_id[ticket_id].append((index, event))

    for user_id in sorted(referenced_user_ids):
        user = users_by_id.get(user_id)
        if user is None:
            continue
        role = require_non_empty_string(user, "role")
        if role and role not in ZENDESK_USER_ROLES:
            result.error(f"Referenced user {user_id} uses unsupported role: {role}")

    total_record_count = 0
    for ticket_id, ticket in tickets_by_id.items():
        ordered_comments = sorted(
            comments_by_ticket_id.get(ticket_id, []),
            key=lambda item: (str(item[1].get("created_at", "")), str(item[1].get("comment_id", ""))),
        )
        for comment_index, (input_index, comment) in enumerate(ordered_comments):
            author_id = int(comment["author_id"])
            author_role = str(users_by_id[author_id]["role"])
            if classify_zendesk_comment(comment, author_role, comment_index) is None:
                result.error(f"comments[{input_index}] ({comment['comment_id']}) does not match a supported comment shape.")

            body = comment.get("body")
            if not isinstance(body, str) or not body.strip():
                if require_non_empty_string(ticket, "subject") is None:
                    result.error(f"comments[{input_index}] ({comment['comment_id']}) has no body and the ticket subject is missing.")
                else:
                    result.warn(f"comments[{input_index}] ({comment['comment_id']}) has blank body; adapter will fall back to ticket subject.")

            requester_org_id = users_by_id[author_id].get("organization_id")
            ticket_org_id = ticket.get("organization_id")
            if author_role == "end_user" and requester_org_id is not None and requester_org_id != ticket_org_id:
                result.warn(f"comments[{input_index}] ({comment['comment_id']}) author organization_id does not match the ticket organization_id.")
            total_record_count += 1

        ordered_events = sorted(
            events_by_ticket_id.get(ticket_id, []),
            key=lambda item: (str(item[1].get("created_at", "")), str(item[1].get("event_id", ""))),
        )
        for input_index, event in ordered_events:
            author_id = int(event["author_id"])
            author_role = str(users_by_id[author_id]["role"])
            if author_role not in ZENDESK_USER_ROLES:
                result.error(f"events[{input_index}] ({event['event_id']}) author uses unsupported role: {author_role}")

            note = event.get("note")
            if not isinstance(note, str) or not note.strip():
                if require_non_empty_string(ticket, "subject") is None:
                    result.error(f"events[{input_index}] ({event['event_id']}) has no note and the ticket subject is missing.")
                else:
                    result.warn(f"events[{input_index}] ({event['event_id']}) has blank note; adapter will fall back to ticket subject.")
            total_record_count += 1

        if not ordered_comments and not ordered_events:
            result.error(f"Ticket {ticket_id} has zero comments/events.")

    result.entity_count = len(organizations_by_id)
    result.ticket_count = len(tickets_by_id)
    result.record_count = total_record_count


def validate_csv(path: Path, result: ValidationResult) -> None:
    result.detected_format = "flat_csv"
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except csv.Error as exc:
        result.error(f"CSV parse error: {exc}")
        return

    fieldnames = reader.fieldnames
    if fieldnames is None:
        result.error("CSV export is missing a header row.")
        return

    missing_columns = [column for column in CSV_REQUIRED_COLUMNS if column not in fieldnames]
    if missing_columns:
        result.error("CSV export is missing required columns: " + ", ".join(missing_columns))
        return

    entities_by_id: dict[str, tuple[str, str]] = {}
    cases_by_ticket_ref: dict[str, tuple[str, str, str, str, str, str, str]] = {}
    seen_record_ids_by_ticket: defaultdict[str, set[str]] = defaultdict(set)
    ticket_windows: dict[str, tuple[datetime, datetime]] = {}
    record_count_by_ticket: defaultdict[str, int] = defaultdict(int)

    for row_number, row in enumerate(rows, start=2):
        row_values: dict[str, str] = {}
        for column in CSV_REQUIRED_COLUMNS:
            value = (row.get(column) or "").strip()
            if not value:
                result.error(f"Row {row_number} is missing required column '{column}'.")
            row_values[column] = value
        if any(not row_values[column] for column in CSV_REQUIRED_COLUMNS):
            continue

        entity_id = row_values["customer_account_key"]
        entity_name = row_values["customer_name"]
        entity_segment = row_values["customer_tier"]
        ticket_ref = row_values["helpdesk_ticket_ref"]
        case_tuple = (
            row_values["case_code"],
            row_values["case_opened_ts"],
            row_values["case_closed_ts"],
            row_values["intake_channel"],
            row_values["case_priority"],
            row_values["case_subject"],
            entity_id,
        )

        existing_entity = entities_by_id.setdefault(entity_id, (entity_name, entity_segment))
        if existing_entity != (entity_name, entity_segment):
            result.error(f"Row {row_number} has inconsistent entity fields for {entity_id}.")

        existing_case = cases_by_ticket_ref.setdefault(ticket_ref, case_tuple)
        if existing_case != case_tuple:
            result.error(f"Row {row_number} has inconsistent ticket fields for {ticket_ref}.")

        try:
            opened_dt = parse_timestamp(row_values["case_opened_ts"], f"row {row_number} case_opened_ts")
            closed_dt = parse_timestamp(row_values["case_closed_ts"], f"row {row_number} case_closed_ts")
            if closed_dt < opened_dt:
                result.error(f"Row {row_number} closes before it opens for ticket {ticket_ref}.")
            else:
                ticket_windows[ticket_ref] = (opened_dt, closed_dt)
        except ValueError as exc:
            result.error(str(exc))

        try:
            occurred_dt = parse_timestamp(row_values["event_occurred_ts"], f"row {row_number} event_occurred_ts")
            if ticket_ref in ticket_windows:
                opened_dt, closed_dt = ticket_windows[ticket_ref]
                if occurred_dt < opened_dt or occurred_dt > closed_dt:
                    result.warn(f"Row {row_number} timestamp falls outside the ticket open/close window for {ticket_ref}.")
        except ValueError as exc:
            result.error(str(exc))

        activity_id = row_values["activity_id"]
        if activity_id in seen_record_ids_by_ticket[ticket_ref]:
            result.error(f"Duplicate activity_id within ticket {ticket_ref}: {activity_id}")
        seen_record_ids_by_ticket[ticket_ref].add(activity_id)

        actor_role = row_values["performed_by_role"]
        if actor_role not in CSV_ALLOWED_ROLES:
            allowed = ", ".join(sorted(CSV_ALLOWED_ROLES))
            result.error(f"Row {row_number} uses unsupported performed_by_role '{actor_role}'. Expected one of: {allowed}.")

        record_count_by_ticket[ticket_ref] += 1

    for ticket_ref in sorted(cases_by_ticket_ref):
        if record_count_by_ticket[ticket_ref] == 0:
            result.error(f"Ticket {ticket_ref} has zero records.")

    result.entity_count = len(entities_by_id)
    result.ticket_count = len(cases_by_ticket_ref)
    result.record_count = sum(record_count_by_ticket.values())


def validate_input(path: Path) -> ValidationResult:
    result = ValidationResult(input_path=str(path))
    if not path.exists():
        result.error("Input file does not exist.")
        return result

    if path.suffix.lower() == ".csv":
        validate_csv(path, result)
        return result

    if path.suffix.lower() == ".json":
        payload = parse_json(path, result)
        if payload is None:
            return result
        detected_format = detect_json_format(payload)
        if detected_format == "raw_json":
            validate_raw_json(path, payload, result)
            return result
        if detected_format == "zendesk_like_json":
            validate_zendesk_like_json(path, payload, result)
            return result
        result.detected_format = detected_format
        result.error("Unsupported JSON export layout for support_v1 contract validation.")
        return result

    result.error(f"Unsupported file type: {path.suffix or '<no extension>'}")
    return result


def write_artifact(results: list[ValidationResult]) -> Path:
    payload = {
        "contract_name": "support_v1_helpdesk_export_contract",
        "generated_at": datetime.now().astimezone().isoformat(),
        "overall_passed": all(result.passed for result in results),
        "inputs": [result.to_dict() for result in results],
    }
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ARTIFACT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return ARTIFACT_PATH


def main(argv: list[str]) -> int:
    input_paths = [Path(argument).resolve() for argument in argv] if argv else list(DEFAULT_INPUT_PATHS)
    results = [validate_input(path) for path in input_paths]
    artifact_path = write_artifact(results)

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{result.input_path} | {status} | warnings={len(result.warnings)} | errors={len(result.errors)}")

    print(f"artifact: {artifact_path}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
