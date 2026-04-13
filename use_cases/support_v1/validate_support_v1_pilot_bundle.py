from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
PILOT_PACKAGE_MANIFEST_FILENAME = "pilot_package_manifest.json"
HANDOFF_MANIFEST_FILENAME = "handoff_manifest.json"
EXECUTION_BUNDLE_MANIFEST_FILENAME = "bundle_manifest.json"
VALIDATION_RESULT_FILENAME = "validation_result.json"
VALID_MODES = {
    "labeled_support",
    "raw_ingest",
    "csv_ingest",
    "mapped_ingest",
    "zendesk_like",
}
PILOT_PACKAGE_REQUIRED_DOC_FILENAMES = (
    "FIRST_LIVE_PILOT_RUNBOOK.md",
    "PILOT_PACKAGE_INDEX.md",
    "pilot_handoff_summary.md",
    "real_export_onboarding_checklist.md",
    "support_v1_pilot_decision_memo_template.md",
    "support_v1_pilot_scorecard.md",
    "support_v1_readiness_memo.md",
)
HANDOFF_REQUIRED_DOC_FILENAMES = (
    "ARTIFACT_INDEX.md",
    "FIRST_LIVE_PILOT_RUNBOOK.md",
    "PILOT_PACKAGE_INDEX.md",
    "executive_status_brief.md",
    "investor_value_brief.md",
    "pilot_handoff_summary.md",
    "support_v1_pilot_decision_memo_template.md",
    "support_v1_pilot_package_summary.json",
    "support_v1_pilot_package_summary.md",
    "support_v1_pilot_scorecard.md",
    "support_v1_readiness_memo.md",
    "support_v1_roi_model.md",
)
REQUIRED_EXECUTION_LABELS = {
    "labeled_support": (
        "main_json_evaluation_artifact",
        "review_csv",
        "comparison_json",
        "comparison_markdown",
    ),
    "raw_ingest": (
        "main_json_evaluation_artifact",
        "review_csv",
        "comparison_json",
        "comparison_markdown",
    ),
    "csv_ingest": (
        "main_json_evaluation_artifact",
        "review_csv",
        "comparison_json",
        "comparison_markdown",
    ),
    "mapped_ingest": (
        "main_json_evaluation_artifact",
        "review_csv",
        "comparison_json",
        "comparison_markdown",
    ),
    "zendesk_like": (
        "main_json_evaluation_artifact",
        "review_csv",
        "comparison_json",
        "comparison_markdown",
    ),
}
RECOMMENDED_EXECUTION_LABELS = {
    "labeled_support": (
        "focused_error_csv",
        "route_change_csv",
        "decision_memo_markdown",
    ),
    "raw_ingest": (
        "ingest_comparison_json",
        "ingest_comparison_markdown",
        "contract_validation_json",
    ),
    "csv_ingest": (
        "ingest_comparison_json",
        "ingest_comparison_markdown",
        "contract_validation_json",
    ),
    "mapped_ingest": (
        "ingest_comparison_json",
        "ingest_comparison_markdown",
        "contract_validation_json",
    ),
    "zendesk_like": (
        "ingest_comparison_json",
        "ingest_comparison_markdown",
        "contract_validation_json",
    ),
}


@dataclass
class ValidationResult:
    bundle_path: Path
    bundle_type_detected: str = "unknown"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def to_dict(self, validation_output_path: Path) -> dict[str, Any]:
        return {
            "bundle_path": project_relative_path(self.bundle_path),
            "bundle_type_detected": self.bundle_type_detected,
            "validated_at": datetime.now().astimezone().isoformat(),
            "passed": self.passed,
            "warning_count": len(self.warnings),
            "error_count": len(self.errors),
            "warnings": self.warnings,
            "errors": self.errors,
            "validation_output_path": project_relative_path(validation_output_path),
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a support_v1 pilot package or pilot handoff bundle and write "
            "validation_result.json inside the target bundle folder."
        )
    )
    parser.add_argument(
        "--bundle-path",
        required=True,
        help=(
            "Path to a folder under use_cases/support_v1/artifacts/pilot_packages/ "
            "or use_cases/support_v1/artifacts/pilot_handoff_bundles/."
        ),
    )
    return parser.parse_args(argv)


