from __future__ import annotations

from datetime import datetime, timedelta, timezone

from iml.decay import apply_decay
from iml.decision import DecisionContext, route_decision
from iml.explain import format_decision_result, format_evidence, format_profile
from iml.extractor import extract_evidence
from iml.models import Event, IntuitionProfile
from iml.revalidate import RevalidationResult, revalidate_profile
from iml.update_engine import apply_event


DEMO_TITLE = "IML MVP Demo"
DEMO_ENTITY_ID = "user_1"
DEMO_SOURCE = "demo"
DECAY_DAYS = 35


def print_block(text: str) -> None:
    print()
    print(text)


def print_profile_snapshot(profile: IntuitionProfile, title: str) -> None:
    print_block(format_profile(profile, title=title))


def print_event_header(index: int, event: Event) -> None:
    print()
    print(f"--- Event {index}: {event.event_type} ({event.event_id}) ---")


def build_demo_events(started_at: datetime) -> list[Event]:
    event_specs = [
        (
            "evt_001",
            0,
            "fulfilled_commitment",
            0.90,
            1.0,
            {"note": "User did what they promised"},
        ),
        (
            "evt_002",
            5,
            "cooperative_response",
            0.95,
            1.0,
            {"note": "User responded cooperatively"},
        ),
        (
            "evt_003",
            10,
            "contradiction_detected",
            0.80,
            -1.0,
            {"note": "User contradicted earlier statement"},
        ),
    ]
    return [
        Event(
            event_id=event_id,
            entity_id=DEMO_ENTITY_ID,
            timestamp=started_at + timedelta(minutes=minute_offset),
            event_type=event_type,
            source=DEMO_SOURCE,
            reliability=reliability,
            polarity=polarity,
            intensity=1.0,
            metadata=metadata,
        )
        for event_id, minute_offset, event_type, reliability, polarity, metadata in event_specs
    ]


def replay_events(profile: IntuitionProfile, events: list[Event]) -> IntuitionProfile:
    for index, event in enumerate(events, start=1):
        print_event_header(index, event)
        evidence_units = extract_evidence(event)
        print(format_evidence(event, evidence_units))
        profile = apply_event(profile, event)
        print_profile_snapshot(profile, title=f"Profile After Event {index}")
    return profile


def apply_demo_decay(profile: IntuitionProfile, days: int) -> tuple[IntuitionProfile, datetime]:
    decay_time = profile.updated_at + timedelta(days=days)
    profile = apply_decay(profile, now=decay_time)
    print_profile_snapshot(profile, title=f"Profile After {days}-Day Decay")
    return profile, decay_time


def print_revalidation_summary(profile: IntuitionProfile, result: RevalidationResult) -> None:
    reasons = ", ".join(result.reasons) if result.reasons else "none"
    print()
    print(f"Revalidation triggered: {result.triggered}")
    print(f"Revalidation reasons: {reasons}")
    print_profile_snapshot(profile, title="Profile After Revalidation")


def print_decision(profile: IntuitionProfile, stakes: str, title: str) -> None:
    result = route_decision(profile, DecisionContext(stakes=stakes))
    print_block(format_decision_result(result, title=title))


def main() -> None:
    profile = IntuitionProfile.new(entity_id=DEMO_ENTITY_ID)
    demo_start = datetime.now(timezone.utc)

    print(DEMO_TITLE)
    print_profile_snapshot(profile, title="Initial Profile")

    profile = replay_events(profile, build_demo_events(demo_start))
    profile, demo_time = apply_demo_decay(profile, days=DECAY_DAYS)

    revalidation_result = revalidate_profile(profile, now=demo_time)
    print_revalidation_summary(profile, revalidation_result)

    print_decision(profile, stakes="low", title="Decision Routing (Low Stakes)")
    print_decision(profile, stakes="high", title="Decision Routing (High Stakes)")


if __name__ == "__main__":
    main()
