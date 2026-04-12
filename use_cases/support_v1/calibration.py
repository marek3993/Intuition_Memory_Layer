from __future__ import annotations

"""Support-specific post-replay calibration for the support_v1 routing flow."""

import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence

from iml.models import Event, IntuitionProfile, clamp


CALIBRATION_NAME = "support_v1_clean_recent_cooperation"
CALIBRATION_VERSION = "v1"


@dataclass(frozen=True)
class SupportV1CalibrationSettings:
    recent_window_days: int
    max_last_event_age_hours: float
    max_contradiction_load: float
    min_recent_positive_events: int
    min_recent_cooperative_events: int
    min_recent_fulfilled_events: int
    min_recent_positive_weight: float
    min_trust: float
    min_cooperativeness: float
    confidence_boost_factor: float
    confidence_boost_cap: float
    unknownness_reduction_factor: float
    unknownness_reduction_cap: float


WINNING_SETTINGS = SupportV1CalibrationSettings(
    recent_window_days=14,
    max_last_event_age_hours=72.0,
    max_contradiction_load=0.05,
    min_recent_positive_events=3,
    min_recent_cooperative_events=2,
    min_recent_fulfilled_events=1,
    min_recent_positive_weight=1.90,
    min_trust=0.60,
    min_cooperativeness=0.55,
    confidence_boost_factor=0.12,
    confidence_boost_cap=0.24,
    unknownness_reduction_factor=0.11,
    unknownness_reduction_cap=0.22,
)


@dataclass(frozen=True)
class SupportV1CalibrationAssessment:
    eligible: bool
    condition_checks: dict[str, bool]
    recent_positive_events: int
    recent_cooperative_events: int
    recent_fulfilled_events: int
    recent_negative_events: int
    recent_inactivity_events: int
    total_contradiction_events: int
    total_long_inactivity_events: int
    recent_positive_weight: float
    last_event_age_hours: float


@dataclass(frozen=True)
class SupportV1CalibrationResult:
    calibration_name: str
    calibration_version: str
    profile: IntuitionProfile
    applied: bool
    confidence_adjustment: float
    unknownness_reduction: float
    assessment: SupportV1CalibrationAssessment


def event_weight(event: Event) -> float:
    return abs(event.polarity) * event.reliability * event.intensity


def assess_clean_history_eligibility(
    profile: IntuitionProfile,
    visible_events: Sequence[Event],
    decision_time: datetime,
    settings: SupportV1CalibrationSettings = WINNING_SETTINGS,
) -> SupportV1CalibrationAssessment:
    recent_threshold = decision_time - timedelta(days=settings.recent_window_days)
    recent_events = [event for event in visible_events if event.timestamp >= recent_threshold]

    recent_positive_events = [event for event in recent_events if event.polarity > 0]
    recent_negative_events = [event for event in recent_events if event.polarity < 0]
    recent_cooperative_events = [
        event
        for event in recent_positive_events
        if event.event_type == "cooperative_response"
    ]
    recent_fulfilled_events = [
        event
        for event in recent_positive_events
        if event.event_type == "fulfilled_commitment"
    ]
    recent_inactivity_events = [
        event for event in recent_events if event.event_type == "long_inactivity"
    ]
    contradiction_events = [
        event
        for event in visible_events
        if event.event_type == "contradiction_detected"
    ]
    long_inactivity_events = [
        event for event in visible_events if event.event_type == "long_inactivity"
    ]

    if visible_events:
        last_event_age_hours = (
            decision_time - visible_events[-1].timestamp
        ).total_seconds() / 3_600
    else:
        last_event_age_hours = float("inf")

    recent_positive_weight = sum(event_weight(event) for event in recent_positive_events)

    condition_checks = {
        "no_contradiction_events": len(contradiction_events) == 0,
        "low_contradiction_load": profile.contradiction_load <= settings.max_contradiction_load,
        "recent_evidence": last_event_age_hours <= settings.max_last_event_age_hours,
        "multiple_recent_positive_events": (
            len(recent_positive_events) >= settings.min_recent_positive_events
        ),
        "multiple_recent_cooperative_events": (
            len(recent_cooperative_events) >= settings.min_recent_cooperative_events
        ),
        "recent_fulfilled_commitment": (
            len(recent_fulfilled_events) >= settings.min_recent_fulfilled_events
        ),
        "no_recent_negative_pressure": len(recent_negative_events) == 0,
        "no_inactivity_pressure": (
            len(long_inactivity_events) == 0 and len(recent_inactivity_events) == 0
        ),
        "supportive_profile_signal": (
            profile.attributes["trust"].value >= settings.min_trust
            and profile.attributes["cooperativeness"].value >= settings.min_cooperativeness
        ),
        "dense_recent_positive_weight": (
            recent_positive_weight >= settings.min_recent_positive_weight
        ),
    }

    return SupportV1CalibrationAssessment(
        eligible=all(condition_checks.values()),
        condition_checks=condition_checks,
        recent_positive_events=len(recent_positive_events),
        recent_cooperative_events=len(recent_cooperative_events),
        recent_fulfilled_events=len(recent_fulfilled_events),
        recent_negative_events=len(recent_negative_events),
        recent_inactivity_events=len(recent_inactivity_events),
        total_contradiction_events=len(contradiction_events),
        total_long_inactivity_events=len(long_inactivity_events),
        recent_positive_weight=recent_positive_weight,
        last_event_age_hours=last_event_age_hours,
    )


def is_support_v1_clean_history_eligible(
    profile: IntuitionProfile,
    visible_events: Sequence[Event],
    decision_time: datetime,
    settings: SupportV1CalibrationSettings = WINNING_SETTINGS,
) -> bool:
    """Return whether the explicit support_v1 clean-history rule passes."""

    assessment = assess_clean_history_eligibility(
        profile=profile,
        visible_events=visible_events,
        decision_time=decision_time,
        settings=settings,
    )
    return assessment.eligible


def apply_support_v1_calibration(
    profile: IntuitionProfile,
    visible_events: Sequence[Event],
    decision_time: datetime,
    settings: SupportV1CalibrationSettings = WINNING_SETTINGS,
) -> SupportV1CalibrationResult:
    assessment = assess_clean_history_eligibility(
        profile=profile,
        visible_events=visible_events,
        decision_time=decision_time,
        settings=settings,
    )
    calibrated_profile = copy.deepcopy(profile)

    if not assessment.eligible:
        return SupportV1CalibrationResult(
            calibration_name=CALIBRATION_NAME,
            calibration_version=CALIBRATION_VERSION,
            profile=calibrated_profile,
            applied=False,
            confidence_adjustment=0.0,
            unknownness_reduction=0.0,
            assessment=assessment,
        )

    confidence_adjustment = min(
        settings.confidence_boost_cap,
        assessment.recent_positive_weight * settings.confidence_boost_factor,
    )
    unknownness_reduction = min(
        settings.unknownness_reduction_cap,
        assessment.recent_positive_weight * settings.unknownness_reduction_factor,
    )

    calibrated_profile.overall_confidence = clamp(
        calibrated_profile.overall_confidence + confidence_adjustment
    )
    calibrated_profile.unknownness = clamp(
        calibrated_profile.unknownness - unknownness_reduction
    )

    return SupportV1CalibrationResult(
        calibration_name=CALIBRATION_NAME,
        calibration_version=CALIBRATION_VERSION,
        profile=calibrated_profile,
        applied=True,
        confidence_adjustment=confidence_adjustment,
        unknownness_reduction=unknownness_reduction,
        assessment=assessment,
    )
