from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4
from pilot_ops.io import write_manifest as write_json_manifest, write_report

from build_support_v1_pilot_execution_bundle import MODE_CONFIGS, SCRIPT_DIR, project_relative_path


ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
SUMMARY_JSON_PATH = ARTIFACTS_DIR / "support_v1_system_summary.json"
SUMMARY_MARKDOWN_PATH = ARTIFACTS_DIR / "support_v1_system_summary.md"
RUN_COMMAND = "py use_cases/support_v1/build_support_v1_system_summary.py"
WHAT_THIS_ADDS = (
    "One explicit top-level support_v1 system-state summary artifact that consolidates "
    "current evaluation evidence, ingest coverage, package and handoff readiness, real "
    "pilot workspace readiness, contract validation status, and the immediate next "
    "recommended step without rerunning evaluations or rebuilding bundles/workspaces."
)

INGEST_COMPARISON_PATH = ARTIFACTS_DIR / "support_ingest_modality_comparison.json"
PACKAGE_SUMMARY_PATH = ARTIFACTS_DIR / "support_v1_pilot_package_summary.json"
BUNDLE_VALIDATION_SUMMARY_PATH = ARTIFACTS_DIR / "support_v1_pilot_bundle_validation_summary.json"
WORKSPACE_SUMMARY_PATH = ARTIFACTS_DIR / "support_v1_real_pilot_workspace_summary.json"
READINESS_MEMO_PATH = ARTIFACTS_DIR / "support_v1_readiness_memo.md"
CONTRACT_VALIDATION_PATH = ARTIFACTS_DIR / "helpdesk_export_contract_validation.json"

MODALITY_TO_MODE = {
    "labeled_support_packs": "labeled_support",
    "raw_ingest_packs": "raw_ingest",
    "csv_ingest_packs": "csv_ingest",
    "mapped_ingest_packs": "mapped_ingest",
    "zendesk_like_ingest_packs": "zendesk_like",
}

MODE_DISPLAY_NAMES = {
    "labeled_support": "labeled support",
    "raw_ingest": "raw ingest",
    "csv_ingest": "CSV ingest",
    "mapped_ingest": "mapped ingest",
    "zendesk_like": "Zendesk-like ingest",
}


def load_json_object(path: Path, *, used_paths: list[Path]) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {project_relative_path(path)}")
    used_paths.append(path)
    return payload


def record_optional_existing_path(path: Path, *, used_paths: list[Path]) -> None:
    if path.exists():
        used_paths.append(path)


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def format_delta(value: float) -> str:
    if value > 0:
        return f"+{format_percent(value)}"
    if value < 0:
        return f"-{format_percent(abs(value))}"
    return format_percent(0.0)


def display_path(value: str | Path | None) -> str | None:
    if value is None:
        return None

    path = Path(value)
    try:
        return project_relative_path(path)
    except Exception:
        return str(path).replace("\\", "/")


def display_mode(mode: str | None) -> str:
    if mode is None:
        return "unknown"
    return MODE_DISPLAY_NAMES.get(mode, mode.replace("_", " "))


def collect_evaluated_modes(ingest_comparison: dict[str, Any]) -> list[str]:
    modality_names = ingest_comparison.get("modalities", {})
    evaluated_modes = [
        MODALITY_TO_MODE[modality_name]
        for modality_name in modality_names
        if modality_name in MODALITY_TO_MODE
    ]
    return sorted(dict.fromkeys(evaluated_modes), key=list(MODE_CONFIGS.keys()).index)


