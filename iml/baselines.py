from __future__ import annotations

from iml.models import Event, clamp


FAST_PATH_CONFIDENCE_THRESHOLD = 0.55
FAST_PATH_CONTRADICTION_THRESHOLD = 0.35
FAST_PATH_UNKNOWNNESS_THRESHOLD = 0.45
FAST_PATH_RISK_THRESHOLD = 0.55


def _average(values: list[float]) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)


def _event_weight(event: Event) -> float:
    return event.reliability * event.intensity


def _route_baseline(
    *,
    overall_confidence: float,
    contradiction_load: float,
    unknownness: float,
    risk: float,
) -> tuple[str, str]:
    meets_confidence = overall_confidence >= FAST_PATH_CONFIDENCE_THRESHOLD
    meets_contradiction = contradiction_load <= FAST_PATH_CONTRADICTION_THRESHOLD
    meets_unknownness = unknownness <= FAST_PATH_UNKNOWNNESS_THRESHOLD
    meets_risk = risk <= FAST_PATH_RISK_THRESHOLD

    if meets_confidence and meets_contradiction and meets_unknownness and meets_risk:
        return (
            "fast_path",
            "Baseline score is confident, low-risk, low-contradiction, and low-unknown.",
        )

    reasons: list[str] = []
    if not meets_confidence:
        reasons.append("overall_confidence below 0.55")
    if not meets_contradiction:
        reasons.append("contradiction_load above 0.35")
    if not meets_unknownness:
        reasons.append("unknownness above 0.45")
    if not meets_risk:
        reasons.append("risk above 0.55")

    return "deep_path", ", ".join(reasons)


def run_naive_summary_baseline(events: list[Event]) -> dict[str, float | str]:
    if not events:
        return {
            "trust": 0.50,
            "risk": 0.50,
            "contradiction_load": 0.00,
            "overall_confidence": 0.00,
            "unknownness": 1.00,
            "selected_path": "deep_path",
            "decision_reason": "No events available for summary baseline.",
        }

    total_events = len(events)
    positive_events = sum(1 for event in events if event.polarity > 0)
    negative_events = sum(1 for event in events if event.polarity < 0)
    contradiction_events = sum(
        1 for event in events if event.event_type == "contradiction_detected"
    )
    ignored_requests = sum(1 for event in events if event.event_type == "ignored_request")
    inactivity_events = sum(1 for event in events if event.event_type == "long_inactivity")

    positive_ratio = positive_events / total_events
    negative_ratio = negative_events / total_events
    contradiction_ratio = contradiction_events / total_events
    ignored_ratio = ignored_requests / total_events
    inactivity_ratio = inactivity_events / total_events

    average_reliability = _average([event.reliability for event in events])
    evidence_coverage = min(total_events / 8.0, 1.0)
    directionality = abs(positive_ratio - negative_ratio)
    last_event_negative = 1.0 if events[-1].polarity < 0 else 0.0
    last_event_inactive = 1.0 if events[-1].event_type == "long_inactivity" else 0.0

    trust = clamp(
        0.50
        + (0.30 * positive_ratio)
        - (0.35 * negative_ratio)
        - (0.15 * contradiction_ratio)
        + (0.05 * average_reliability)
    )
    risk = clamp(
        0.20
        + (0.35 * negative_ratio)
        + (0.30 * contradiction_ratio)
        + (0.20 * ignored_ratio)
        + (0.10 * inactivity_ratio)
        + (0.15 * last_event_negative)
        + (0.05 * last_event_inactive)
        - (0.10 * positive_ratio)
    )
    contradiction_load = clamp((0.80 * contradiction_ratio) + (0.10 * negative_ratio))
    overall_confidence = clamp(
        0.20
        + (0.35 * evidence_coverage)
        + (0.20 * average_reliability)
        + (0.15 * directionality)
        - (0.20 * contradiction_ratio)
        - (0.10 * inactivity_ratio)
        - (0.10 * last_event_negative)
    )
    unknownness = clamp(
        (1.0 - overall_confidence)
        + (0.10 * (1.0 - evidence_coverage))
        + (0.08 * last_event_inactive)
    )

    selected_path, decision_reason = _route_baseline(
        overall_confidence=overall_confidence,
        contradiction_load=contradiction_load,
        unknownness=unknownness,
        risk=risk,
    )

    return {
        "trust": trust,
        "risk": risk,
        "contradiction_load": contradiction_load,
        "overall_confidence": overall_confidence,
        "unknownness": unknownness,
        "selected_path": selected_path,
        "decision_reason": decision_reason,
    }


