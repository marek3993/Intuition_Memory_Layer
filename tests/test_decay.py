from __future__ import annotations

import unittest
from datetime import timedelta

from iml.decay import apply_decay
from iml.models import IntuitionProfile


class ApplyDecayTests(unittest.TestCase):
    def make_profile(self) -> IntuitionProfile:
        return IntuitionProfile.new("entity-1")

    def test_no_decay_is_applied_when_now_is_not_after_updated_at(self) -> None:
        profile = self.make_profile()
        before_freshness = profile.freshness
        before_unknownness = profile.unknownness
        before_overall_confidence = profile.overall_confidence
        before_confidences = {
            name: state.confidence for name, state in profile.attributes.items()
        }
        before_updated_at = profile.updated_at

        apply_decay(profile, profile.updated_at)

        self.assertEqual(profile.freshness, before_freshness)
        self.assertEqual(profile.unknownness, before_unknownness)
        self.assertEqual(profile.overall_confidence, before_overall_confidence)
        self.assertEqual(profile.updated_at, before_updated_at)
        self.assertEqual(
            {name: state.confidence for name, state in profile.attributes.items()},
            before_confidences,
        )

    def test_freshness_decreases_after_time_passes(self) -> None:
        profile = self.make_profile()
        later = profile.updated_at + timedelta(days=5)
        before_freshness = profile.freshness

        apply_decay(profile, later)

        self.assertLess(profile.freshness, before_freshness)

    def test_attribute_confidence_decreases_slightly_after_time_passes(self) -> None:
        profile = self.make_profile()
        later = profile.updated_at + timedelta(days=3)
        before_trust_confidence = profile.attributes["trust"].confidence

        apply_decay(profile, later)

        self.assertLess(profile.attributes["trust"].confidence, before_trust_confidence)
        self.assertGreater(profile.attributes["trust"].confidence, 0.0)

    def test_unknownness_increases_after_decay(self) -> None:
        profile = self.make_profile()
        later = profile.updated_at + timedelta(days=4)
        before_unknownness = profile.unknownness

        apply_decay(profile, later)

        self.assertGreater(profile.unknownness, before_unknownness)

    def test_overall_confidence_is_recomputed_after_decay(self) -> None:
        profile = self.make_profile()
        later = profile.updated_at + timedelta(days=2)
        before_overall_confidence = profile.overall_confidence

        apply_decay(profile, later)

        expected_overall_confidence = sum(
            state.confidence for state in profile.attributes.values()
        ) / len(profile.attributes)

        self.assertNotEqual(profile.overall_confidence, before_overall_confidence)
        self.assertAlmostEqual(profile.overall_confidence, expected_overall_confidence)

    def test_all_values_stay_in_range_zero_to_one(self) -> None:
        profile = self.make_profile()
        much_later = profile.updated_at + timedelta(days=10_000)

        apply_decay(profile, much_later)

        self.assertGreaterEqual(profile.freshness, 0.0)
        self.assertLessEqual(profile.freshness, 1.0)
        self.assertGreaterEqual(profile.overall_confidence, 0.0)
        self.assertLessEqual(profile.overall_confidence, 1.0)
        self.assertGreaterEqual(profile.unknownness, 0.0)
        self.assertLessEqual(profile.unknownness, 1.0)

        for attribute_state in profile.attributes.values():
            self.assertGreaterEqual(attribute_state.value, 0.0)
            self.assertLessEqual(attribute_state.value, 1.0)
            self.assertGreaterEqual(attribute_state.confidence, 0.0)
            self.assertLessEqual(attribute_state.confidence, 1.0)

    def test_profile_updated_at_remains_unchanged_after_passive_decay(self) -> None:
        profile = self.make_profile()
        original_updated_at = profile.updated_at
        later = original_updated_at + timedelta(days=7)

        apply_decay(profile, later)

        self.assertEqual(profile.updated_at, original_updated_at)


if __name__ == "__main__":
    unittest.main()
