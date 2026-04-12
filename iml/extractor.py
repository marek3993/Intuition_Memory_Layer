from __future__ import annotations

from iml.models import EvidenceUnit, Event


EVENT_TYPE_TO_EVIDENCE: dict[str, list[tuple[str, float, float, str]]] = {
    "fulfilled_commitment": [
        ("trust", 0.12, 0.06, "Entity fulfilled a commitment"),
        ("stability", 0.08, 0.04, "Entity behavior supports stability"),
        ("predictability", 0.05, 0.03, "Entity acted as expected"),
    ],
    "contradiction_detected": [
        ("predictability", -0.15, 0.07, "Contradictory behavior detected"),
        ("risk", 0.10, 0.05, "Contradiction increases perceived risk"),
    ],
    "cooperative_response": [
        ("cooperativeness", 0.10, 0.05, "Entity responded cooperatively"),
        ("trust", 0.04, 0.02, "Cooperative response slightly improves trust"),
    ],
    "ignored_request": [
        ("cooperativeness", -0.10, 0.05, "Entity ignored a request"),
        ("trust", -0.05, 0.03, "Ignored request slightly reduces trust"),
    ],
    "long_inactivity": [
        ("stability", -0.03, 0.01, "Long inactivity reduces certainty about stability"),
    ],
}


def extract_evidence(event: Event) -> list[EvidenceUnit]:
    templates = EVENT_TYPE_TO_EVIDENCE.get(event.event_type, [])
    evidence_units: list[EvidenceUnit] = []

    for attribute, base_delta, base_confidence_delta, reason in templates:
        scaled_delta = base_delta * event.reliability * event.intensity
        scaled_confidence_delta = base_confidence_delta * event.reliability

        evidence_units.append(
            EvidenceUnit(
                attribute=attribute,
                delta=scaled_delta,
                confidence_delta=scaled_confidence_delta,
                reason=reason,
            )
        )

    return evidence_units
