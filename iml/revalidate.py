from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from iml.models import IntuitionProfile, clamp

FRESHNESS_THRESHOLD = 0.50
CONFIDENCE_THRESHOLD = 0.40
CONTRADICTION_THRESHOLD = 0.30
UNKNOWNNESS_THRESHOLD = 0.60
STALE_DAYS_THRESHOLD = 30

CONTRADICTION_REDUCTION = 0.08
FRESHNESS_IMPROVEMENT = 0.18
FRESHNESS_CAP = 0.70
CONFIDENCE_IMPROVEMENT = 0.08
UNKNOWNNESS_REDUCTION = 0.10


@dataclass
class RevalidationResult:
    triggered: bool
    reasons: list[str]
    confidence_before: float
    confidence_after: float
    freshness_before: float
    freshness_after: float
    unknownness_before: float
    unknownness_after: float


def should_revalidate(profile: IntuitionProfile, now: datetime) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if profile.freshness < FRESHNESS_THRESHOLD:
        reasons.append("freshness_below_threshold")
    if profile.overall_confidence < CONFIDENCE_THRESHOLD:
        reasons.append("confidence_below_threshold")
    if profile.contradiction_load > CONTRADICTION_THRESHOLD:
        reasons.append("contradiction_load_above_threshold")
    if profile.unknownness > UNKNOWNNESS_THRESHOLD:
        reasons.append("unknownness_above_threshold")

    elapsed_days = (now - profile.updated_at).total_seconds() / 86_400
    if elapsed_days > STALE_DAYS_THRESHOLD:
        reasons.append("stale_since_last_update")

    return bool(reasons), reasons


def revalidate_profile(profile: IntuitionProfile, now: datetime) -> RevalidationResult:
    triggered, reasons = should_revalidate(profile, now)

    confidence_before = profile.overall_confidence
    freshness_before = profile.freshness
    unknownness_before = profile.unknownness

    if not triggered:
        return RevalidationResult(
            triggered=False,
            reasons=reasons,
            confidence_before=confidence_before,
            confidence_after=confidence_before,
            freshness_before=freshness_before,
            freshness_after=freshness_before,
            unknownness_before=unknownness_before,
            unknownness_after=unknownness_before,
        )

    profile.contradiction_load = clamp(profile.contradiction_load - CONTRADICTION_REDUCTION)
    profile.freshness = clamp(min(FRESHNESS_CAP, profile.freshness + FRESHNESS_IMPROVEMENT))

    if profile.contradiction_load <= CONTRADICTION_THRESHOLD:
        profile.overall_confidence = clamp(
            profile.overall_confidence + CONFIDENCE_IMPROVEMENT
        )

    profile.unknownness = clamp(profile.unknownness - UNKNOWNNESS_REDUCTION)
    profile.last_revalidated_at = now

    return RevalidationResult(
        triggered=True,
        reasons=reasons,
        confidence_before=confidence_before,
        confidence_after=profile.overall_confidence,
        freshness_before=freshness_before,
        freshness_after=profile.freshness,
        unknownness_before=unknownness_before,
        unknownness_after=profile.unknownness,
    )
