from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from build_support_v1_pilot_execution_bundle import (
    MODE_CONFIGS,
    project_relative_path,
    sanitize_bundle_name,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
PILOT_PACKAGES_DIR = ARTIFACTS_DIR / "pilot_packages"
PILOT_HANDOFF_BUNDLES_DIR = ARTIFACTS_DIR / "pilot_handoff_bundles"
PILOT_PACKAGE_MANIFEST_FILENAME = "pilot_package_manifest.json"
PILOT_PACKAGE_INDEX_FILENAME = "PILOT_PACKAGE_INDEX.md"
HANDOFF_MANIFEST_FILENAME = "handoff_manifest.json"
PACKAGE_SUMMARY_JSON_PATH = ARTIFACTS_DIR / "support_v1_pilot_package_summary.json"
PACKAGE_SUMMARY_MARKDOWN_PATH = ARTIFACTS_DIR / "support_v1_pilot_package_summary.md"


@dataclass(frozen=True)
class HandoffDocument:
    label: str
    path: Path
    note: str


COMMON_HANDOFF_DOCUMENTS: tuple[HandoffDocument, ...] = (
    HandoffDocument(
        label="pilot_package_summary_json",
        path=PACKAGE_SUMMARY_JSON_PATH,
        note="Machine-readable summary of the latest reviewer-ready pilot packages.",
    ),
    HandoffDocument(
        label="pilot_package_summary_markdown",
        path=PACKAGE_SUMMARY_MARKDOWN_PATH,
        note="Human-readable summary of the latest reviewer-ready pilot packages.",
    ),
    HandoffDocument(
        label="support_v1_readiness_memo",
        path=ARTIFACTS_DIR / "support_v1_readiness_memo.md",
        note="Top-level readiness memo built from existing support_v1 artifacts.",
    ),
    HandoffDocument(
        label="executive_status_brief",
        path=SCRIPT_DIR / "executive_status_brief.md",
        note="Short executive status brief for stakeholder review.",
    ),
    HandoffDocument(
        label="investor_value_brief",
        path=SCRIPT_DIR / "investor_value_brief.md",
        note="Investor-facing value summary for the support_v1 pilot.",
    ),
    HandoffDocument(
        label="pilot_handoff_summary",
        path=SCRIPT_DIR / "pilot_handoff_summary.md",
        note="Compact pilot handoff summary for reviewers and operators.",
    ),
    HandoffDocument(
        label="support_v1_roi_model",
        path=SCRIPT_DIR / "support_v1_roi_model.md",
        note="ROI framing for pilot economics and value discussion.",
    ),
    HandoffDocument(
        label="support_v1_pilot_scorecard",
        path=SCRIPT_DIR / "support_v1_pilot_scorecard.md",
        note="Pilot scorecard for tracking readiness and success criteria.",
    ),
    HandoffDocument(
        label="support_v1_pilot_decision_memo_template",
        path=SCRIPT_DIR / "support_v1_pilot_decision_memo_template.md",
        note="Template for the post-pilot go or no-go memo.",
    ),
    HandoffDocument(
        label="artifact_index",
        path=SCRIPT_DIR / "ARTIFACT_INDEX.md",
        note="Index of the support_v1 scripts, docs, and generated artifacts.",
    ),
    HandoffDocument(
        label="first_live_pilot_runbook",
        path=SCRIPT_DIR / "FIRST_LIVE_PILOT_RUNBOOK.md",
        note="Operational runbook for the first live pilot run.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export one support_v1 pilot handoff bundle by copying the latest existing "
            "reviewer-ready pilot package for a mode together with the highest-value "
            "summary documents into a single shareable folder."
        )
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=tuple(MODE_CONFIGS.keys()),
        help="Select which support_v1 pilot mode to export.",
    )
    parser.add_argument(
        "--handoff-name",
        help=(
            "Optional output folder name. Defaults to a mode-prefixed timestamp under "
            "use_cases/support_v1/artifacts/pilot_handoff_bundles/."
        ),
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {project_relative_path(path)}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_name(f"{path.stem}.{uuid4().hex}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_path.replace(path)


def build_handoff_dir(mode: str, handoff_name: str | None) -> Path:
    if handoff_name is None:
        timestamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
        folder_name = f"{mode}_{timestamp}"
    else:
        folder_name = sanitize_bundle_name(handoff_name)

    handoff_dir = PILOT_HANDOFF_BUNDLES_DIR / folder_name
    if handoff_dir.exists():
        raise FileExistsError(
            "Handoff output folder already exists: "
            f"{project_relative_path(handoff_dir)}"
        )
    return handoff_dir


def resolve_package_sort_key(
    package_manifest: dict[str, Any],
    package_dir: Path,
) -> tuple[datetime, str]:
    generated_at_raw = package_manifest.get("generated_at")
    if isinstance(generated_at_raw, str):
        try:
            return datetime.fromisoformat(generated_at_raw), package_dir.name
        except ValueError:
            pass
    return datetime.fromtimestamp(package_dir.stat().st_mtime).astimezone(), package_dir.name


def resolve_project_path(path_value: str) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate.resolve()
    return (PROJECT_ROOT / candidate).resolve()


def load_valid_package_manifest(
    package_dir: Path,
    manifest_path: Path,
    expected_mode: str,
) -> dict[str, Any] | None:
    if not package_dir.exists() or not package_dir.is_dir():
        return None
    if not manifest_path.exists():
        return None

    try:
        manifest = load_json(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None

    if manifest.get("selected_mode") != expected_mode:
        return None
    return manifest


def find_latest_package_from_summary(
    mode: str,
) -> tuple[Path, Path, dict[str, Any], str] | None:
    if not PACKAGE_SUMMARY_JSON_PATH.exists():
        return None

    try:
        summary = load_json(PACKAGE_SUMMARY_JSON_PATH)
    except (OSError, ValueError, json.JSONDecodeError):
        return None

    packages_by_mode = summary.get("packages_by_mode")
    if not isinstance(packages_by_mode, dict):
        return None

    entry = packages_by_mode.get(mode)
    if not isinstance(entry, dict):
        return None

    package_folder_value = entry.get("latest_package_folder")
    if not isinstance(package_folder_value, str):
        return None

    manifest_path_value = entry.get("manifest_path")
    package_dir = resolve_project_path(package_folder_value)
    if isinstance(manifest_path_value, str):
        manifest_path = resolve_project_path(manifest_path_value)
    else:
        manifest_path = package_dir / PILOT_PACKAGE_MANIFEST_FILENAME

    manifest = load_valid_package_manifest(
        package_dir=package_dir,
        manifest_path=manifest_path,
        expected_mode=mode,
    )
    if manifest is None:
        return None

    return package_dir, manifest_path, manifest, "support_v1_pilot_package_summary.json"


def find_latest_package_by_scan(
    mode: str,
) -> tuple[Path, Path, dict[str, Any], str] | None:
    if not PILOT_PACKAGES_DIR.exists():
        return None

    candidates: list[tuple[datetime, str, Path, Path, dict[str, Any]]] = []
    for package_dir in PILOT_PACKAGES_DIR.iterdir():
        if not package_dir.is_dir():
            continue

        manifest_path = package_dir / PILOT_PACKAGE_MANIFEST_FILENAME
        manifest = load_valid_package_manifest(
            package_dir=package_dir,
            manifest_path=manifest_path,
            expected_mode=mode,
        )
        if manifest is None:
            continue

        sort_time, sort_name = resolve_package_sort_key(manifest, package_dir)
        candidates.append((sort_time, sort_name, package_dir, manifest_path, manifest))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    _, _, package_dir, manifest_path, manifest = candidates[0]
    return package_dir, manifest_path, manifest, "pilot_packages_directory_scan"


def find_latest_pilot_package(mode: str) -> tuple[Path, Path, dict[str, Any], str]:
    summary_result = find_latest_package_from_summary(mode)
    scan_result = find_latest_package_by_scan(mode)

    if summary_result is not None and scan_result is not None:
        summary_sort_key = resolve_package_sort_key(
            summary_result[2],
            summary_result[0],
        )
        scan_sort_key = resolve_package_sort_key(
            scan_result[2],
            scan_result[0],
        )
        return summary_result if summary_sort_key >= scan_sort_key else scan_result

    if summary_result is not None:
        return summary_result

    if scan_result is not None:
        return scan_result

    raise FileNotFoundError(
        "No pilot package found for mode "
        f"'{mode}'. Build one first with "
        f"'py use_cases/support_v1/build_support_v1_pilot_package.py {mode}'."
    )


def copy_latest_package(
    *,
    source_package_dir: Path,
    handoff_dir: Path,
) -> tuple[Path, list[str]]:
    destination_dir = handoff_dir / source_package_dir.name
    shutil.copytree(source_package_dir, destination_dir)
    return destination_dir, [project_relative_path(destination_dir)]


def build_handoff_documents(source_package_dir: Path) -> tuple[HandoffDocument, ...]:
    return COMMON_HANDOFF_DOCUMENTS + (
        HandoffDocument(
            label="pilot_package_index",
            path=source_package_dir / "docs" / PILOT_PACKAGE_INDEX_FILENAME,
            note="Generated index from the selected reviewer-ready pilot package.",
        ),
    )


def copy_handoff_documents(
    *,
    source_package_dir: Path,
    handoff_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
    included_docs: list[dict[str, Any]] = []
    missing_docs: list[dict[str, str]] = []
    output_paths: list[str] = []

    for document in build_handoff_documents(source_package_dir):
        source_path = document.path.resolve()
        if not source_path.exists():
            missing_docs.append(
                {
                    "label": document.label,
                    "expected_source_path": project_relative_path(source_path),
                }
            )
            continue

        destination_path = handoff_dir / source_path.name
        shutil.copy2(source_path, destination_path)
        included_docs.append(
            {
                "label": document.label,
                "source_path": project_relative_path(source_path),
                "handoff_output_path": project_relative_path(destination_path),
                "note": document.note,
            }
        )
        output_paths.append(project_relative_path(destination_path))

    return included_docs, missing_docs, output_paths


def build_manifest(
    *,
    mode: str,
    handoff_dir: Path,
    source_package_dir: Path,
    source_package_manifest_path: Path,
    source_package_manifest: dict[str, Any],
    source_package_resolution: str,
    package_output_paths: list[str],
    included_docs: list[dict[str, Any]],
    missing_docs: list[dict[str, str]],
    doc_output_paths: list[str],
    generated_at: str,
) -> dict[str, Any]:
    manifest_path = project_relative_path(handoff_dir / HANDOFF_MANIFEST_FILENAME)
    output_paths = [
        project_relative_path(handoff_dir),
        *package_output_paths,
        *doc_output_paths,
        manifest_path,
    ]

    return {
        "bundle_type": "support_v1_pilot_handoff_bundle",
        "selected_mode": mode,
        "generated_at": generated_at,
        "handoff_output_folder": project_relative_path(handoff_dir),
        "source_package_used": {
            "package_output_folder": project_relative_path(source_package_dir),
            "package_manifest_path": project_relative_path(source_package_manifest_path),
            "package_generated_at": source_package_manifest.get("generated_at"),
            "package_resolution_source": source_package_resolution,
        },
        "included_docs": included_docs,
        "output_paths": output_paths,
        "purpose_note": (
            "Shareable support_v1 pilot handoff bundle that packages the latest "
            "reviewer-ready pilot package for the selected mode together with the "
            "highest-value summary, readiness, ROI, and runbook documents already "
            "present in the repo."
        ),
        "optional_docs_missing": missing_docs,
    }


def main() -> None:
    args = parse_args()
    (
        source_package_dir,
        source_package_manifest_path,
        source_package_manifest,
        source_package_resolution,
    ) = find_latest_pilot_package(args.mode)
    handoff_dir = build_handoff_dir(args.mode, args.handoff_name)
    handoff_dir.mkdir(parents=True, exist_ok=False)

    _, package_output_paths = copy_latest_package(
        source_package_dir=source_package_dir,
        handoff_dir=handoff_dir,
    )
    included_docs, missing_docs, doc_output_paths = copy_handoff_documents(
        source_package_dir=source_package_dir,
        handoff_dir=handoff_dir,
    )
    generated_at = datetime.now().astimezone().isoformat()
    manifest = build_manifest(
        mode=args.mode,
        handoff_dir=handoff_dir,
        source_package_dir=source_package_dir,
        source_package_manifest_path=source_package_manifest_path,
        source_package_manifest=source_package_manifest,
        source_package_resolution=source_package_resolution,
        package_output_paths=package_output_paths,
        included_docs=included_docs,
        missing_docs=missing_docs,
        doc_output_paths=doc_output_paths,
        generated_at=generated_at,
    )
    manifest_path = handoff_dir / HANDOFF_MANIFEST_FILENAME
    write_json(manifest_path, manifest)

    print(f"selected_mode: {args.mode}")
    print(f"handoff_output_folder: {project_relative_path(handoff_dir)}")
    print(f"manifest_path: {project_relative_path(manifest_path)}")


if __name__ == "__main__":
    main()
