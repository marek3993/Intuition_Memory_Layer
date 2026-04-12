from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


DEFAULT_ATTRIBUTE_NAMES = (
    "trust",
    "stability",
    "predictability",
    "cooperativeness",
    "risk",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


@dataclass
class Event:
    event_id: str
    entity_id: str
    timestamp: datetime
    event_type: str
    source: str
    reliability: float
    polarity: float
    intensity: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceUnit:
    attribute: str
    delta: float
    confidence_delta: float
    reason: str


@dataclass
class AttributeState:
    value: float = 0.50
    confidence: float = 0.20
    evidence_for: int = 0
    evidence_against: int = 0
    last_changed_at: datetime = field(default_factory=utc_now)

    def apply(self, delta: float, confidence_delta: float, changed_at: datetime) -> None:
        old_value = self.value
        self.value = clamp(self.value + delta)
        self.confidence = clamp(self.confidence + confidence_delta)
        if self.value > old_value:
            self.evidence_for += 1
        elif self.value < old_value:
            self.evidence_against += 1
        self.last_changed_at = changed_at


@dataclass
class IntuitionProfile:
    entity_id: str
    attributes: dict[str, AttributeState]
    overall_confidence: float
    contradiction_load: float
    unknownness: float
    freshness: float
    created_at: datetime
    updated_at: datetime
    last_revalidated_at: datetime

    @classmethod
    def new(cls, entity_id: str) -> "IntuitionProfile":
        now = utc_now()
        attributes = {name: AttributeState() for name in DEFAULT_ATTRIBUTE_NAMES}
        return cls(
            entity_id=entity_id,
            attributes=attributes,
            overall_confidence=0.20,
            contradiction_load=0.00,
            unknownness=0.80,
            freshness=1.00,
            created_at=now,
            updated_at=now,
            last_revalidated_at=now,
        )