def build_current_evaluation_position(ingest_comparison: dict[str, Any]) -> dict[str, Any]:
    top_level_summary = ingest_comparison["top_level_summary"]
    calibrated_vs_default = top_level_summary["calibrated_iml_vs_default_iml_across_modalities"]
    calibrated_vs_baselines = top_level_summary[
        "calibrated_iml_vs_baselines_on_largest_slice_per_modality"
    ]
    strongest = top_level_summary["strongest_evidence_modality"]
    weakest = top_level_summary["modality_needing_more_data"]
    evaluated_modes = collect_evaluated_modes(ingest_comparison)

    return {
        "evaluated_modes": evaluated_modes,
        "evaluated_mode_count": len(evaluated_modes),
        "overall_conclusion": top_level_summary["overall_conclusion"],
        "calibrated_iml_vs_default_iml": {
            "overall_relation": calibrated_vs_default["overall"],
            "improved_slice_count": calibrated_vs_default["improved_slice_count"],
            "tied_slice_count": calibrated_vs_default["tied_slice_count"],
            "total_slice_count": calibrated_vs_default["total_slice_count"],
        },
        "largest_slice_baseline_check": {
            "beats_best_baseline_count": calibrated_vs_baselines["beats_both_count"],
            "total_modalities_evaluated": calibrated_vs_baselines["total_modalities"],
        },
        "strongest_evidence_modality": {
            "mode": MODALITY_TO_MODE.get(strongest["modality"]),
            "display_name": strongest["display_name"],
            "largest_slice": strongest["largest_slice"],
            "label_count": strongest["label_count"],
            "calibrated_iml_accuracy": strongest["calibrated_iml_accuracy"],
            "best_non_calibrated_accuracy": strongest["best_non_calibrated_accuracy"],
            "margin_vs_best_non_calibrated": strongest["margin_vs_best_non_calibrated"],
            "selection_basis": strongest["selection_basis"],
        },
        "modality_needing_more_data": {
            "mode": MODALITY_TO_MODE.get(weakest["modality"]),
            "display_name": weakest["display_name"],
            "largest_slice": weakest["largest_slice"],
            "label_count": weakest["label_count"],
            "calibrated_iml_accuracy": weakest["calibrated_iml_accuracy"],
            "margin_vs_best_baseline": weakest["margin_vs_best_baseline"],
            "selection_basis": weakest["selection_basis"],
        },
        "summary_line": (
            f"Unified ingest comparison currently covers {len(evaluated_modes)} modes "
            f"({', '.join(f'`{mode}`' for mode in evaluated_modes)}). "
            f"Calibrated IML improves or ties default IML on "
            f"{calibrated_vs_default['improved_slice_count'] + calibrated_vs_default['tied_slice_count']} "
            f"of {calibrated_vs_default['total_slice_count']} slices and clears the best baseline "
            f"on the largest slice in {calibrated_vs_baselines['beats_both_count']} of "
            f"{calibrated_vs_baselines['total_modalities']} evaluated modalities."
        ),
    }


def build_ingest_coverage(
    ingest_comparison: dict[str, Any],
    package_summary: dict[str, Any],
    contract_validation: dict[str, Any],
) -> dict[str, Any]:
    supported_modes = package_summary["supported_modes"]
    evaluated_modes = collect_evaluated_modes(ingest_comparison)
    modes_without_top_level_eval_evidence = [
        mode for mode in supported_modes if mode not in evaluated_modes
    ]

    inputs = contract_validation.get("inputs", [])
    validated_formats = sorted(
        {
            str(input_result["detected_format"])
            for input_result in inputs
            if isinstance(input_result, dict) and isinstance(input_result.get("detected_format"), str)
        }
    )

    return {
        "supported_modes": supported_modes,
        "supported_mode_count": len(supported_modes),
        "modes_with_top_level_eval_evidence": evaluated_modes,
        "modes_without_top_level_eval_evidence": modes_without_top_level_eval_evidence,
        "validated_contract_formats": validated_formats,
        "contract_input_count": len(inputs),
        "summary_line": (
            f"Top-level package coverage exists for all {len(supported_modes)} supported modes, "
            f"while the unified ingest comparison currently covers {len(evaluated_modes)} modes. "
            + (
                f"`{modes_without_top_level_eval_evidence[0]}` is the current gap in the top-level ingest comparison."
                if len(modes_without_top_level_eval_evidence) == 1
                else (
                    "No supported mode is missing from the top-level ingest comparison."
                    if not modes_without_top_level_eval_evidence
                    else "Some supported modes are still missing from the top-level ingest comparison."
                )
            )
        ),
    }


