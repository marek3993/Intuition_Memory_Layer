from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
REAL_PILOT_WORKSPACES_DIR = ARTIFACTS_DIR / "real_pilot_workspaces"
WORKSPACE_MANIFEST_FILENAME = "workspace_manifest.json"
VALIDATION_RESULT_FILENAME = "validation_result.json"
PILOT_PACKAGE_MANIFEST_FILENAME = "pilot_package_manifest.json"
HANDOFF_MANIFEST_FILENAME = "handoff_manifest.json"
VALID_MODES = {
    "labeled_support",
    "raw_ingest",
    "csv_ingest",
    "mapped_ingest",
    "zendesk_like",
}
REQUIRED_SUBFOLDER_NAMES = (
    "intake",
    "inputs",
    "evaluation",
    "decision",
    "references",
)
REQUIRED_INTAKE_FILENAMES = (
    "real_export_intake_template.md",
    "real_export_field_inventory_template.csv",
    "real_export_onboarding_checklist.md",
)
MODE_REQUIRED_INTAKE_FILENAMES = {
    "mapped_ingest": (
        "helpdesk_export_mapping_template.json",
    ),
}
REQUIRED_DECISION_FILENAMES = (
    "support_v1_pilot_scorecard_template.csv",
    "support_v1_pilot_decision_memo_template.md",
    "support_v1_roi_model_template.csv",
)
REQUIRED_REFERENCE_FILENAMES = (
    "ARTIFACT_INDEX.md",
    "FIRST_LIVE_PILOT_RUNBOOK.md",
    "README_RUNBOOK.md",
    "executive_status_brief.md",
    "helpdesk_export_contract.md",
    "investor_value_brief.md",
    "pilot_handoff_summary.md",
    "schema.md",
    "support_v1_readiness_memo.md",
    "support_v1_roi_model.md",
)
REQUIRED_EVALUATION_FILENAMES = {
    "labeled_support": (
        "latest_support_label_evaluation.json",
        "latest_support_label_review.csv",
        "support_label_pack_comparison.json",
        "support_label_pack_comparison.md",
    ),
    "raw_ingest": (
        "latest_support_raw_ingest_label_evaluation.json",
        "latest_support_raw_ingest_label_review.csv",
        "support_raw_ingest_pack_comparison.json",
        "support_raw_ingest_pack_comparison.md",
    ),
    "csv_ingest": (
        "latest_support_csv_ingest_label_evaluation.json",
        "latest_support_csv_ingest_label_review.csv",
        "support_csv_ingest_pack_comparison.json",
        "support_csv_ingest_pack_comparison.md",
    ),
    "mapped_ingest": (
        "latest_support_mapped_ingest_label_evaluation.json",
        "latest_support_mapped_ingest_label_review.csv",
        "support_mapped_ingest_pack_comparison.json",
        "support_mapped_ingest_pack_comparison.md",
    ),
    "zendesk_like": (
        "latest_support_zendesk_like_label_evaluation.json",
        "latest_support_zendesk_like_label_review.csv",
        "support_zendesk_like_pack_comparison.json",
        "support_zendesk_like_pack_comparison.md",
    ),
}
WARNING_EVALUATION_FILENAMES = {
    "labeled_support": (
        "latest_support_label_errors.csv",
        "latest_support_label_route_changes.csv",
        "support_label_pack_decision_memo.md",
    ),
    "raw_ingest": (
        "helpdesk_export_contract_validation.json",
        "support_ingest_modality_comparison.json",
        "support_ingest_modality_comparison.md",
    ),
    "csv_ingest": (
        "helpdesk_export_contract_validation.json",
        "support_ingest_modality_comparison.json",
        "support_ingest_modality_comparison.md",
    ),
    "mapped_ingest": (
        "helpdesk_export_contract_validation.json",
        "support_ingest_modality_comparison.json",
        "support_ingest_modality_comparison.md",
    ),
    "zendesk_like": (
        "helpdesk_export_contract_validation.json",
        "support_ingest_modality_comparison.json",
        "support_ingest_modality_comparison.md",
    ),
}


@dataclass
class ValidationResult:
    workspace_path: Path
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    selected_mode: str | None = None

    @property
    def passed(self) -> bool:
        return not self.errors

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def to_dict(self, validation_output_path: Path) -> dict[str, Any]:
        return {
            "workspace_path": project_relative_path(self.workspace_path),
            "validated_at": datetime.now().astimezone().isoformat(),
            "passed": self.passed,
            "selected_mode": self.selected_mode,
            "warning_count": len(self.warnings),
            "error_count": len(self.errors),
            "warnings": self.warnings,
            "errors": self.errors,
            "validation_output_path": project_relative_path(validation_output_path),
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that one support_v1 real pilot workspace is structurally complete "
            "and ready for use, then write validation_result.json into that workspace."
        )
    )
    parser.add_argument(
        "--workspace-path",
        required=True,
        help=(
            "Path to a workspace folder under "
            "use_cases/support_v1/artifacts/real_pilot_workspaces/."
        ),
    )
    return parser.parse_args(argv)


