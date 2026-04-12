from __future__ import annotations

from dataclasses import dataclass

from iml.models import IntuitionProfile


@dataclass
class DecisionContext:
    stakes: str


@dataclass
class DecisionResult:
    selected_path: str
    reason: str
    confidence_snapshot: float
    freshness_snapshot: float
    contradiction_snapshot: float
    unknownness_snapshot: float


def route_decision(profile: IntuitionProfile, context: DecisionContext) -> DecisionResult:
    meets_confidence = profile.overall_confidence >= 0.55
    meets_freshness = profile.freshness >= 0.60
    meets_contradiction = profile.contradiction_load <= 0.35
    meets_unknownness = profile.unknownness <= 0.45
    is_high_stakes = context.stakes == "high"

    if (
        meets_confidence
        and meets_freshness
        and meets_contradiction
        and meets_unknownness
        and not is_high_stakes
    ):
        selected_path = "fast_path"
        reason = "Profile is confident, fresh, low-contradiction, low-unknown, and stakes are not high."
    else:
        reasons: list[str] = []
        if not meets_confidence:
            reasons.append("overall_confidence below 0.55")
        if not meets_freshness:
            reasons.append("freshness below 0.60")
        if not meets_contradiction:
            reasons.append("contradiction_load above 0.35")
        if not meets_unknownness:
            reasons.append("unknownness above 0.45")
        if is_high_stakes:
            reasons.append("stakes are high")

        selected_path = "deep_path"
        reason = ", ".join(reasons) if reasons else "Defaulted to deep_path."

    return DecisionResult(
        selected_path=selected_path,
        reason=reason,
        confidence_snapshot=profile.overall_confidence,
        freshness_snapshot=profile.freshness,
        contradiction_snapshot=profile.contradiction_load,
        unknownness_snapshot=profile.unknownness,
    )