def build_bundle_package_readiness(
    package_summary: dict[str, Any],
    bundle_validation_summary: dict[str, Any],
) -> dict[str, Any]:
    latest_validated_package_per_mode = bundle_validation_summary["latest_validated_package_per_mode"]
    latest_validated_handoff_bundle_per_mode = bundle_validation_summary[
        "latest_validated_handoff_bundle_per_mode"
    ]
    modes_missing_package = package_summary["modes_missing_package"]
    total_supported_modes = len(package_summary["supported_modes"])

    return {
        "total_package_count_found": package_summary["total_package_count_found"],
        "modes_with_package": package_summary["modes_with_package"],
        "modes_missing_package": modes_missing_package,
        "latest_package_overall": package_summary["latest_package_overall"],
        "total_bundles_scanned": bundle_validation_summary["total_bundles_scanned"],
        "validated_pass_count": bundle_validation_summary["validated_pass_count"],
        "validated_fail_count": bundle_validation_summary["validated_fail_count"],
        "missing_validation_count": bundle_validation_summary["missing_validation_count"],
        "latest_validated_package_mode_count": len(latest_validated_package_per_mode),
        "latest_validated_handoff_mode_count": len(latest_validated_handoff_bundle_per_mode),
        "latest_validated_package_per_mode": latest_validated_package_per_mode,
        "latest_validated_handoff_bundle_per_mode": latest_validated_handoff_bundle_per_mode,
        "summary_line": (
            f"{package_summary['total_package_count_found']} pilot packages are present and "
            f"{len(package_summary['modes_with_package'])} of {total_supported_modes} supported modes "
            "have a top-level package. "
            f"Bundle validation currently reports {bundle_validation_summary['validated_pass_count']} PASS, "
            f"{bundle_validation_summary['validated_fail_count']} FAIL, and "
            f"{bundle_validation_summary['missing_validation_count']} missing validation artifacts across "
            f"{bundle_validation_summary['total_bundles_scanned']} scanned pilot packages and handoff bundles."
        ),
    }


def build_workspace_readiness(workspace_summary: dict[str, Any]) -> dict[str, Any]:
    latest_workspace_overall = workspace_summary.get("latest_workspace_overall")
    workspace_overview = workspace_summary.get("workspace_overview", [])
    workspaces_missing_validation = [
        entry["workspace_path"]
        for entry in workspace_overview
        if isinstance(entry, dict) and entry.get("status") == "WARN"
    ]

    return {
        "total_workspaces_found": workspace_summary["total_workspaces_found"],
        "validated_pass_count": workspace_summary["validated_pass_count"],
        "validated_fail_count": workspace_summary["validated_fail_count"],
        "missing_validation_count": workspace_summary["missing_validation_count"],
        "latest_validated_workspace_mode_count": len(
            workspace_summary["latest_validated_workspace_per_mode"]
        ),
        "latest_validated_workspace_per_mode": workspace_summary["latest_validated_workspace_per_mode"],
        "latest_workspace_overall": latest_workspace_overall,
        "workspaces_missing_validation": workspaces_missing_validation,
        "summary_line": (
            f"Real pilot workspace summary currently shows {workspace_summary['total_workspaces_found']} "
            f"workspace folders, {workspace_summary['validated_pass_count']} PASS, "
            f"{workspace_summary['validated_fail_count']} FAIL, and "
            f"{workspace_summary['missing_validation_count']} missing validation artifacts."
        ),
    }