def project_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved)


def resolve_manifest_path(path_value: str) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate.resolve()
    return (PROJECT_ROOT / candidate).resolve()


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
        result.error(f"{description} must contain a top-level JSON object: {project_relative_path(path)}")
        return None
    return payload


def validate_path_reference(
    path_value: str,
    result: ValidationResult,
    description: str,
    *,
    level: str,
) -> None:
    resolved_path = resolve_manifest_path(path_value)
    if resolved_path.exists():
        return

    message = f"{description} is missing: {path_value}"
    if level == "warning":
        result.warn(message)
    else:
        result.error(message)


def validate_output_paths(
    output_paths: list[Any],
    result: ValidationResult,
    context: str,
) -> None:
    for index, path_value in enumerate(output_paths, start=1):
        if not isinstance(path_value, str) or not path_value.strip():
            result.error(f"{context} output_paths[{index}] must be a non-empty string.")
            continue
        validate_path_reference(
            path_value.strip(),
            result,
            f"{context} output_paths[{index}]",
            level="error",
        )


def validate_optional_missing_entries(
    entries: list[Any],
    result: ValidationResult,
    context: str,
) -> None:
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            result.warn(f"{context}[{index}] should be an object.")
            continue
        label = entry.get("label")
        expected_source_path = entry.get("expected_source_path")
        if isinstance(label, str) and isinstance(expected_source_path, str):
            result.warn(f"{context} reports missing optional item '{label}': {expected_source_path}")
            continue
        result.warn(f"{context}[{index}] is missing expected 'label'/'expected_source_path' fields.")


def validate_included_doc_entries(
    entries: list[Any],
    result: ValidationResult,
    *,
    context: str,
    output_key: str,
) -> None:
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            result.error(f"{context}[{index}] must be an object.")
            continue

        label = entry.get("label")
        if not isinstance(label, str) or not label.strip():
            result.error(f"{context}[{index}] is missing required string field 'label'.")

        output_path_value = entry.get(output_key)
        if not isinstance(output_path_value, str) or not output_path_value.strip():
            result.error(f"{context}[{index}] is missing required string field '{output_key}'.")
        else:
            validate_path_reference(
                output_path_value.strip(),
                result,
                f"{context}[{index}] {output_key}",
                level="error",
            )

        source_path_value = entry.get("source_path")
        if source_path_value is None:
            continue
        if not isinstance(source_path_value, str) or not source_path_value.strip():
            result.warn(f"{context}[{index}] has a blank 'source_path'.")
            continue
        validate_path_reference(
            source_path_value.strip(),
            result,
            f"{context}[{index}] source_path",
            level="warning",
        )


def detect_bundle_type(bundle_dir: Path) -> str:
    package_manifest_path = bundle_dir / PILOT_PACKAGE_MANIFEST_FILENAME
    handoff_manifest_path = bundle_dir / HANDOFF_MANIFEST_FILENAME

    if package_manifest_path.exists() and not handoff_manifest_path.exists():
        return "support_v1_pilot_package"
    if handoff_manifest_path.exists() and not package_manifest_path.exists():
        return "support_v1_pilot_handoff_bundle"
    if package_manifest_path.exists() and handoff_manifest_path.exists():
        return "ambiguous"

    if bundle_dir.name == "pilot_packages" or bundle_dir.parent.name == "pilot_packages":
        return "support_v1_pilot_package"
    if bundle_dir.name == "pilot_handoff_bundles" or bundle_dir.parent.name == "pilot_handoff_bundles":
        return "support_v1_pilot_handoff_bundle"

    return "unknown"


def validate_current_files(
    directory: Path,
    required_filenames: tuple[str, ...],
    result: ValidationResult,
    *,
    context: str,
) -> None:
    for filename in required_filenames:
        target_path = directory / filename
        if not target_path.is_file():
            result.error(f"{context} is missing required file: {project_relative_path(target_path)}")


