from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from convert_support_cases_to_events import (
    EVENTS_ARTIFACT_PATH,
    SOURCE_PATH,
    convert_cases_to_entity_event_payload,
    export_events,
    load_support_cases,
)
from calibration import (
    CALIBRATION_NAME,
    CALIBRATION_VERSION,
    WINNING_SETTINGS,
    apply_support_v1_calibration,
)
from iml.decay import apply_decay
from iml.decision import DecisionContext, route_decision
from iml.models import Event, IntuitionProfile
from iml.revalidate import revalidate_profile
from iml.update_engine import apply_event


DATASET_PATH = SOURCE_PATH
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
EVALUATION_ARTIFACT_PATH = ARTIFACTS_DIR / "latest_support_evaluation.json"
DECAY_GAP_DAYS = 21
FINAL_DECISION_GAP_DAYS = 7
EVALUATION_STAKES = "low"


@dataclass(frozen=True)
class SupportEntitySummary:
    entity_id: str
    account_name: str
    segment: str
    case_count: int
    event_count: int
    decay_checkpoints: int
    event_type_counts: dict[str, int]
    route_after_optional_calibration: str
    route_reason_after_optional_calibration: str
    trust: float
    cooperativeness: float
    predictability: float
    stability: float
    risk: float
    overall_confidence: float
    unknownness: float
    freshness: float
    contradiction_load: float
    revalidation_triggered: bool
    revalidation_reasons: tuple[str, ...]
    calibration_applied: bool
    confidence_adjustment: float
    unknownness_reduction: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay support_v1 entities through the generic IML pipeline, with "
            "optional support-specific calibration applied after replay and before routing."
        )
    )
    parser.add_argument(
        "--calibrated",
        action="store_true",
        help="Apply the support_v1 clean-history calibration before final routing.",
    )
    return parser.parse_args()


def parse_timestamp(raw_timestamp: str) -> datetime:
    return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))


def build_event(raw_event: dict[str, Any]) -> Event:
    return Event(
        event_id=str(raw_event["event_id"]),
        entity_id=str(raw_event["entity_id"]),
        timestamp=parse_timestamp(str(raw_event["timestamp"])),
        event_type=str(raw_event["event_type"]),
        source=str(raw_event["source"]),
        reliability=float(raw_event["reliability"]),
        polarity=float(raw_event["polarity"]),
        intensity=float(raw_event["intensity"]),
        metadata=dict(raw_event.get("metadata", {})),
    )


def make_profile(entity_id: str, start_time: datetime) -> IntuitionProfile:
    profile = IntuitionProfile.new(entity_id)
    profile.created_at = start_time
    profile.updated_at = start_time
    profile.last_revalidated_at = start_time

    for attribute_state in profile.attributes.values():
        attribute_state.last_changed_at = start_time

    return profile


def maybe_apply_gap_decay(profile: IntuitionProfile, next_timestamp: datetime) -> bool:
    elapsed_days = (next_timestamp - profile.updated_at).total_seconds() / 86_400
    if elapsed_days < DECAY_GAP_DAYS:
        return False

    apply_decay(profile, now=next_timestamp)
    return True