def project_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved)


def resolve_input_path(path_value: str) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate.resolve()
    return (PROJECT_ROOT / candidate).resolve()


def resolve_manifest_path(path_value: str) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate.resolve()
    return (PROJECT_ROOT / candidate).resolve()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_name(f"{path.stem}.{uuid4().hex}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_path.replace(path)


def load_json_object(
    path: Path,
    result: ValidationResult,
    description: str,
) -> dict[str, Any] | None:
    if not path.exists():
        result.error(f"{description} does not exist: {project_relative_path(path)}")
        return None

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        result.error(f"{description} is not valid JSON: {project_relative_path(path)} ({exc})")
        return None
    except OSError as exc:
        result.error(f"Failed to read {description}: {project_relative_path(path)} ({exc})")
        return None

    if not isinstance(payload, dict):
        result.error(
            f"{description} must contain a top-level JSON object: {project_relative_path(path)}"
        )
        return None
    return payload


def require_string(
    payload: dict[str, Any],
    key: str,
    result: ValidationResult,
    context: str,
) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        result.error(f"{context} is missing required string field '{key}'.")
        return None
    return value.strip()


def require_list(
    payload: dict[str, Any],
    key: str,
    result: ValidationResult,
    context: str,
) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        result.error(f"{context} is missing required list field '{key}'.")
        return []
    return value


def require_object(
    payload: dict[str, Any],
    key: str,
    result: ValidationResult,
    context: str,
) -> dict[str, Any] | None:
    value = payload.get(key)
    if not isinstance(value, dict):
        result.error(f"{context} is missing required object field '{key}'.")
        return None
    return value


def validate_workspace_root(workspace_path: Path, result: ValidationResult) -> bool:
    if not workspace_path.exists():
        result.error(f"Workspace folder does not exist: {project_relative_path(workspace_path)}")
        return False
    if not workspace_path.is_dir():
        result.error(f"Workspace path is not a folder: {project_relative_path(workspace_path)}")
        return False
    try:
        workspace_path.relative_to(REAL_PILOT_WORKSPACES_DIR.resolve())
    except ValueError:
        result.error(
            "Workspace folder must live under "
            f"{project_relative_path(REAL_PILOT_WORKSPACES_DIR)}."
        )
        return False
    return True


def validate_manifest_metadata(
    manifest: dict[str, Any],
    workspace_path: Path,
    result: ValidationResult,
) -> None:
    context = "workspace manifest"
    workspace_type = require_string(manifest, "workspace_type", result, context)
    if workspace_type is not None and workspace_type != "support_v1_real_pilot_workspace":
        result.error(
            "workspace manifest has unexpected workspace_type "
            f"'{workspace_type}'."
        )

    selected_mode = require_string(manifest, "selected_mode", result, context)
    if selected_mode is not None:
        result.selected_mode = selected_mode
        if selected_mode not in VALID_MODES:
            result.error(
                "workspace manifest selected_mode must be one of "
                f"{', '.join(sorted(VALID_MODES))}; got '{selected_mode}'."
            )

    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip():
        result.warn("workspace manifest is missing a non-empty 'description' field.")

    generated_at = manifest.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at.strip():
        result.warn("workspace manifest is missing a non-empty 'generated_at' field.")
    else:
        try:
            datetime.fromisoformat(generated_at)
        except ValueError:
            result.warn("workspace manifest 'generated_at' is not valid ISO 8601.")

    manifest_workspace_path = manifest.get("workspace_path")
    expected_workspace_path = project_relative_path(workspace_path)
    if manifest_workspace_path != expected_workspace_path:
        result.warn(
            "workspace manifest 'workspace_path' does not match the current folder: "
            f"{manifest_workspace_path!r} != {expected_workspace_path!r}."
        )

    manifest_workspace_absolute = manifest.get("workspace_path_absolute")
    expected_workspace_absolute = str(workspace_path.resolve())
    if manifest_workspace_absolute != expected_workspace_absolute:
        result.warn(
            "workspace manifest 'workspace_path_absolute' does not match the current folder."
        )

    manifest_path_value = manifest.get("manifest_path")
    expected_manifest_path = project_relative_path(workspace_path / WORKSPACE_MANIFEST_FILENAME)
    if manifest_path_value != expected_manifest_path:
        result.warn(
            "workspace manifest 'manifest_path' does not match the current manifest location."
        )

    project_root_value = manifest.get("project_root")
    expected_project_root = str(PROJECT_ROOT.resolve())
    if project_root_value != expected_project_root:
        result.warn("workspace manifest 'project_root' does not match the repository root.")


def validate_subfolders(
    manifest: dict[str, Any],
    workspace_path: Path,
    result: ValidationResult,
) -> None:
    subfolders = require_object(manifest, "subfolders", result, "workspace manifest")
    if subfolders is None:
        return

    for subfolder_name in REQUIRED_SUBFOLDER_NAMES:
        subfolder_path = workspace_path / subfolder_name
        manifest_value = subfolders.get(subfolder_name)
        if not isinstance(manifest_value, str) or not manifest_value.strip():
            result.error(
                f"workspace manifest subfolders entry '{subfolder_name}' is missing or empty."
            )
        else:
            expected_relative_path = project_relative_path(subfolder_path)
            if manifest_value != expected_relative_path:
                result.warn(
                    f"workspace manifest subfolders entry '{subfolder_name}' does not match "
                    "the current folder layout."
                )

        if not subfolder_path.exists():
            result.error(f"Required subfolder is missing: {project_relative_path(subfolder_path)}")
            continue
        if not subfolder_path.is_dir():
            result.error(f"Required subfolder is not a folder: {project_relative_path(subfolder_path)}")


def validate_required_files(
    workspace_path: Path,
    selected_mode: str | None,
    result: ValidationResult,
) -> None:
    required_file_groups = [
        ("intake", REQUIRED_INTAKE_FILENAMES),
        ("decision", REQUIRED_DECISION_FILENAMES),
        ("references", REQUIRED_REFERENCE_FILENAMES),
    ]

    if selected_mode in MODE_REQUIRED_INTAKE_FILENAMES:
        required_file_groups.append(
            ("intake", MODE_REQUIRED_INTAKE_FILENAMES[selected_mode])
        )

    for subfolder_name, required_filenames in required_file_groups:
        subfolder_path = workspace_path / subfolder_name
        for filename in required_filenames:
            candidate_path = subfolder_path / filename
            if not candidate_path.exists():
                result.error(f"Required file is missing: {project_relative_path(candidate_path)}")
            elif not candidate_path.is_file():
                result.error(f"Required file path is not a file: {project_relative_path(candidate_path)}")


def validate_evaluation_artifacts(
    workspace_path: Path,
    selected_mode: str | None,
    result: ValidationResult,
) -> None:
    evaluation_dir = workspace_path / "evaluation"
    current_mode_dir = evaluation_dir / "current_mode_artifacts"

    if not current_mode_dir.exists():
        result.error(
            f"Required evaluation subfolder is missing: {project_relative_path(current_mode_dir)}"
        )
        return
    if not current_mode_dir.is_dir():
        result.error(
            f"Required evaluation subfolder is not a folder: {project_relative_path(current_mode_dir)}"
        )
        return

    if selected_mode is None or selected_mode not in REQUIRED_EVALUATION_FILENAMES:
        return

    for filename in REQUIRED_EVALUATION_FILENAMES[selected_mode]:
        candidate_path = current_mode_dir / filename
        if not candidate_path.exists():
            result.error(f"Required evaluation file is missing: {project_relative_path(candidate_path)}")
        elif not candidate_path.is_file():
            result.error(
                f"Required evaluation file path is not a file: {project_relative_path(candidate_path)}"
            )

    for filename in WARNING_EVALUATION_FILENAMES.get(selected_mode, ()):
        candidate_path = current_mode_dir / filename
        if not candidate_path.exists():
            result.warn(
                f"Recommended evaluation artifact is missing: {project_relative_path(candidate_path)}"
            )
        elif not candidate_path.is_file():
            result.warn(
                f"Recommended evaluation artifact path is not a file: {project_relative_path(candidate_path)}"
            )


def validate_manifest_copied_artifacts(
    manifest: dict[str, Any],
    workspace_path: Path,
    result: ValidationResult,
) -> None:
    copied_artifacts = require_list(
        manifest,
        "source_artifacts_copied_in",
        result,
        "workspace manifest",
    )
    if not copied_artifacts:
        result.error("workspace manifest 'source_artifacts_copied_in' must not be empty.")
        return

    for index, entry in enumerate(copied_artifacts, start=1):
        if not isinstance(entry, dict):
            result.error(
                f"workspace manifest copied artifact entry #{index} must be an object."
            )
            continue

        context = f"workspace manifest copied artifact entry #{index}"
        label = require_string(entry, "label", result, context)
        workspace_output_path = require_string(entry, "workspace_output_path", result, context)

        if workspace_output_path is not None:
            resolved_output_path = resolve_manifest_path(workspace_output_path)
            if not resolved_output_path.exists():
                result.error(
                    f"Copied artifact '{label or index}' is missing from the workspace: "
                    f"{workspace_output_path}"
                )
            else:
                try:
                    resolved_output_path.relative_to(workspace_path)
                except ValueError:
                    result.error(
                        f"Copied artifact '{label or index}' points outside the workspace: "
                        f"{workspace_output_path}"
                    )

        source_path = entry.get("source_path")
        if isinstance(source_path, str) and source_path.strip():
            resolved_source_path = resolve_manifest_path(source_path)
            if not resolved_source_path.exists():
                result.warn(
                    f"Source artifact reference for '{label or index}' does not exist anymore: "
                    f"{source_path}"
                )
        else:
            result.warn(f"Copied artifact '{label or index}' is missing 'source_path'.")

        source_manifest_path = entry.get("source_manifest_path")
        if source_manifest_path is not None:
            if not isinstance(source_manifest_path, str) or not source_manifest_path.strip():
                result.warn(
                    f"Copied artifact '{label or index}' has an invalid 'source_manifest_path'."
                )
            else:
                resolved_source_manifest_path = resolve_manifest_path(source_manifest_path)
                if not resolved_source_manifest_path.exists():
                    result.warn(
                        f"Source manifest reference for '{label or index}' does not exist anymore: "
                        f"{source_manifest_path}"
                    )

    latest_package_dir = workspace_path / "evaluation" / "latest_pilot_package"
    if latest_package_dir.exists():
        manifest_path = latest_package_dir / PILOT_PACKAGE_MANIFEST_FILENAME
        if not manifest_path.exists():
            result.error(
                f"latest_pilot_package is missing its manifest: {project_relative_path(manifest_path)}"
            )

    latest_handoff_dir = workspace_path / "evaluation" / "latest_pilot_handoff_bundle"
    if latest_handoff_dir.exists():
        manifest_path = latest_handoff_dir / HANDOFF_MANIFEST_FILENAME
        if not manifest_path.exists():
            result.error(
                "latest_pilot_handoff_bundle is missing its manifest: "
                f"{project_relative_path(manifest_path)}"
            )


def validate_optional_artifacts(
    manifest: dict[str, Any],
    result: ValidationResult,
) -> None:
    optional_artifacts_missing = require_list(
        manifest,
        "optional_artifacts_missing",
        result,
        "workspace manifest",
    )
    for index, entry in enumerate(optional_artifacts_missing, start=1):
        if not isinstance(entry, dict):
            result.warn(
                f"workspace manifest optional artifact entry #{index} must be an object."
            )
            continue

        label = entry.get("label")
        expected_source_path = entry.get("expected_source_path")
        if not isinstance(label, str) or not label.strip():
            result.warn(
                f"workspace manifest optional artifact entry #{index} is missing 'label'."
            )
            continue
        if not isinstance(expected_source_path, str) or not expected_source_path.strip():
            result.warn(
                f"workspace manifest optional artifact '{label}' is missing "
                "'expected_source_path'."
            )
            continue
        result.warn(
            f"Optional artifact was not available when the workspace was initialized: "
            f"{label} ({expected_source_path})"
        )


def validate_workspace(workspace_path: Path) -> ValidationResult:
    result = ValidationResult(workspace_path=workspace_path)
    if not validate_workspace_root(workspace_path, result):
        return result

    manifest_path = workspace_path / WORKSPACE_MANIFEST_FILENAME
    manifest = load_json_object(manifest_path, result, "workspace manifest")
    if manifest is None:
        return result

    validate_manifest_metadata(manifest, workspace_path, result)
    validate_subfolders(manifest, workspace_path, result)
    validate_required_files(workspace_path, result.selected_mode, result)
    validate_evaluation_artifacts(workspace_path, result.selected_mode, result)
    validate_manifest_copied_artifacts(manifest, workspace_path, result)
    validate_optional_artifacts(manifest, result)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    workspace_path = resolve_input_path(args.workspace_path)
    validation_output_path = workspace_path / VALIDATION_RESULT_FILENAME

    result = validate_workspace(workspace_path)
    if workspace_path.exists() and workspace_path.is_dir():
        write_json(validation_output_path, result.to_dict(validation_output_path))

    print(f"workspace_path: {project_relative_path(workspace_path)}")
    print(f"status: {'PASS' if result.passed else 'FAIL'}")
    print(f"warning_count: {len(result.warnings)}")
    print(f"error_count: {len(result.errors)}")
    print(f"validation_output_path: {project_relative_path(validation_output_path)}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
