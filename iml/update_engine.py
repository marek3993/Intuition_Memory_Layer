from __future__ import annotations

from iml.extractor import extract_evidence
from iml.models import Event, IntuitionProfile, clamp


def apply_event(profile: IntuitionProfile, event: Event) -> IntuitionProfile:
    if profile.entity_id != event.entity_id:
        raise ValueError(
            f"Entity mismatch: profile.entity_id={profile.entity_id}, event.entity_id={event.entity_id}"
        )

    for unit in extract_evidence(event):
        attribute_state = profile.attributes.get(unit.attribute)
        if attribute_state is None:
            continue
        attribute_state.apply(
            delta=unit.delta,
            confidence_delta=unit.confidence_delta,
            changed_at=event.timestamp,
        )

    if event.event_type == "contradiction_detected":
        profile.contradiction_load = clamp(
            profile.contradiction_load + (0.18 * event.reliability * event.intensity)
        )
    else:
        profile.contradiction_load = clamp(profile.contradiction_load * 0.97)

    total_confidence = sum(attr.confidence for attr in profile.attributes.values())
    profile.overall_confidence = clamp(total_confidence / len(profile.attributes))
    profile.unknownness = clamp(1.0 - profile.overall_confidence)
    profile.freshness = 1.0
    profile.updated_at = event.timestamp

    return profile