def validate_execution_bundle(
    execution_bundle_dir: Path,
    result: ValidationResult,
    *,
    expected_mode: str | None,
    copied_into_handoff: bool,
) -> None:
    if not execution_bundle_dir.is_dir():
        result.error(
            "Execution bundle directory is missing: "
            f"{project_relative_path(execution_bundle_dir)}"
        )
        return

    manifest_path = execution_bundle_dir / EXECUTION_BUNDLE_MANIFEST_FILENAME
    manifest = load_json_object(manifest_path, result, "Execution bundle manifest")
    if manifest is None:
        return

    mode = require_string(manifest, "bundle_type", result, "Execution bundle manifest")
    if mode is not None and mode not in VALID_MODES:
        result.error(f"Execution bundle manifest bundle_type is not supported: {mode}")
    if expected_mode is not None and mode is not None and mode != expected_mode:
        result.error(
            "Execution bundle manifest bundle_type does not match the enclosing bundle: "
            f"{mode} != {expected_mode}"
        )

    bundle_output_folder = require_string(
        manifest,
        "bundle_output_folder",
        result,
        "Execution bundle manifest",
    )
    if bundle_output_folder is not None:
        resolved_output_folder = resolve_manifest_path(bundle_output_folder)
        if copied_into_handoff:
            pass
        elif resolved_output_folder != execution_bundle_dir.resolve():
            result.error(
                "Execution bundle manifest bundle_output_folder does not match the validated "
                f"directory: {bundle_output_folder}"
            )

    require_string(manifest, "generated_at", result, "Execution bundle manifest")
    require_string(manifest, "notes", result, "Execution bundle manifest")

    source_artifacts_used = require_list(
        manifest,
        "source_artifacts_used",
        result,
        "Execution bundle manifest",
    )
    output_paths = require_list(
        manifest,
        "bundle_output_paths",
        result,
        "Execution bundle manifest",
    )
    optional_missing = require_list(
        manifest,
        "optional_source_artifacts_missing",
        result,
        "Execution bundle manifest",
    )
    document_references = require_list(
        manifest,
        "document_references",
        result,
        "Execution bundle manifest",
    )

    labels_present: set[str] = set()
    current_file_names = {
        path.name for path in execution_bundle_dir.iterdir() if path.is_file()
    }

    for index, entry in enumerate(source_artifacts_used, start=1):
        if not isinstance(entry, dict):
            result.error(f"Execution bundle manifest source_artifacts_used[{index}] must be an object.")
            continue

        label = entry.get("label")
        if not isinstance(label, str) or not label.strip():
            result.error(
                f"Execution bundle manifest source_artifacts_used[{index}] is missing "
                "required string field 'label'."
            )
            continue
        labels_present.add(label.strip())

        source_path_value = entry.get("source_path")
        if isinstance(source_path_value, str) and source_path_value.strip():
            validate_path_reference(
                source_path_value.strip(),
                result,
                f"Execution bundle manifest source_artifacts_used[{index}] source_path",
                level="warning",
            )
        else:
            result.warn(
                "Execution bundle manifest source_artifacts_used["
                f"{index}] is missing a usable source_path."
            )

        bundle_output_path_value = entry.get("bundle_output_path")
        if not isinstance(bundle_output_path_value, str) or not bundle_output_path_value.strip():
            result.error(
                f"Execution bundle manifest source_artifacts_used[{index}] is missing "
                "required string field 'bundle_output_path'."
            )
            continue

        validate_path_reference(
            bundle_output_path_value.strip(),
            result,
            f"Execution bundle manifest source_artifacts_used[{index}] bundle_output_path",
            level="error",
        )
        current_bundle_file = execution_bundle_dir / Path(bundle_output_path_value).name
        if not current_bundle_file.is_file():
            result.error(
                "Execution bundle is missing the copied artifact referenced by the manifest: "
                f"{project_relative_path(current_bundle_file)}"
            )

    if mode in REQUIRED_EXECUTION_LABELS:
        for label in REQUIRED_EXECUTION_LABELS[mode]:
            if label not in labels_present:
                result.error(
                    "Execution bundle manifest is missing required artifact label "
                    f"'{label}' for mode '{mode}'."
                )

    if mode in RECOMMENDED_EXECUTION_LABELS:
        for label in RECOMMENDED_EXECUTION_LABELS[mode]:
            if label not in labels_present:
                result.warn(
                    "Execution bundle manifest is missing recommended artifact label "
                    f"'{label}' for mode '{mode}'."
                )

    validate_output_paths(output_paths, result, "Execution bundle manifest")
    validate_optional_missing_entries(
        optional_missing,
        result,
        "Execution bundle manifest optional_source_artifacts_missing",
    )

    for index, entry in enumerate(document_references, start=1):
        if not isinstance(entry, dict):
            result.warn(f"Execution bundle manifest document_references[{index}] should be an object.")
            continue
        path_value = entry.get("path")
        exists_value = entry.get("exists")
        if not isinstance(path_value, str) or not path_value.strip():
            result.warn(
                f"Execution bundle manifest document_references[{index}] is missing required string field 'path'."
            )
            continue
        resolved_path = resolve_manifest_path(path_value.strip())
        path_exists = resolved_path.exists()
        if path_exists and exists_value is False:
            result.warn(
                "Execution bundle manifest document_references["
                f"{index}] marks an existing document as missing: {path_value}"
            )
        if not path_exists and exists_value is True:
            result.warn(
                "Execution bundle manifest document_references["
                f"{index}] marks a missing document as present: {path_value}"
            )

    if EXECUTION_BUNDLE_MANIFEST_FILENAME not in current_file_names:
        result.error(
            "Execution bundle is missing its manifest file: "
            f"{project_relative_path(manifest_path)}"
        )


