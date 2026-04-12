from __future__ import annotations

import unittest
from datetime import timedelta

from iml.models import IntuitionProfile
from iml.revalidate import revalidate_profile, should_revalidate


class RevalidateProfileTests(unittest.TestCase):
    def make_profile(self) -> IntuitionProfile:
        return IntuitionProfile.new("entity-1")

    def test_should_not_revalidate_when_profile_is_still_healthy(self) -> None:
        profile = self.make_profile()
        profile.overall_confidence = 0.75
        profile.freshness = 0.90
        profile.contradiction_load = 0.10
        profile.unknownness = 0.20

        triggered, reasons = should_revalidate(profile, profile.updated_at + timedelta(days=5))

        self.assertFalse(triggered)
        self.assertEqual(reasons, [])

    def test_should_revalidate_when_profile_is_stale(self) -> None:
        profile = self.make_profile()

        triggered, reasons = should_revalidate(profile, profile.updated_at + timedelta(days=31))

        self.assertTrue(triggered)
        self.assertIn("stale_since_last_update", reasons)

    def test_revalidation_updates_fields_but_preserves_updated_at(self) -> None:
        profile = self.make_profile()
        profile.overall_confidence = 0.35
        profile.freshness = 0.42
        profile.contradiction_load = 0.28
        profile.unknownness = 0.72

        original_updated_at = profile.updated_at
        revalidation_time = profile.updated_at + timedelta(days=35)

        result = revalidate_profile(profile, revalidation_time)

        self.assertTrue(result.triggered)
        self.assertLess(profile.unknownness, 0.72)
        self.assertGreater(profile.freshness, 0.42)
        self.assertGreater(profile.overall_confidence, 0.35)
        self.assertEqual(profile.updated_at, original_updated_at)
        self.assertEqual(profile.last_revalidated_at, revalidation_time)

    def test_revalidation_caps_freshness_at_point_seven_zero(self) -> None:
        profile = self.make_profile()
        profile.freshness = 0.69
        profile.overall_confidence = 0.80
        profile.contradiction_load = 0.10
        profile.unknownness = 0.70

        revalidate_profile(profile, profile.updated_at + timedelta(days=1))

        self.assertEqual(profile.freshness, 0.70)


if __name__ == "__main__":
    unittest.main()
