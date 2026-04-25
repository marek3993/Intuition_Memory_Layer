from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from iml.live_write_phase1b_helper import CONTRACT, DecisionEpisodeStore, utc_now_iso

DEFAULT_OUTPUT_DIR = Path("artifacts/trendatlas_shadow_run_verification")
DEFAULT_OUTPUT_JSON = "shadow_run_verification.json"
DEFAULT_OUTPUT_MARKDOWN = "shadow_run_verification.md"
DEFAULT_AUTHORITATIVE_BASELINE_PATH = "authoritative_current_artifacts_only"
DEFAULT_SHADOW_PATH = "shadow_retrieval_memory_augmented"
STRONG_MATCH_FLOOR = 0.55


def _tokenize(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", value.lower()))


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _serialize(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        default=_json_default,
    )


def _payload_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_serialize(value).encode("utf-8")).hexdigest()


def _clamp(value: float, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _days_between(earlier: datetime, later: datetime) -> float:
    return max(0.0, (later - earlier).total_seconds() / 86_400.0)


def _load_store_records(store_path: Path) -> list[dict[str, Any]]:
    if not store_path.exists():
        raise FileNotFoundError(f"store path does not exist: {store_path}")

    records: list[dict[str, Any]] = []
    with store_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            record = json.loads(line)
            if isinstance(record, dict):
                records.append(record)
    return records


def _episode_matches_filters(
    payload: dict[str, Any],
    *,
    request: dict[str, Any],
    now: datetime,
) -> bool:
    if payload.get("schema_version") != CONTRACT:
        return False
    if payload.get("tenant_id") != request.get("tenant_id"):
        return False
    if payload.get("namespace") != request.get("namespace"):
        return False
    if payload.get("collection") not in request.get("collections", []):
        return False

    filters = request.get("filters", {})
    episode_types = filters.get("episode_types") or []
    if episode_types and payload.get("episode_type") not in episode_types:
        return False

    environment = filters.get("environment")
    metadata = payload.get("metadata", {})
    if environment and metadata.get("environment") != environment:
        return False

    decision_timestamp = _parse_timestamp(payload.get("decision_timestamp_utc"))
    max_age_days = filters.get("max_age_days")
    if (
        isinstance(max_age_days, (int, float))
        and decision_timestamp is not None
        and _days_between(decision_timestamp, now) > float(max_age_days)
    ):
        return False

    query_context = request.get("query_context", {})
    run_context = payload.get("run_context", {})
    family_id = str(query_context.get("family_id") or "").strip()
    if filters.get("same_family_only") and family_id:
        if str(run_context.get("family_id") or "").strip() != family_id:
            return False

    return True


def _compute_reason_codes(
    payload: dict[str, Any],
    *,
    request: dict[str, Any],
    score_inputs: dict[str, bool],
) -> list[str]:
    reason_codes: list[str] = []
    requester = str(request.get("requester") or "").strip().lower()
    query_context = request.get("query_context", {})
    run_context = payload.get("run_context", {})
    decision = payload.get("decision", {})
    outcome = payload.get("outcome", {})

    if score_inputs["same_family"]:
        reason_codes.append("same_family")
    if score_inputs["same_mechanism"]:
        reason_codes.append("same_mechanism")
    if score_inputs["goal_overlap"]:
        reason_codes.append("same_goal_shape")
    if score_inputs["current_packet_overlap"]:
        reason_codes.append("same_packet_shape")

    failure_modes = set(outcome.get("failure_modes") or [])
    contradiction_flags = set(outcome.get("contradiction_flags") or [])
    decision_text = " ".join(
        [
            str(decision.get("verdict") or ""),
            str(decision.get("action") or ""),
            str(decision.get("rationale_summary") or ""),
        ]
    ).lower()

    if "cost_blowup" in failure_modes or "cost" in decision_text:
        reason_codes.append("cost_failure_signal")
    if contradiction_flags:
        reason_codes.append("expected_actual_mismatch")
    if requester == "planner" and (
        "governor" in str(payload.get("episode_type") or "")
        or "critic" in str(payload.get("episode_type") or "")
    ):
        reason_codes.append("recent_negative_supervisor_signal")
    if requester == "critic" and contradiction_flags:
        reason_codes.append("contradiction_pattern")
    if requester == "governor" and (
        "mixed" in decision_text or "reject" in decision_text or "hold" in decision_text
    ):
        reason_codes.append("recent_negative_governor_signal")

    unique_reason_codes: list[str] = []
    for reason_code in reason_codes:
        if reason_code not in unique_reason_codes:
            unique_reason_codes.append(reason_code)
    return unique_reason_codes


def _score_episode(
    payload: dict[str, Any],
    *,
    request: dict[str, Any],
    now: datetime,
) -> tuple[float, list[str]]:
    query_context = request.get("query_context", {})
    run_context = payload.get("run_context", {})

    family_id = str(query_context.get("family_id") or "").strip()
    mechanism_id = str(query_context.get("mechanism_id") or "").strip()
    goal_tokens = _tokenize(str(query_context.get("goal") or ""))
    current_packet_tokens = _tokenize(str(query_context.get("current_packet_text") or ""))

    packet = payload.get("decision_packet", {})
    packet_tokens = _tokenize(
        " ".join(
            [
                str(packet.get("packet_text") or ""),
                " ".join(str(item) for item in packet.get("salient_facts") or []),
                " ".join(str(item) for item in packet.get("risk_flags") or []),
            ]
        )
    )

    same_family = bool(family_id) and str(run_context.get("family_id") or "").strip() == family_id
    same_mechanism = bool(mechanism_id) and (
        str(run_context.get("mechanism_id") or "").strip() == mechanism_id
    )
    goal_overlap = bool(goal_tokens and packet_tokens and goal_tokens & packet_tokens)
    current_packet_overlap = bool(
        current_packet_tokens and packet_tokens and current_packet_tokens & packet_tokens
    )

    similarity_score = 0.0
    if same_family:
        similarity_score += 0.42
    if same_mechanism:
        similarity_score += 0.22
    if goal_overlap:
        similarity_score += 0.12
    if current_packet_overlap:
        similarity_score += 0.10

    decision_timestamp = _parse_timestamp(payload.get("decision_timestamp_utc"))
    if decision_timestamp is not None:
        recency_days = _days_between(decision_timestamp, now)
        similarity_score += 0.14 * max(0.0, 1.0 - min(recency_days, 45.0) / 45.0)

    requester = str(request.get("requester") or "").strip().lower()
    episode_type = str(payload.get("episode_type") or "").strip().lower()
    decision = payload.get("decision", {})
    decision_text = " ".join(
        [
            str(decision.get("verdict") or ""),
            str(decision.get("action") or ""),
            str(decision.get("rationale_summary") or ""),
        ]
    ).lower()

    if requester == "planner" and episode_type == "governor_decision":
        similarity_score += 0.18
    elif requester == "planner" and episode_type == "critic_verdict":
        similarity_score += 0.12
    if requester == "critic" and episode_type in {"heavy_validation_verdict", "governor_decision"}:
        similarity_score += 0.06
    if requester == "governor" and episode_type in {"critic_verdict", "governor_decision"}:
        similarity_score += 0.08
    if requester in {"planner", "governor"} and (
        "mixed_negative" in decision_text or "hold" in decision_text or "reject" in decision_text
    ):
        similarity_score += 0.05

    packet_unknownness = float(packet.get("unknownness_score") or 0.0)
    contradiction_load = float(packet.get("contradiction_load") or 0.0)
    freshness_hours = float(packet.get("freshness_hours") or 999.0)
    confidence_bonus = (
        (1.0 - min(packet_unknownness, 1.0)) * 0.04
        + min(contradiction_load, 1.0) * 0.03
        + max(0.0, 1.0 - min(freshness_hours, 72.0) / 72.0) * 0.03
    )

    score_inputs = {
        "same_family": same_family,
        "same_mechanism": same_mechanism,
        "goal_overlap": goal_overlap,
        "current_packet_overlap": current_packet_overlap,
    }
    reason_codes = _compute_reason_codes(payload, request=request, score_inputs=score_inputs)
    confidence_adjusted_score = _clamp(similarity_score + confidence_bonus)
    return confidence_adjusted_score, reason_codes


def retrieve_shadow_matches(
    *,
    request: dict[str, Any],
    store_path: Path,
    now_utc: str | None = None,
) -> dict[str, Any]:
    if request.get("schema_version") != CONTRACT:
        raise ValueError("shadow retrieval request schema_version must match contract")

    now = _parse_timestamp(now_utc or utc_now_iso())
    if now is None:
        raise ValueError("failed to parse shadow retrieval time")

    top_k = max(1, int(request.get("top_k") or 1))
    records = _load_store_records(store_path)
    candidates: list[dict[str, Any]] = []

    for record in records:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if not _episode_matches_filters(payload, request=request, now=now):
            continue
        score, reason_codes = _score_episode(payload, request=request, now=now)
        candidates.append(
            {
                "record": record,
                "payload": payload,
                "confidence_adjusted_score": round(score, 4),
                "reason_codes": reason_codes,
            }
        )

    requester = str(request.get("requester") or "").strip().lower()

    def _episode_priority(payload: dict[str, Any]) -> int:
        episode_type = str(payload.get("episode_type") or "").strip().lower()
        if requester == "planner":
            return {
                "governor_decision": 3,
                "critic_verdict": 2,
                "heavy_validation_verdict": 1,
            }.get(episode_type, 0)
        if requester == "critic":
            return {
                "heavy_validation_verdict": 3,
                "governor_decision": 2,
                "planner_proposal": 1,
            }.get(episode_type, 0)
        if requester == "governor":
            return {
                "governor_decision": 3,
                "critic_verdict": 2,
                "heavy_validation_verdict": 1,
            }.get(episode_type, 0)
        return 0

    candidates.sort(
        key=lambda item: (
            -float(item["confidence_adjusted_score"]),
            -_episode_priority(item["payload"]),
            str(item["payload"].get("decision_timestamp_utc") or ""),
            str(item["payload"].get("memory_id") or ""),
        )
    )

    strong_candidates = [
        item for item in candidates if float(item["confidence_adjusted_score"]) >= STRONG_MATCH_FLOOR
    ]
    selected = strong_candidates[:top_k]

    matches: list[dict[str, Any]] = []
    for candidate in selected:
        payload = candidate["payload"]
        packet = payload.get("decision_packet", {})
        decision = payload.get("decision", {})
        outcome = payload.get("outcome", {})
        matches.append(
            {
                "memory_id": payload.get("memory_id"),
                "episode_type": payload.get("episode_type"),
                "similarity_score": candidate["confidence_adjusted_score"],
                "confidence_adjusted_score": candidate["confidence_adjusted_score"],
                "reason_codes": candidate["reason_codes"],
                "packet": {
                    "decision_summary": decision.get("rationale_summary"),
                    "what_worked": outcome.get("actual_impact_summary"),
                    "what_failed": outcome.get("delta_summary"),
                    "expected_vs_actual": (
                        " / ".join(str(item) for item in outcome.get("contradiction_flags") or [])
                        or decision.get("expected_impact_summary")
                    ),
                    "risk_flags": list(packet.get("risk_flags") or []),
                    "recommended_caution": decision.get("stop_condition"),
                },
                "artifact_refs": list(payload.get("metadata", {}).get("artifact_refs") or []),
            }
        )

    retrieval_confidence = (
        round(
            sum(float(item["confidence_adjusted_score"]) for item in matches) / len(matches),
            4,
        )
        if matches
        else 0.0
    )

    if matches:
        fallback = {
            "recommended": False,
            "reason": "Strong memory match found. No raw fallback required.",
        }
        status = "ok"
    else:
        fallback = {
            "recommended": False,
            "reason": "No strong same-scope memory match cleared the fail-closed threshold.",
        }
        status = "ok"

    return {
        "schema_version": CONTRACT,
        "status": status,
        "query_id": "qry_" + hashlib.sha256(_serialize(request).encode("utf-8")).hexdigest()[:8],
        "requester": request.get("requester"),
        "retrieval_confidence": retrieval_confidence,
        "matches": matches,
        "fallback": fallback,
    }


def _build_divergence_markers(
    *,
    response: dict[str, Any],
    fail_closed_triggered: bool,
) -> list[str]:
    markers: list[str] = []
    if fail_closed_triggered:
        markers.append("fail_closed_triggered")

    matches = response.get("matches") or []
    if not matches:
        markers.append("no_shadow_matches")
        return markers

    episode_types = sorted({str(match.get("episode_type") or "") for match in matches})
    if episode_types:
        markers.append("shadow_matches:" + ",".join(episode_types))

    reason_codes = sorted(
        {
            str(reason_code)
            for match in matches
            for reason_code in match.get("reason_codes") or []
            if str(reason_code)
        }
    )
    if reason_codes:
        markers.append("reason_codes:" + ",".join(reason_codes))

    risk_flags = sorted(
        {
            str(flag)
            for match in matches
            for flag in match.get("packet", {}).get("risk_flags") or []
            if str(flag)
        }
    )
    if risk_flags:
        markers.append("shadow_risk_flags:" + ",".join(risk_flags))
    return markers


def build_shadow_run_artifact(
    *,
    request: dict[str, Any],
    authoritative_output: dict[str, Any],
    store_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    authoritative_baseline_path: str = DEFAULT_AUTHORITATIVE_BASELINE_PATH,
    shadow_path: str = DEFAULT_SHADOW_PATH,
    now_utc: str | None = None,
) -> dict[str, Any]:
    retrieved_response: dict[str, Any] | None = None
    retrieval_error: str | None = None
    fail_closed_triggered = False

    try:
        retrieved_response = retrieve_shadow_matches(
            request=request,
            store_path=store_path,
            now_utc=now_utc,
        )
        fail_closed_triggered = not bool(retrieved_response.get("matches"))
    except Exception as error:
        retrieval_error = f"{type(error).__name__}: {error}"
        fail_closed_triggered = True

    response = retrieved_response or {
        "schema_version": CONTRACT,
        "status": "unavailable",
        "query_id": None,
        "requester": request.get("requester"),
        "retrieval_confidence": 0.0,
        "matches": [],
        "fallback": {
            "recommended": False,
            "reason": "Shadow retrieval was unavailable, so the run stayed fail-closed.",
        },
    }
    divergence_markers = _build_divergence_markers(
        response=response,
        fail_closed_triggered=fail_closed_triggered,
    )
    final_authoritative_output = json.loads(json.dumps(authoritative_output))
    comparison_summary = {
        "authoritative_output_preserved": final_authoritative_output == authoritative_output,
        "retrieval_status": response.get("status"),
        "retrieval_match_count": len(response.get("matches") or []),
        "retrieval_confidence": float(response.get("retrieval_confidence") or 0.0),
        "shadow_memory_attached": bool(response.get("matches")),
        "comparison_mode": "shadow_only",
        "divergence_marker_count": len(divergence_markers),
        "manual_inspection_ready": True,
    }
    fail_closed = {
        "enabled": bool(request.get("fail_closed", True)),
        "triggered": fail_closed_triggered,
        "status": "unchanged_authoritative_output",
        "reason": (
            retrieval_error
            or response.get("fallback", {}).get("reason")
            or "Shadow retrieval returned matches without changing authoritative output."
        ),
    }

    artifact = {
        "run_metadata": {
            "generated_at": now_utc or utc_now_iso(),
            "schema_version": CONTRACT,
            "requester": request.get("requester"),
            "store_path": str(store_path),
            "output_dir": str(output_dir),
            "mode": "shadow_only_verification",
        },
        "authoritative_baseline_path_used": {
            "path": authoritative_baseline_path,
            "output_hash": _payload_hash(authoritative_output),
            "output": authoritative_output,
        },
        "shadow_comparison_path_used": {
            "path": shadow_path,
            "request": request,
            "retrieval_inputs_selected": {
                "query_context": request.get("query_context", {}),
                "filters": request.get("filters", {}),
                "top_k": request.get("top_k"),
                "collections": request.get("collections", []),
            },
            "response": response,
        },
        "comparison_result_summary": comparison_summary,
        "divergence_markers": divergence_markers,
        "fail_closed_status": fail_closed,
        "final_authoritative_output": {
            "output_hash": _payload_hash(final_authoritative_output),
            "output": final_authoritative_output,
        },
        "retrieval_error": retrieval_error,
    }
    return artifact


def render_shadow_run_markdown(artifact: dict[str, Any]) -> str:
    response = artifact["shadow_comparison_path_used"]["response"]
    matches = response.get("matches") or []
    fail_closed = artifact["fail_closed_status"]
    summary = artifact["comparison_result_summary"]

    lines = [
        "# TrendAtlas Shadow Run Verification",
        "",
        f"- Generated: `{artifact['run_metadata']['generated_at']}`",
        f"- Requester: `{artifact['run_metadata']['requester']}`",
        f"- Mode: `{artifact['run_metadata']['mode']}`",
        f"- Store path: `{artifact['run_metadata']['store_path']}`",
        "",
        "## Paths",
        "",
        f"- Authoritative baseline path used: `{artifact['authoritative_baseline_path_used']['path']}`",
        f"- Shadow comparison path used: `{artifact['shadow_comparison_path_used']['path']}`",
        "",
        "## Retrieval Inputs Selected",
        "",
        f"- Query context: `{_serialize(artifact['shadow_comparison_path_used']['retrieval_inputs_selected']['query_context'])}`",
        f"- Filters: `{_serialize(artifact['shadow_comparison_path_used']['retrieval_inputs_selected']['filters'])}`",
        f"- top_k: `{artifact['shadow_comparison_path_used']['retrieval_inputs_selected']['top_k']}`",
        "",
        "## Comparison Result Summary",
        "",
        f"- Retrieval status: `{summary['retrieval_status']}`",
        f"- Retrieval match count: `{summary['retrieval_match_count']}`",
        f"- Retrieval confidence: `{summary['retrieval_confidence']:.4f}`",
        f"- Authoritative output preserved: `{str(summary['authoritative_output_preserved']).lower()}`",
        f"- Shadow memory attached: `{str(summary['shadow_memory_attached']).lower()}`",
        "",
        "## Divergence Markers",
        "",
    ]

    if artifact["divergence_markers"]:
        for marker in artifact["divergence_markers"]:
            lines.append(f"- {marker}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Fail-Closed Status",
            "",
            f"- Enabled: `{str(fail_closed['enabled']).lower()}`",
            f"- Triggered: `{str(fail_closed['triggered']).lower()}`",
            f"- Status: `{fail_closed['status']}`",
            f"- Reason: {fail_closed['reason']}",
            "",
            "## Shadow Matches",
            "",
        ]
    )

    if not matches:
        lines.append("- none")
    else:
        for match in matches:
            lines.append(
                f"- `{match['memory_id']}` | episode_type=`{match['episode_type']}` | score=`{float(match['confidence_adjusted_score']):.4f}` | reasons=`{', '.join(match['reason_codes'])}`"
            )

    lines.extend(
        [
            "",
            "## Final Authoritative Output",
            "",
            f"- Output hash: `{artifact['final_authoritative_output']['output_hash']}`",
            f"- Output body: `{_serialize(artifact['final_authoritative_output']['output'])}`",
        ]
    )

    if artifact.get("retrieval_error"):
        lines.extend(
            [
                "",
                "## Retrieval Error",
                "",
                f"- `{artifact['retrieval_error']}`",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def write_shadow_run_artifacts(
    artifact: dict[str, Any],
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / DEFAULT_OUTPUT_JSON
    markdown_path = output_dir / DEFAULT_OUTPUT_MARKDOWN
    json_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_shadow_run_markdown(artifact), encoding="utf-8")
    return {
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }


def build_demo_authoritative_output() -> dict[str, Any]:
    return {
        "planner_action": "propose_mutation",
        "proposal_id": "prop_shadow_demo_001",
        "status": "authoritative_unchanged",
        "notes": [
            "Current authoritative planner result was produced without memory injection.",
            "Shadow verification must not mutate this output.",
        ],
    }


def build_demo_retrieval_request(*, requester: str = "planner") -> dict[str, Any]:
    return {
        "schema_version": CONTRACT,
        "tenant_id": "research_os_prod",
        "namespace": "trendatlas",
        "collections": ["decision_episodes"],
        "requester": requester,
        "query_context": {
            "current_stage": "proposal_generation",
            "cycle_id": "cy_2026_04_21_eq_mr_042",
            "family_id": "fam_eq_mr_042",
            "mechanism_id": "mech_spreadfade_7",
            "goal": (
                "Propose the next mutation after mixed recent evidence and avoid "
                "repeating the most relevant prior caution signal."
            ),
            "current_packet_text": (
                "Planner is considering lower rebalance frequency plus a volatility "
                "gate after a recent mixed validation and a governor hold."
            ),
        },
        "filters": {
            "episode_types": [
                "planner_proposal",
                "heavy_validation_verdict",
                "critic_verdict",
                "governor_decision",
            ],
            "same_family_only": True,
            "same_mechanism_preferred": True,
            "max_age_days": 45,
            "environment": "prod",
        },
        "top_k": 3,
        "include_cycle_summary": False,
        "allow_raw_fallback": False,
        "fail_closed": True,
    }


def seed_demo_store(store_path: Path) -> None:
    store = DecisionEpisodeStore(store_path)
    demo_payloads = [
        {
            "schema_version": CONTRACT,
            "tenant_id": "research_os_prod",
            "namespace": "trendatlas",
            "collection": "decision_episodes",
            "memory_id": "mem_fam_eq_mr_042_mech_spreadfade_7_hv_2026_04_18t23_52_10z",
            "entity_type": "mechanism",
            "entity_id": "mech_spreadfade_7",
            "episode_type": "heavy_validation_verdict",
            "decision_timestamp_utc": "2026-04-18T23:52:10Z",
            "run_context": {
                "cycle_id": "cy_2026_04_18_eq_mr_042",
                "family_id": "fam_eq_mr_042",
                "mechanism_id": "mech_spreadfade_7",
                "proposal_id": "prop_67aa21",
                "validation_job_id": "hv_91c2d0",
                "critic_run_id": "crit_a13c66",
                "governor_run_id": "gov_6e1ad3",
            },
            "decision": {
                "action": "send_to_critic_with_warning",
                "verdict": "mixed",
                "rationale_summary": (
                    "Mutation reduced false entries in calm sessions but increased "
                    "turnover and spread loss in volatile opens."
                ),
                "expected_impact_summary": (
                    "Planner expected lower churn and better net retention from the tighter filter."
                ),
                "stop_condition": (
                    "Do not promote if net edge improvement is negative after realistic "
                    "cost model or if the same contradiction reappears in the next cycle."
                ),
                "confidence": 0.76,
            },
            "outcome": {
                "status": "mixed_result",
                "actual_impact_summary": (
                    "Precision improved, gross edge slightly improved, but net edge "
                    "deteriorated after transaction costs."
                ),
                "delta_summary": (
                    "Expected +12 bps net vs control; observed -4 bps net overall and "
                    "-11 bps in volatile-open slice."
                ),
                "cost_summary": "Turnover +24%, spread slippage +14%, validation compute spend 1.3x baseline.",
                "failure_modes": [
                    "expected_vs_actual_mismatch",
                    "cost_blowup",
                    "slice_instability",
                ],
                "contradiction_flags": [
                    "planner_expected_churn_down",
                    "observed_turnover_up",
                    "planner_expected_net_up",
                    "observed_net_down",
                ],
            },
            "decision_packet": {
                "packet_text": (
                    "Heavy validation found a directional mismatch. The tighter entry "
                    "filter improved precision and gross edge, but turnover rose and "
                    "spread cost erased the gain."
                ),
                "salient_facts": [
                    "family fam_eq_mr_042",
                    "mechanism mech_spreadfade_7",
                    "precision up",
                    "net down after costs",
                    "volatile-open slice failed",
                ],
                "risk_flags": [
                    "cost_blowup",
                    "regime_instability",
                    "promotion_not_safe",
                ],
                "unknownness_score": 0.18,
                "contradiction_load": 0.72,
                "freshness_hours": 28.4,
            },
            "metadata": {
                "authoritative": False,
                "environment": "prod",
                "artifact_refs": [
                    "s3://trendatlas/runs/cy_2026_04_18_eq_mr_042/validation/hv_91c2d0_summary.json"
                ],
                "tags": ["heavy_validation", "mixed", "cost_aware"],
            },
        },
        {
            "schema_version": CONTRACT,
            "tenant_id": "research_os_prod",
            "namespace": "trendatlas",
            "collection": "decision_episodes",
            "memory_id": "mem_fam_eq_mr_042_mech_spreadfade_7_gov_2026_04_20t08_14_33z",
            "entity_type": "mechanism",
            "entity_id": "mech_spreadfade_7",
            "episode_type": "governor_decision",
            "decision_timestamp_utc": "2026-04-20T08:14:33Z",
            "run_context": {
                "cycle_id": "cy_2026_04_20_eq_mr_042",
                "family_id": "fam_eq_mr_042",
                "mechanism_id": "mech_spreadfade_7",
                "proposal_id": "prop_8f3e21",
                "validation_job_id": "hv_0d91aa",
                "critic_run_id": "crit_7d4b8e",
                "governor_run_id": "gov_24e1b7",
            },
            "decision": {
                "action": "hold_back_promotion",
                "verdict": "mixed_negative",
                "rationale_summary": (
                    "Validation cleared minimum return threshold but cost expansion and "
                    "contradictory regime behavior weakened promotion confidence."
                ),
                "expected_impact_summary": (
                    "Expected lower slippage and more stable win-rate in high-volatility opens."
                ),
                "stop_condition": (
                    "Do not re-run unchanged on the same family if cost delta remains "
                    "above tolerance and contradiction load stays elevated."
                ),
                "confidence": 0.71,
            },
            "outcome": {
                "status": "validated_but_rejected",
                "actual_impact_summary": (
                    "Gross edge improved modestly, but net edge deteriorated after "
                    "turnover and spread costs."
                ),
                "delta_summary": "Expected +18 bps net improvement; observed -6 bps net vs control.",
                "cost_summary": "Turnover +29%, spread cost +17%, compute spend medium-high.",
                "failure_modes": [
                    "cost_blowup",
                    "regime_instability",
                    "expected_vs_actual_mismatch",
                ],
                "contradiction_flags": [
                    "planner_predicted_lower_cost",
                    "validation_showed_higher_cost",
                    "critic_found_regime_split",
                ],
            },
            "decision_packet": {
                "packet_text": (
                    "Governor held promotion after mixed validation. Mechanism improved "
                    "gross edge in one slice but failed net improvement after cost expansion."
                ),
                "salient_facts": [
                    "same family",
                    "same mechanism",
                    "gross up net down",
                    "cost expansion after mutation",
                    "promotion blocked",
                ],
                "risk_flags": [
                    "cost_blowup",
                    "mixed_evidence",
                    "contradiction_load_high",
                ],
                "unknownness_score": 0.22,
                "contradiction_load": 0.68,
                "freshness_hours": 3.1,
            },
            "metadata": {
                "authoritative": False,
                "environment": "prod",
                "artifact_refs": [
                    "s3://trendatlas/runs/cy_2026_04_20_eq_mr_042/critic/crit_7d4b8e.md"
                ],
                "tags": ["governor", "mixed_negative", "cost_aware"],
            },
        },
    ]

    from iml.live_write_phase1b_helper import process_decision_episode_write

    for payload in demo_payloads:
        process_decision_episode_write(payload=payload, store=store, received_at_utc=utc_now_iso())
