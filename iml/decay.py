from __future__ import annotations

from datetime import datetime

from iml.models import IntuitionProfile, clamp


def apply_decay(profile: IntuitionProfile, now: datetime) -> IntuitionProfile:
    if now <= profile.updated_at:
        return profile

    elapsed_days = (now - profile.updated_at).total_seconds() / 86_400

    freshness_loss = 0.03 * elapsed_days
    profile.freshness = clamp(profile.freshness - freshness_loss)

    total_confidence = 0.0
    total_confidence_loss = 0.0

    for attribute_state in profile.attributes.values():
        previous_confidence = attribute_state.confidence
        confidence_loss = 0.006 * elapsed_days
        attribute_state.confidence = clamp(previous_confidence - confidence_loss)
        total_confidence += attribute_state.confidence
        total_confidence_loss += previous_confidence - attribute_state.confidence

    if profile.attributes:
        profile.overall_confidence = clamp(total_confidence / len(profile.attributes))
        average_confidence_loss = total_confidence_loss / len(profile.attributes)
    else:
        profile.overall_confidence = 0.0
        average_confidence_loss = 0.0

    unknownness_increase = (freshness_loss * 0.35) + (average_confidence_loss * 0.65)
    profile.unknownness = clamp(profile.unknownness + unknownness_increase)

    return profile
