from __future__ import annotations

import unittest
from datetime import timedelta

from iml.models import Event, IntuitionProfile
from iml.update_engine import apply_event


class ApplyEventTests(unittest.TestCase):
    def make_profile(self, entity_id: str = "entity-1") -> IntuitionProfile:
        return IntuitionProfile.new(entity_id)

    def make_event(
        self,
        event_type: str,
        *,
        entity_id: str = "entity-1",
        base_timestamp=None,
        timestamp_offset_seconds: int = 60,
        reliability: float = 1.0,
        intensity: float = 1.0,
    ) -> Event:
        if base_timestamp is None:
            base_timestamp = IntuitionProfile.new(entity_id).updated_at
        timestamp = base_timestamp + timedelta(seconds=timestamp_offset_seconds)
        return Event(
            event_id=f"evt-{event_type}",
            entity_id=entity_id,
            timestamp=timestamp,
            event_type=event_type,
            source="test-suite",
            reliability=reliability,
            polarity=1.0,
            intensity=intensity,
        )

    def test_fulfilled_commitment_increases_trust(self) -> None:
        profile = self.make_profile()
        event = self.make_event(
            "fulfilled_commitment",
            entity_id=profile.entity_id,
            base_timestamp=profile.updated_at,
        )
        before_trust = profile.attributes["trust"].value

        apply_event(profile, event)

        self.assertGreater(profile.attributes["trust"].value, before_trust)

    def test_fulfilled_commitment_increases_stability(self) -> None:
        profile = self.make_profile()
        event = self.make_event(
            "fulfilled_commitment",
            entity_id=profile.entity_id,
            base_timestamp=profile.updated_at,
        )
        before_stability = profile.attributes["stability"].value

        apply_event(profile, event)

        self.assertGreater(profile.attributes["stability"].value, before_stability)

    def test_cooperative_response_increases_cooperativeness(self) -> None:
        profile = self.make_profile()
        event = self.make_event(
            "cooperative_response",
            entity_id=profile.entity_id,
            base_timestamp=profile.updated_at,
        )
        before_cooperativeness = profile.attributes["cooperativeness"].value

        apply_event(profile, event)

        self.assertGreater(profile.attributes["cooperativeness"].value, before_cooperativeness)

    def test_contradiction_detected_lowers_predictability(self) -> None:
        profile = self.make_profile()
        event = self.make_event(
            "contradiction_detected",
            entity_id=profile.entity_id,
            base_timestamp=profile.updated_at,
        )
        before_predictability = profile.attributes["predictability"].value

        apply_event(profile, event)

        self.assertLess(profile.attributes["predictability"].value, before_predictability)

    def test_contradiction_detected_increases_risk(self) -> None:
        profile = self.make_profile()
        event = self.make_event(
            "contradiction_detected",
            entity_id=profile.entity_id,
            base_timestamp=profile.updated_at,
        )
        before_risk = profile.attributes["risk"].value

        apply_event(profile, event)

        self.assertGreater(profile.attributes["risk"].value, before_risk)

    def test_contradiction_detected_increases_contradiction_load(self) -> None:
        profile = self.make_profile()
        event = self.make_event(
            "contradiction_detected",
            entity_id=profile.entity_id,
            base_timestamp=profile.updated_at,
        )
        before_contradiction_load = profile.contradiction_load

        apply_event(profile, event)

        self.assertGreater(profile.contradiction_load, before_contradiction_load)

    def test_overall_confidence_changes_after_applying_event(self) -> None:
        profile = self.make_profile()
        event = self.make_event(
            "fulfilled_commitment",
            entity_id=profile.entity_id,
            base_timestamp=profile.updated_at,
        )
        before_overall_confidence = profile.overall_confidence

        apply_event(profile, event)

        self.assertNotEqual(profile.overall_confidence, before_overall_confidence)

    def test_wrong_entity_id_raises_value_error(self) -> None:
        profile = self.make_profile(entity_id="entity-1")
        event = self.make_event("fulfilled_commitment", entity_id="entity-2")

        with self.assertRaises(ValueError):
            apply_event(profile, event)


if __name__ == "__main__":
    unittest.main()
