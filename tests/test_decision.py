from __future__ import annotations

import unittest

from iml.decision import DecisionContext, route_decision
from iml.models import IntuitionProfile


class RouteDecisionTests(unittest.TestCase):
    def make_profile(
        self,
        *,
        overall_confidence: float = 0.75,
        freshness: float = 0.90,
        contradiction_load: float = 0.10,
        unknownness: float = 0.20,
    ) -> IntuitionProfile:
        profile = IntuitionProfile.new("entity-1")
        profile.overall_confidence = overall_confidence
        profile.freshness = freshness
        profile.contradiction_load = contradiction_load
        profile.unknownness = unknownness
        return profile

    def test_strong_profile_with_low_stakes_uses_fast_path(self) -> None:
        profile = self.make_profile()

        result = route_decision(profile, DecisionContext(stakes="low"))

        self.assertEqual(result.selected_path, "fast_path")

    def test_high_stakes_uses_deep_path(self) -> None:
        profile = self.make_profile()

        result = route_decision(profile, DecisionContext(stakes="high"))

        self.assertEqual(result.selected_path, "deep_path")
        self.assertIn("stakes are high", result.reason)

    def test_low_freshness_uses_deep_path(self) -> None:
        profile = self.make_profile(freshness=0.59)

        result = route_decision(profile, DecisionContext(stakes="low"))

        self.assertEqual(result.selected_path, "deep_path")
        self.assertIn("freshness below 0.60", result.reason)

    def test_low_confidence_uses_deep_path(self) -> None:
        profile = self.make_profile(overall_confidence=0.54)

        result = route_decision(profile, DecisionContext(stakes="low"))

        self.assertEqual(result.selected_path, "deep_path")
        self.assertIn("overall_confidence below 0.55", result.reason)

    def test_high_contradiction_uses_deep_path(self) -> None:
        profile = self.make_profile(contradiction_load=0.36)

        result = route_decision(profile, DecisionContext(stakes="low"))

        self.assertEqual(result.selected_path, "deep_path")
        self.assertIn("contradiction_load above 0.35", result.reason)

    def test_high_unknownness_uses_deep_path(self) -> None:
        profile = self.make_profile(unknownness=0.46)

        result = route_decision(profile, DecisionContext(stakes="low"))

        self.assertEqual(result.selected_path, "deep_path")
        self.assertIn("unknownness above 0.45", result.reason)


if __name__ == "__main__":
    unittest.main()