def validate_pilot_package_bundle(
    package_dir: Path,
    result: ValidationResult,
    *,
    copied_into_handoff: bool,
    expected_mode: str | None,
) -> None:
    manifest_path = package_dir / PILOT_PACKAGE_MANIFEST_FILENAME
    manifest = load_json_object(manifest_path, result, "Pilot package manifest")
    if manifest is None:
        return

    package_type = require_string(manifest, "package_type", result, "Pilot package manifest")
    if package_type is not None and package_type != "support_v1_pilot_package":
        result.error(
            "Pilot package manifest package_type must be "
            f"'support_v1_pilot_package', found '{package_type}'."
        )

    mode = require_string(manifest, "selected_mode", result, "Pilot package manifest")
    if mode is not None and mode not in VALID_MODES:
        result.error(f"Pilot package manifest selected_mode is not supported: {mode}")
    if expected_mode is not None and mode is not None and mode != expected_mode:
        result.error(
            "Pilot package manifest selected_mode does not match the enclosing handoff "
            f"bundle: {mode} != {expected_mode}"
        )

    package_output_folder = require_string(
        manifest,
        "package_output_folder",
        result,
        "Pilot package manifest",
    )
    if package_output_folder is not None:
        resolved_output_folder = resolve_manifest_path(package_output_folder)
        if copied_into_handoff:
            pass
        elif resolved_output_folder != package_dir.resolve():
            result.error(
                "Pilot package manifest package_output_folder does not match the validated "
                f"directory: {package_output_folder}"
            )

    require_string(manifest, "generated_at", result, "Pilot package manifest")
    require_string(manifest, "notes", result, "Pilot package manifest")

    source_execution_bundle = require_object(
        manifest,
        "source_execution_bundle_used",
        result,
        "Pilot package manifest",
    )
    included_docs = require_list(manifest, "included_docs", result, "Pilot package manifest")
    output_paths = require_list(manifest, "output_paths", result, "Pilot package manifest")
    optional_missing = require_list(
        manifest,
        "optional_docs_missing",
        result,
        "Pilot package manifest",
    )

    docs_dir = package_dir / "docs"
    execution_bundle_dir = package_dir / "execution_bundle"
    if not docs_dir.is_dir():
        result.error(f"Pilot package is missing docs directory: {project_relative_path(docs_dir)}")
    if not execution_bundle_dir.is_dir():
        result.error(
            "Pilot package is missing execution_bundle directory: "
            f"{project_relative_path(execution_bundle_dir)}"
        )

    if docs_dir.is_dir():
        validate_current_files(
            docs_dir,
            PILOT_PACKAGE_REQUIRED_DOC_FILENAMES,
            result,
            context="Pilot package docs directory",
        )

    validate_included_doc_entries(
        included_docs,
        result,
        context="Pilot package manifest included_docs",
        output_key="package_output_path",
    )
    validate_output_paths(output_paths, result, "Pilot package manifest")
    validate_optional_missing_entries(
        optional_missing,
        result,
        "Pilot package manifest optional_docs_missing",
    )

    if source_execution_bundle is not None:
        bundle_output_folder = require_string(
            source_execution_bundle,
            "bundle_output_folder",
            result,
            "Pilot package manifest source_execution_bundle_used",
        )
        bundle_manifest_path = require_string(
            source_execution_bundle,
            "bundle_manifest_path",
            result,
            "Pilot package manifest source_execution_bundle_used",
        )
        bundle_type = require_string(
            source_execution_bundle,
            "bundle_type",
            result,
            "Pilot package manifest source_execution_bundle_used",
        )
        require_string(
            source_execution_bundle,
            "bundle_generated_at",
            result,
            "Pilot package manifest source_execution_bundle_used",
        )
        if bundle_output_folder is not None:
            validate_path_reference(
                bundle_output_folder,
                result,
                "Pilot package manifest source_execution_bundle_used bundle_output_folder",
                level="warning",
            )
        if bundle_manifest_path is not None:
            validate_path_reference(
                bundle_manifest_path,
                result,
                "Pilot package manifest source_execution_bundle_used bundle_manifest_path",
                level="warning",
            )
        if mode is not None and bundle_type is not None and bundle_type != mode:
            result.error(
                "Pilot package manifest source_execution_bundle_used bundle_type does not "
                f"match selected_mode: {bundle_type} != {mode}"
            )

    if execution_bundle_dir.is_dir():
        validate_execution_bundle(
            execution_bundle_dir,
            result,
            expected_mode=mode,
            copied_into_handoff=True,
        )