def run_full_history_baseline(events: list[Event]) -> dict[str, float | str]:
    if not events:
        return {
            "trust": 0.50,
            "risk": 0.50,
            "contradiction_load": 0.00,
            "overall_confidence": 0.00,
            "unknownness": 1.00,
            "selected_path": "deep_path",
            "decision_reason": "No events available for full-history baseline.",
        }

    positive_weight = 0.0
    negative_weight = 0.0
    contradiction_weight = 0.0
    ignored_weight = 0.0
    inactivity_weight = 0.0

    for event in events:
        weight = _event_weight(event)
        signed_weight = abs(event.polarity) * weight

        if event.polarity > 0:
            positive_weight += signed_weight
        elif event.polarity < 0:
            negative_weight += signed_weight

        if event.event_type == "contradiction_detected":
            contradiction_weight += signed_weight
        if event.event_type == "ignored_request":
            ignored_weight += signed_weight
        if event.event_type == "long_inactivity":
            inactivity_weight += signed_weight

    total_weight = positive_weight + negative_weight
    if total_weight == 0.0:
        total_weight = 1.0

    support_ratio = positive_weight / total_weight
    pressure_ratio = negative_weight / total_weight
    contradiction_ratio = contradiction_weight / total_weight
    ignored_ratio = ignored_weight / total_weight
    inactivity_ratio = inactivity_weight / total_weight
    balance_ratio = abs(positive_weight - negative_weight) / total_weight
    average_reliability = _average([event.reliability for event in events])
    volume_score = min(total_weight / 9.0, 1.0)
    last_event_negative = 1.0 if events[-1].polarity < 0 else 0.0
    last_event_inactive = 1.0 if events[-1].event_type == "long_inactivity" else 0.0

    trust = clamp(
        0.50
        + (0.40 * (support_ratio - pressure_ratio))
        - (0.20 * contradiction_ratio)
        + (0.05 * average_reliability)
    )
    risk = clamp(
        0.18
        + (0.45 * pressure_ratio)
        + (0.30 * contradiction_ratio)
        + (0.15 * ignored_ratio)
        + (0.10 * inactivity_ratio)
        + (0.12 * last_event_negative)
        - (0.12 * support_ratio)
    )
    contradiction_load = clamp((0.85 * contradiction_ratio) + (0.15 * pressure_ratio))
    overall_confidence = clamp(
        0.15
        + (0.45 * volume_score)
        + (0.20 * average_reliability)
        + (0.15 * (1.0 - contradiction_ratio))
        + (0.10 * balance_ratio)
        - (0.15 * inactivity_ratio)
        - (0.08 * last_event_negative)
    )
    unknownness = clamp(
        (1.0 - overall_confidence)
        + (0.12 * (1.0 - volume_score))
        + (0.10 * last_event_inactive)
    )

    selected_path, decision_reason = _route_baseline(
        overall_confidence=overall_confidence,
        contradiction_load=contradiction_load,
        unknownness=unknownness,
        risk=risk,
    )

    return {
        "trust": trust,
        "risk": risk,
        "contradiction_load": contradiction_load,
        "overall_confidence": overall_confidence,
        "unknownness": unknownness,
        "selected_path": selected_path,
        "decision_reason": decision_reason,
    }