def summarize_entity(
    entity_payload: dict[str, Any],
    use_calibration: bool,
) -> SupportEntitySummary:
    events = [
        build_event(raw_event)
        for raw_event in sorted(
            entity_payload["events"],
            key=lambda item: (item["timestamp"], item["event_id"]),
        )
    ]
    if not events:
        raise ValueError(f"Entity {entity_payload['entity_id']} has no derived support events.")

    profile = make_profile(str(entity_payload["entity_id"]), events[0].timestamp)
    event_type_counts: Counter[str] = Counter()
    decay_checkpoints = 0

    for event in events:
        if maybe_apply_gap_decay(profile, event.timestamp):
            decay_checkpoints += 1
        apply_event(profile, event)
        event_type_counts[event.event_type] += 1

    decision_time = profile.updated_at + timedelta(days=FINAL_DECISION_GAP_DAYS)
    apply_decay(profile, now=decision_time)
    revalidation_result = revalidate_profile(profile, now=decision_time)
    calibration_result = None
    routing_profile = profile

    if use_calibration:
        calibration_result = apply_support_v1_calibration(
            profile=profile,
            visible_events=events,
            decision_time=decision_time,
        )
        routing_profile = calibration_result.profile

    decision_result = route_decision(
        routing_profile,
        DecisionContext(stakes=EVALUATION_STAKES),
    )

    return SupportEntitySummary(
        entity_id=str(entity_payload["entity_id"]),
        account_name=str(entity_payload["account_name"]),
        segment=str(entity_payload["segment"]),
        case_count=len(entity_payload["case_ids"]),
        event_count=len(events),
        decay_checkpoints=decay_checkpoints,
        event_type_counts=dict(sorted(event_type_counts.items())),
        route_after_optional_calibration=decision_result.selected_path,
        route_reason_after_optional_calibration=decision_result.reason,
        trust=routing_profile.attributes["trust"].value,
        cooperativeness=routing_profile.attributes["cooperativeness"].value,
        predictability=routing_profile.attributes["predictability"].value,
        stability=routing_profile.attributes["stability"].value,
        risk=routing_profile.attributes["risk"].value,
        overall_confidence=routing_profile.overall_confidence,
        unknownness=routing_profile.unknownness,
        freshness=routing_profile.freshness,
        contradiction_load=routing_profile.contradiction_load,
        revalidation_triggered=revalidation_result.triggered,
        revalidation_reasons=tuple(revalidation_result.reasons),
        calibration_applied=calibration_result.applied if calibration_result else False,
        confidence_adjustment=(
            calibration_result.confidence_adjustment if calibration_result else 0.0
        ),
        unknownness_reduction=(
            calibration_result.unknownness_reduction if calibration_result else 0.0
        ),
    )


def format_float(value: float) -> str:
    return f"{value:.2f}"


def format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{name}={counts[name]}" for name in sorted(counts))


def format_revalidation_reasons(reasons: tuple[str, ...]) -> str:
    return ", ".join(reasons) if reasons else "none"


def print_summary(summary: SupportEntitySummary) -> None:
    print(
        " | ".join(
            [
                f"entity={summary.entity_id}",
                f"cases={summary.case_count}",
                f"events={summary.event_count}",
                f"event_mix={format_counts(summary.event_type_counts)}",
                f"path={summary.route_after_optional_calibration}",
                f"trust={format_float(summary.trust)}",
                f"confidence={format_float(summary.overall_confidence)}",
                f"unknownness={format_float(summary.unknownness)}",
                f"freshness={format_float(summary.freshness)}",
                f"contradiction={format_float(summary.contradiction_load)}",
                f"revalidated={summary.revalidation_triggered}",
                f"calibration_applied={summary.calibration_applied}",
            ]
        )
    )
    print(
        "route_after_optional_calibration_reason="
        f"{summary.route_reason_after_optional_calibration}"
    )
    print(f"revalidation_reasons={format_revalidation_reasons(summary.revalidation_reasons)}")
    print(
        "calibration_adjustments="
        f"confidence+{format_float(summary.confidence_adjustment)}, "
        f"unknownness-{format_float(summary.unknownness_reduction)}"
    )
    print()


def build_entity_export(summary: SupportEntitySummary) -> dict[str, Any]:
    return {
        "entity_id": summary.entity_id,
        "account_name": summary.account_name,
        "segment": summary.segment,
        "case_count": summary.case_count,
        "event_count": summary.event_count,
        "decay_checkpoints": summary.decay_checkpoints,
        "event_type_counts": summary.event_type_counts,
        "route_after_optional_calibration": summary.route_after_optional_calibration,
        "route_reason_after_optional_calibration": (
            summary.route_reason_after_optional_calibration
        ),
        "profile_snapshot": {
            "trust": summary.trust,
            "cooperativeness": summary.cooperativeness,
            "predictability": summary.predictability,
            "stability": summary.stability,
            "risk": summary.risk,
            "overall_confidence": summary.overall_confidence,
            "unknownness": summary.unknownness,
            "freshness": summary.freshness,
            "contradiction_load": summary.contradiction_load,
        },
        "revalidation": {
            "triggered": summary.revalidation_triggered,
            "reasons": list(summary.revalidation_reasons),
        },
        "calibration": {
            "applied": summary.calibration_applied,
            "confidence_adjustment": summary.confidence_adjustment,
            "unknownness_reduction": summary.unknownness_reduction,
        },
    }