def validate_pilot_handoff_bundle(bundle_dir: Path, result: ValidationResult) -> None:
    manifest_path = bundle_dir / HANDOFF_MANIFEST_FILENAME
    manifest = load_json_object(manifest_path, result, "Pilot handoff manifest")
    if manifest is None:
        return

    bundle_type = require_string(manifest, "bundle_type", result, "Pilot handoff manifest")
    if bundle_type is not None and bundle_type != "support_v1_pilot_handoff_bundle":
        result.error(
            "Pilot handoff manifest bundle_type must be "
            f"'support_v1_pilot_handoff_bundle', found '{bundle_type}'."
        )

    mode = require_string(manifest, "selected_mode", result, "Pilot handoff manifest")
    if mode is not None and mode not in VALID_MODES:
        result.error(f"Pilot handoff manifest selected_mode is not supported: {mode}")

    handoff_output_folder = require_string(
        manifest,
        "handoff_output_folder",
        result,
        "Pilot handoff manifest",
    )
    if handoff_output_folder is not None:
        resolved_output_folder = resolve_manifest_path(handoff_output_folder)
        if resolved_output_folder != bundle_dir.resolve():
            result.error(
                "Pilot handoff manifest handoff_output_folder does not match the validated "
                f"directory: {handoff_output_folder}"
            )

    require_string(manifest, "generated_at", result, "Pilot handoff manifest")
    require_string(manifest, "purpose_note", result, "Pilot handoff manifest")

    source_package_used = require_object(
        manifest,
        "source_package_used",
        result,
        "Pilot handoff manifest",
    )
    included_docs = require_list(manifest, "included_docs", result, "Pilot handoff manifest")
    output_paths = require_list(manifest, "output_paths", result, "Pilot handoff manifest")
    optional_missing = require_list(
        manifest,
        "optional_docs_missing",
        result,
        "Pilot handoff manifest",
    )

    validate_current_files(
        bundle_dir,
        HANDOFF_REQUIRED_DOC_FILENAMES,
        result,
        context="Pilot handoff bundle root",
    )
    validate_included_doc_entries(
        included_docs,
        result,
        context="Pilot handoff manifest included_docs",
        output_key="handoff_output_path",
    )
    validate_output_paths(output_paths, result, "Pilot handoff manifest")
    validate_optional_missing_entries(
        optional_missing,
        result,
        "Pilot handoff manifest optional_docs_missing",
    )

    expected_copied_package_dir: Path | None = None
    if source_package_used is not None:
        package_output_folder = require_string(
            source_package_used,
            "package_output_folder",
            result,
            "Pilot handoff manifest source_package_used",
        )
        package_manifest_path = require_string(
            source_package_used,
            "package_manifest_path",
            result,
            "Pilot handoff manifest source_package_used",
        )
        require_string(
            source_package_used,
            "package_generated_at",
            result,
            "Pilot handoff manifest source_package_used",
        )
        require_string(
            source_package_used,
            "package_resolution_source",
            result,
            "Pilot handoff manifest source_package_used",
        )
        if package_output_folder is not None:
            validate_path_reference(
                package_output_folder,
                result,
                "Pilot handoff manifest source_package_used package_output_folder",
                level="warning",
            )
            expected_copied_package_dir = bundle_dir / Path(package_output_folder).name
        if package_manifest_path is not None:
            validate_path_reference(
                package_manifest_path,
                result,
                "Pilot handoff manifest source_package_used package_manifest_path",
                level="warning",
            )

    copied_package_candidates = [
        path
        for path in bundle_dir.iterdir()
        if path.is_dir() and (path / PILOT_PACKAGE_MANIFEST_FILENAME).is_file()
    ]
    if not copied_package_candidates:
        result.error(
            "Pilot handoff bundle does not contain a copied pilot package directory with "
            f"{PILOT_PACKAGE_MANIFEST_FILENAME}."
        )
        return
    if len(copied_package_candidates) > 1:
        result.warn(
            "Pilot handoff bundle contains multiple copied pilot package directories; "
            "the first matching directory will be validated."
        )

    copied_package_dir = copied_package_candidates[0]
    if expected_copied_package_dir is not None:
        if expected_copied_package_dir.is_dir():
            copied_package_dir = expected_copied_package_dir
        else:
            result.error(
                "Pilot handoff bundle is missing the copied package directory named by "
                f"source_package_used.package_output_folder: {project_relative_path(expected_copied_package_dir)}"
            )
            return

    validate_pilot_package_bundle(
        copied_package_dir,
        result,
        copied_into_handoff=True,
        expected_mode=mode,
    )


