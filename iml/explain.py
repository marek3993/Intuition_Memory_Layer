from __future__ import annotations

from typing import TYPE_CHECKING

from iml.models import DEFAULT_ATTRIBUTE_NAMES, Event, EvidenceUnit, IntuitionProfile

if TYPE_CHECKING:
    from iml.decision import DecisionResult


ATTRIBUTE_DISPLAY_ORDER = DEFAULT_ATTRIBUTE_NAMES


def _format_float(value: float) -> str:
    return f"{value:.2f}"


def _format_delta(value: float) -> str:
    return f"{value:+.3f}"


def _ordered_attribute_names(profile: IntuitionProfile) -> list[str]:
    ordered_names = [name for name in ATTRIBUTE_DISPLAY_ORDER if name in profile.attributes]
    remaining_names = sorted(name for name in profile.attributes if name not in ordered_names)
    return ordered_names + remaining_names


def format_profile(profile: IntuitionProfile, title: str | None = None) -> str:
    lines = [f"=== {title or 'Profile Snapshot'} ==="]
    lines.append(f"entity_id: {profile.entity_id}")
    lines.append(f"overall_confidence: {_format_float(profile.overall_confidence)}")
    lines.append(f"unknownness: {_format_float(profile.unknownness)}")
    lines.append(f"freshness: {_format_float(profile.freshness)}")
    lines.append(f"contradiction_load: {_format_float(profile.contradiction_load)}")
    lines.append(f"last_revalidated_at: {profile.last_revalidated_at.isoformat()}")
    lines.append("attributes:")

    for attribute_name in _ordered_attribute_names(profile):
        attribute_state = profile.attributes[attribute_name]
        lines.append(
            (
                f"- {attribute_name}: value={_format_float(attribute_state.value)}, "
                f"confidence={_format_float(attribute_state.confidence)}, "
                f"for={attribute_state.evidence_for}, "
                f"against={attribute_state.evidence_against}"
            )
        )

    lines.append(f"updated_at: {profile.updated_at.isoformat()}")
    return "\n".join(lines)


def format_evidence(event: Event, evidence_units: list[EvidenceUnit]) -> str:
    lines = ["=== Extracted Evidence ==="]
    lines.append(f"event: {event.event_type} ({event.event_id})")
    lines.append(f"entity_id: {event.entity_id}")
    lines.append(f"timestamp: {event.timestamp.isoformat()}")
    lines.append(f"source: {event.source}")
    lines.append(f"reliability: {_format_float(event.reliability)}")
    lines.append(f"polarity: {_format_float(event.polarity)}")
    lines.append(f"intensity: {_format_float(event.intensity)}")

    note = event.metadata.get("note")
    if note:
        lines.append(f"note: {note}")

    lines.append("evidence:")
    if evidence_units:
        for unit in evidence_units:
            lines.append(
                (
                    f"- {unit.attribute}: delta={_format_delta(unit.delta)}, "
                    f"confidence_delta={_format_delta(unit.confidence_delta)}, "
                    f"reason={unit.reason}"
                )
            )
    else:
        lines.append("- none")

    return "\n".join(lines)


def format_decision_result(result: "DecisionResult", title: str | None = None) -> str:
    lines = [f"=== {title or 'Decision Result'} ==="]
    lines.append(f"selected_path: {result.selected_path}")
    lines.append(f"reason: {result.reason}")
    lines.append(f"confidence_snapshot: {_format_float(result.confidence_snapshot)}")
    lines.append(f"freshness_snapshot: {_format_float(result.freshness_snapshot)}")
    lines.append(f"contradiction_snapshot: {_format_float(result.contradiction_snapshot)}")
    lines.append(f"unknownness_snapshot: {_format_float(result.unknownness_snapshot)}")
    return "\n".join(lines)