def build_contract_validation_status(contract_validation: dict[str, Any]) -> dict[str, Any]:
    inputs = contract_validation.get("inputs", [])
    total_warning_count = sum(
        int(input_result.get("warning_count", 0))
        for input_result in inputs
        if isinstance(input_result, dict)
    )
    total_error_count = sum(
        int(input_result.get("error_count", 0))
        for input_result in inputs
        if isinstance(input_result, dict)
    )

    summarized_inputs: list[dict[str, Any]] = []
    for input_result in inputs:
        if not isinstance(input_result, dict):
            continue
        summarized_inputs.append(
            {
                "input_path": display_path(input_result.get("input_path")),
                "input_name": Path(str(input_result.get("input_path"))).name,
                "detected_format": input_result.get("detected_format"),
                "passed": input_result.get("passed"),
                "warning_count": input_result.get("warning_count"),
                "error_count": input_result.get("error_count"),
                "entity_count": input_result.get("entity_count"),
                "ticket_count": input_result.get("ticket_count"),
                "record_count": input_result.get("record_count"),
            }
        )

    return {
        "overall_passed": contract_validation["overall_passed"],
        "input_count": len(summarized_inputs),
        "total_warning_count": total_warning_count,
        "total_error_count": total_error_count,
        "inputs": summarized_inputs,
        "summary_line": (
            f"Contract validation currently reports "
            f"{'PASS' if contract_validation['overall_passed'] else 'FAIL'} across "
            f"{len(summarized_inputs)} checked inputs with {total_warning_count} warnings and "
            f"{total_error_count} errors."
        ),
    }


def build_strongest_current_evidence(
    current_evaluation_position: dict[str, Any],
) -> dict[str, Any]:
    strongest = current_evaluation_position["strongest_evidence_modality"]
    return {
        **strongest,
        "summary_line": (
            f"{strongest['display_name']} on `{strongest['largest_slice']}` is the strongest current "
            f"evidence: {strongest['label_count']} labels, calibrated IML "
            f"{format_percent(float(strongest['calibrated_iml_accuracy']))}, and a "
            f"{format_delta(float(strongest['margin_vs_best_non_calibrated']))} lead over the best "
            "non-calibrated method."
        ),
    }


def build_weakest_current_area(
    *,
    ingest_coverage: dict[str, Any],
    workspace_readiness: dict[str, Any],
    current_evaluation_position: dict[str, Any],
) -> dict[str, Any]:
    if workspace_readiness["missing_validation_count"] > 0:
        latest_workspace_overall = workspace_readiness.get("latest_workspace_overall") or {}
        secondary_note = ""
        missing_eval_modes = ingest_coverage["modes_without_top_level_eval_evidence"]
        if missing_eval_modes:
            secondary_note = (
                f" The top-level ingest comparison also does not yet cover "
                f"{', '.join(f'`{mode}`' for mode in missing_eval_modes)}."
            )
        return {
            "area": "workspace_readiness",
            "reason": (
                f"Workspace validation is the current weakest area because "
                f"{workspace_readiness['missing_validation_count']} of "
                f"{workspace_readiness['total_workspaces_found']} discovered real pilot workspaces "
                "are still missing validation artifacts."
                + secondary_note
            ),
            "evidence": workspace_readiness["summary_line"],
            "latest_workspace_path": latest_workspace_overall.get("workspace_path"),
        }

    weakest_modality = current_evaluation_position["modality_needing_more_data"]
    return {
        "area": "evaluation_coverage",
        "reason": (
            f"{weakest_modality['display_name']} remains the thinnest evaluated evidence path at "
            f"{weakest_modality['label_count']} labels on `{weakest_modality['largest_slice']}`."
        ),
        "evidence": weakest_modality["selection_basis"],
        "latest_workspace_path": None,
    }


def build_immediate_next_recommended_step(
    weakest_current_area: dict[str, Any],
    current_evaluation_position: dict[str, Any],
) -> dict[str, Any]:
    if weakest_current_area["area"] == "workspace_readiness":
        workspace_path = weakest_current_area.get("latest_workspace_path")
        workspace_path_text = f"`{workspace_path}`" if workspace_path else "the active real pilot workspace"
        return {
            "area": "workspace_readiness",
            "step": (
                f"Run the real pilot workspace validator against {workspace_path_text}, then rebuild "
                "the workspace summary and this system summary so live-pilot readiness has an explicit "
                "validation artifact behind it."
            ),
        }

    weakest_modality = current_evaluation_position["modality_needing_more_data"]
    return {
        "area": "evaluation_coverage",
        "step": (
            f"Add one more labeled {weakest_modality['display_name']} slice so the thinnest "
            "evaluated modality moves beyond its current evidence base."
        ),
    }