def write_validation_result(bundle_dir: Path, result: ValidationResult) -> Path:
    output_path = bundle_dir / VALIDATION_RESULT_FILENAME
    payload = result.to_dict(output_path)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return output_path


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    bundle_dir = Path(args.bundle_path).resolve()
    result = ValidationResult(bundle_path=bundle_dir)

    if not bundle_dir.exists():
        print(f"bundle_path: {bundle_dir}")
        print("bundle_type_detected: unknown")
        print("result: FAIL")
        print("warning_count: 0")
        print("error_count: 1")
        print("validation_output_path: <not written>")
        return 1

    if not bundle_dir.is_dir():
        print(f"bundle_path: {bundle_dir}")
        print("bundle_type_detected: unknown")
        print("result: FAIL")
        print("warning_count: 0")
        print("error_count: 1")
        print("validation_output_path: <not written>")
        return 1

    result.bundle_type_detected = detect_bundle_type(bundle_dir)
    if result.bundle_type_detected == "ambiguous":
        result.error(
            "Bundle directory contains both pilot package and handoff manifests; bundle type "
            "cannot be determined safely."
        )
    elif result.bundle_type_detected == "support_v1_pilot_package":
        validate_pilot_package_bundle(
            bundle_dir,
            result,
            copied_into_handoff=False,
            expected_mode=None,
        )
    elif result.bundle_type_detected == "support_v1_pilot_handoff_bundle":
        validate_pilot_handoff_bundle(bundle_dir, result)
    else:
        result.error(
            "Unsupported bundle type. Expected a folder under "
            "use_cases/support_v1/artifacts/pilot_packages/ or "
            "use_cases/support_v1/artifacts/pilot_handoff_bundles/."
        )

    validation_output_path = write_validation_result(bundle_dir, result)

    print(f"bundle_path: {project_relative_path(bundle_dir)}")
    print(f"bundle_type_detected: {result.bundle_type_detected}")
    print(f"result: {'PASS' if result.passed else 'FAIL'}")
    print(f"warning_count: {len(result.warnings)}")
    print(f"error_count: {len(result.errors)}")
    print(f"validation_output_path: {project_relative_path(validation_output_path)}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