def build_export_payload(
    event_payload: dict[str, Any],
    summaries: list[SupportEntitySummary],
    use_calibration: bool,
) -> dict[str, Any]:
    return {
        "run_metadata": {
            "generated_at": datetime.now().astimezone().isoformat(),
            "dataset_path": str(DATASET_PATH),
            "support_events_path": str(EVENTS_ARTIFACT_PATH),
            "export_path": str(EVALUATION_ARTIFACT_PATH),
            "mode": "calibrated" if use_calibration else "default",
            "stakes": EVALUATION_STAKES,
            "decay_gap_days": DECAY_GAP_DAYS,
            "final_decision_gap_days": FINAL_DECISION_GAP_DAYS,
            "calibration": {
                "enabled": use_calibration,
                "name": CALIBRATION_NAME,
                "version": CALIBRATION_VERSION,
                "confidence_boost_cap": WINNING_SETTINGS.confidence_boost_cap,
                "unknownness_reduction_cap": WINNING_SETTINGS.unknownness_reduction_cap,
            },
        },
        "aggregate_summary": {
            "entities_evaluated": len(summaries),
            "fast_path_count": sum(
                1
                for summary in summaries
                if summary.route_after_optional_calibration == "fast_path"
            ),
            "deep_path_count": sum(
                1
                for summary in summaries
                if summary.route_after_optional_calibration == "deep_path"
            ),
            "revalidations_triggered": sum(
                1 for summary in summaries if summary.revalidation_triggered
            ),
            "calibration_applied_count": sum(
                1 for summary in summaries if summary.calibration_applied
            ),
            "average_confidence": (
                sum(summary.overall_confidence for summary in summaries) / len(summaries)
            ),
            "average_unknownness": (
                sum(summary.unknownness for summary in summaries) / len(summaries)
            ),
        },
        "support_event_artifact": {
            "path": str(EVENTS_ARTIFACT_PATH),
            "entity_count": len(event_payload["entities"]),
            "total_events": sum(
                int(entity_payload["event_count"])
                for entity_payload in event_payload["entities"]
            ),
        },
        "entity_summaries": [build_entity_export(summary) for summary in summaries],
    }


def export_evaluation(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with EVALUATION_ARTIFACT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return EVALUATION_ARTIFACT_PATH


def main() -> None:
    args = parse_args()
    cases = load_support_cases(DATASET_PATH)
    event_payload = convert_cases_to_entity_event_payload(cases, DATASET_PATH)
    export_events(event_payload, EVENTS_ARTIFACT_PATH)
    summaries = [
        summarize_entity(entity_payload, use_calibration=args.calibrated)
        for entity_payload in event_payload["entities"]
    ]

    print("support_v1 evaluation")
    print(f"dataset: {DATASET_PATH}")
    print(f"support_events: {EVENTS_ARTIFACT_PATH}")
    print(f"mode: {'calibrated' if args.calibrated else 'default'}")
    print(f"stakes: {EVALUATION_STAKES}")
    print(f"decay_gap_days: {DECAY_GAP_DAYS}")
    print(f"final_decision_gap_days: {FINAL_DECISION_GAP_DAYS}")
    if args.calibrated:
        print(
            "calibration: "
            f"enabled ({CALIBRATION_NAME}/{CALIBRATION_VERSION}, "
            f"confidence_boost_cap={format_float(WINNING_SETTINGS.confidence_boost_cap)}, "
            f"unknownness_reduction_cap={format_float(WINNING_SETTINGS.unknownness_reduction_cap)})"
        )
    else:
        print(
            "calibration: "
            f"disabled ({CALIBRATION_NAME}/{CALIBRATION_VERSION} available)"
        )
    print()

    for summary in summaries:
        print_summary(summary)

    export_payload = build_export_payload(
        event_payload,
        summaries,
        use_calibration=args.calibrated,
    )
    export_path = export_evaluation(export_payload)
    print(f"evaluation_export: {export_path}")


if __name__ == "__main__":
    main()