def build_validation_state(
    bundle_package_readiness: dict[str, Any],
    workspace_readiness: dict[str, Any],
    contract_validation_status: dict[str, Any],
) -> dict[str, Any]:
    return {
        "pilot_bundle_validation": {
            "validated_pass_count": bundle_package_readiness["validated_pass_count"],
            "validated_fail_count": bundle_package_readiness["validated_fail_count"],
            "missing_validation_count": bundle_package_readiness["missing_validation_count"],
        },
        "workspace_validation": {
            "validated_pass_count": workspace_readiness["validated_pass_count"],
            "validated_fail_count": workspace_readiness["validated_fail_count"],
            "missing_validation_count": workspace_readiness["missing_validation_count"],
        },
        "contract_validation": {
            "overall_passed": contract_validation_status["overall_passed"],
            "input_count": contract_validation_status["input_count"],
            "total_warning_count": contract_validation_status["total_warning_count"],
            "total_error_count": contract_validation_status["total_error_count"],
        },
    }


def build_summary(
    *,
    source_artifact_paths_used: list[Path],
    ingest_comparison: dict[str, Any],
    package_summary: dict[str, Any],
    bundle_validation_summary: dict[str, Any],
    workspace_summary: dict[str, Any],
    contract_validation: dict[str, Any],
) -> dict[str, Any]:
    current_evaluation_position = build_current_evaluation_position(ingest_comparison)
    ingest_coverage = build_ingest_coverage(
        ingest_comparison,
        package_summary,
        contract_validation,
    )
    bundle_package_readiness = build_bundle_package_readiness(
        package_summary,
        bundle_validation_summary,
    )
    workspace_readiness = build_workspace_readiness(workspace_summary)
    contract_validation_status = build_contract_validation_status(contract_validation)
    strongest_current_evidence = build_strongest_current_evidence(current_evaluation_position)
    weakest_current_area = build_weakest_current_area(
        ingest_coverage=ingest_coverage,
        workspace_readiness=workspace_readiness,
        current_evaluation_position=current_evaluation_position,
    )
    immediate_next_recommended_step = build_immediate_next_recommended_step(
        weakest_current_area,
        current_evaluation_position,
    )

    return {
        "summary_type": "support_v1_system_summary",
        "generated_at": datetime.now().astimezone().isoformat(),
        "run_command_powershell": RUN_COMMAND,
        "what_this_adds": WHAT_THIS_ADDS,
        "source_artifacts_used": [project_relative_path(path) for path in source_artifact_paths_used],
        "current_evaluation_position": current_evaluation_position,
        "ingest_coverage": ingest_coverage,
        "bundle_package_readiness": bundle_package_readiness,
        "workspace_readiness": workspace_readiness,
        "contract_validation_status": contract_validation_status,
        "validation_state": build_validation_state(
            bundle_package_readiness,
            workspace_readiness,
            contract_validation_status,
        ),
        "strongest_current_evidence": strongest_current_evidence,
        "weakest_current_area": weakest_current_area,
        "immediate_next_recommended_step": immediate_next_recommended_step,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    evaluation = summary["current_evaluation_position"]
    ingest_coverage = summary["ingest_coverage"]
    bundle_package_readiness = summary["bundle_package_readiness"]
    workspace_readiness = summary["workspace_readiness"]
    contract_validation_status = summary["contract_validation_status"]
    strongest_current_evidence = summary["strongest_current_evidence"]
    weakest_current_area = summary["weakest_current_area"]
    immediate_next_recommended_step = summary["immediate_next_recommended_step"]

    latest_package_overall = bundle_package_readiness.get("latest_package_overall")
    latest_workspace_overall = workspace_readiness.get("latest_workspace_overall")

    lines = [
        "# Support V1 System Summary",
        "",
        f"Run with `{summary['run_command_powershell']}`.",
        "",
        summary["what_this_adds"],
        "",
        f"- Generated at: `{summary['generated_at']}`",
        "- Source artifacts used:",
    ]

    for path in summary["source_artifacts_used"]:
        lines.append(f"  - `{path}`")

    lines.extend(
        [
            "",
            "## Current Evaluation Position",
            "",
            f"- {evaluation['summary_line']}",
            f"- Overall conclusion: {evaluation['overall_conclusion']}",
            "",
            "## Ingest Coverage",
            "",
            f"- {ingest_coverage['summary_line']}",
            f"- Supported modes: {', '.join(f'`{mode}`' for mode in ingest_coverage['supported_modes'])}",
            (
                "- Top-level comparison gap: none"
                if not ingest_coverage["modes_without_top_level_eval_evidence"]
                else "- Top-level comparison gap: "
                + ", ".join(f'`{mode}`' for mode in ingest_coverage["modes_without_top_level_eval_evidence"])
            ),
            f"- Contract-validated formats: {', '.join(f'`{fmt}`' for fmt in ingest_coverage['validated_contract_formats'])}",
            "",
            "## Bundle/Package Readiness",
            "",
            f"- {bundle_package_readiness['summary_line']}",
        ]
    )

    if isinstance(latest_package_overall, dict):
        lines.append(
            f"- Latest package overall: `{latest_package_overall['mode']}` at "
            f"`{latest_package_overall['latest_package_folder']}`"
        )

    lines.extend(
        [
            "",
            "## Workspace Readiness",
            "",
            f"- {workspace_readiness['summary_line']}",
        ]
    )

    if isinstance(latest_workspace_overall, dict):
        lines.append(
            f"- Latest workspace overall: `{latest_workspace_overall.get('workspace_path')}` "
            f"({display_mode(latest_workspace_overall.get('mode'))}, "
            f"status `{latest_workspace_overall.get('validation_status')}`)"
        )

    if workspace_readiness["workspaces_missing_validation"]:
        lines.append(
            "- Workspaces missing validation artifacts: "
            + ", ".join(f"`{path}`" for path in workspace_readiness["workspaces_missing_validation"])
        )

    lines.extend(
        [
            "",
            "## Contract Validation Status",
            "",
            f"- {contract_validation_status['summary_line']}",
        ]
    )

    for input_result in contract_validation_status["inputs"]:
        lines.append(
            f"- `{input_result['input_name']}`: "
            f"{'PASS' if input_result['passed'] else 'FAIL'} "
            f"({input_result['detected_format']}, "
            f"{input_result['warning_count']} warnings, {input_result['error_count']} errors)"
        )

    lines.extend(
        [
            "",
            "## Strongest Current Evidence",
            "",
            f"- {strongest_current_evidence['summary_line']}",
            "",
            "## Weakest Current Area",
            "",
            f"- {weakest_current_area['reason']}",
            f"- Evidence: {weakest_current_area['evidence']}",
            "",
            "## Immediate Next Recommended Step",
            "",
            f"- {immediate_next_recommended_step['step']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    used_paths: list[Path] = []
    ingest_comparison = load_json_object(INGEST_COMPARISON_PATH, used_paths=used_paths)
    package_summary = load_json_object(PACKAGE_SUMMARY_PATH, used_paths=used_paths)
    bundle_validation_summary = load_json_object(
        BUNDLE_VALIDATION_SUMMARY_PATH,
        used_paths=used_paths,
    )
    workspace_summary = load_json_object(WORKSPACE_SUMMARY_PATH, used_paths=used_paths)
    contract_validation = load_json_object(CONTRACT_VALIDATION_PATH, used_paths=used_paths)
    record_optional_existing_path(READINESS_MEMO_PATH, used_paths=used_paths)

    summary = build_summary(
        source_artifact_paths_used=used_paths,
        ingest_comparison=ingest_comparison,
        package_summary=package_summary,
        bundle_validation_summary=bundle_validation_summary,
        workspace_summary=workspace_summary,
        contract_validation=contract_validation,
    )
    markdown = render_markdown(summary)

    write_json_manifest(SUMMARY_JSON_PATH, summary)
    write_report(SUMMARY_MARKDOWN_PATH, markdown)

    for path in used_paths:
        print(f"source_artifact_path: {project_relative_path(path)}")
    print(f"summary_json_path: {project_relative_path(SUMMARY_JSON_PATH)}")
    print(f"summary_markdown_path: {project_relative_path(SUMMARY_MARKDOWN_PATH)}")


if __name__ == "__main__":
    main()
