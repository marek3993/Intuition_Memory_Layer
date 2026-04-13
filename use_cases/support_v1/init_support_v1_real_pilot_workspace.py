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
    ARTIFACTS_DIR,
    MODE_CONFIGS,
    PROJECT_ROOT,
    SCRIPT_DIR,
    project_relative_path,
    sanitize_bundle_name,
)
from export_support_v1_pilot_handoff_bundle import (
    HANDOFF_MANIFEST_FILENAME,
    PILOT_HANDOFF_BUNDLES_DIR,
    find_latest_pilot_package,
)


REAL_PILOT_WORKSPACES_DIR = ARTIFACTS_DIR / "real_pilot_workspaces"
WORKSPACE_MANIFEST_FILENAME = "workspace_manifest.json"


@dataclass(frozen=True)
class WorkspaceAsset:
    label: str
    path: Path
    target_subdir: str
    note: str


COMMON_WORKSPACE_ASSETS: tuple[WorkspaceAsset, ...] = (
    WorkspaceAsset(
        label="real_export_intake_template",
        path=SCRIPT_DIR / "real_export_intake_template.md",
        target_subdir="intake",
        note="Fill-in intake template for the first real export onboarding.",
    ),
    WorkspaceAsset(
        label="real_export_field_inventory_template",
        path=SCRIPT_DIR / "real_export_field_inventory_template.csv",
        target_subdir="intake",
        note="Field inventory sheet for documenting the incoming export.",
    ),
    WorkspaceAsset(
        label="real_export_onboarding_checklist",
        path=SCRIPT_DIR / "real_export_onboarding_checklist.md",
        target_subdir="intake",
        note="Checklist for preparing and validating the first real export slice.",
    ),
    WorkspaceAsset(
        label="support_v1_pilot_scorecard_template",
        path=SCRIPT_DIR / "support_v1_pilot_scorecard_template.csv",
        target_subdir="decision",
        note="Template for recording pilot outcomes against success criteria.",
    ),
    WorkspaceAsset(
        label="support_v1_pilot_decision_memo_template",
        path=SCRIPT_DIR / "support_v1_pilot_decision_memo_template.md",
        target_subdir="decision",
        note="Template for the post-pilot go or no-go memo.",
    ),
    WorkspaceAsset(
        label="support_v1_roi_model_template",
        path=SCRIPT_DIR / "support_v1_roi_model_template.csv",
        target_subdir="decision",
        note="Template for turning pilot outcomes into a basic ROI estimate.",
    ),
    WorkspaceAsset(
        label="first_live_pilot_runbook",
        path=SCRIPT_DIR / "FIRST_LIVE_PILOT_RUNBOOK.md",
        target_subdir="references",
        note="Operational runbook for the first live pilot run.",
    ),
    WorkspaceAsset(
        label="support_v1_readiness_memo",
        path=ARTIFACTS_DIR / "support_v1_readiness_memo.md",
        target_subdir="references",
        note="Current readiness summary built from existing support_v1 artifacts.",
    ),
    WorkspaceAsset(
        label="executive_status_brief",
        path=SCRIPT_DIR / "executive_status_brief.md",
        target_subdir="references",
        note="Executive-facing status brief for stakeholder review.",
    ),
    WorkspaceAsset(
        label="investor_value_brief",
        path=SCRIPT_DIR / "investor_value_brief.md",
        target_subdir="references",
        note="High-level value framing for the pilot.",
    ),
    WorkspaceAsset(
        label="support_v1_roi_model",
        path=SCRIPT_DIR / "support_v1_roi_model.md",
        target_subdir="references",
        note="Narrative ROI framing for pilot economics.",
    ),
    WorkspaceAsset(
        label="pilot_handoff_summary",
        path=SCRIPT_DIR / "pilot_handoff_summary.md",
        target_subdir="references",
        note="Compact summary of the current pilot package and operator context.",
    ),
    WorkspaceAsset(
        label="artifact_index",
        path=SCRIPT_DIR / "ARTIFACT_INDEX.md",
        target_subdir="references",
        note="Index of the key support_v1 scripts, docs, and generated artifacts.",
    ),
    WorkspaceAsset(
        label="support_v1_runbook",
        path=SCRIPT_DIR / "README_RUNBOOK.md",
        target_subdir="references",
        note="Command runbook for the support_v1 workflow.",
    ),
    WorkspaceAsset(
        label="helpdesk_export_contract",
        path=SCRIPT_DIR / "helpdesk_export_contract.md",
        target_subdir="references",
        note="Minimum external export contract for a real pilot intake.",
    ),
    WorkspaceAsset(
        label="support_schema",
        path=SCRIPT_DIR / "schema.md",
        target_subdir="references",
        note="Schema reference for the normalized support case shape.",
    ),
)


MODE_SPECIFIC_WORKSPACE_ASSETS: dict[str, tuple[WorkspaceAsset, ...]] = {
    "mapped_ingest": (
        WorkspaceAsset(
            label="helpdesk_export_mapping_template",
            path=SCRIPT_DIR / "helpdesk_export_mapping_template.json",
            target_subdir="intake",
            note="Starter mapping template for a real CSV export with non-contract field names.",
        ),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Initialize a clean support_v1 real pilot workspace by copying the core intake, "
            "decision, reference, and latest mode-specific pilot artifacts into one folder."
        )
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=tuple(MODE_CONFIGS.keys()),
        help="Select which support_v1 pilot mode this workspace is for.",
    )
    parser.add_argument(
        "--workspace-name",
        help=(
            "Optional output folder name. Defaults to a mode-prefixed timestamp under "
            "use_cases/support_v1/artifacts/real_pilot_workspaces/."
        ),
    )
    return parser.parse_args()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_name(f"{path.stem}.{uuid4().hex}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_path.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {project_relative_path(path)}")
    return payload


def build_workspace_dir(mode: str, workspace_name: str | None) -> Path:
    if workspace_name is None:
        timestamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
        folder_name = f"{mode}_{timestamp}"
    else:
        folder_name = sanitize_bundle_name(workspace_name)

    workspace_dir = REAL_PILOT_WORKSPACES_DIR / folder_name
    if workspace_dir.exists():
        raise FileExistsError(
            "Real pilot workspace output folder already exists: "
            f"{project_relative_path(workspace_dir)}"
        )
    return workspace_dir


def ensure_workspace_layout(workspace_dir: Path) -> dict[str, Path]:
    workspace_dir.mkdir(parents=True, exist_ok=False)
    subdirs = {
        "intake": workspace_dir / "intake",
        "inputs": workspace_dir / "inputs",
        "evaluation": workspace_dir / "evaluation",
        "decision": workspace_dir / "decision",
        "references": workspace_dir / "references",
    }
    for directory in subdirs.values():
        directory.mkdir(parents=True, exist_ok=False)
    return subdirs


def copy_workspace_asset(
    asset: WorkspaceAsset,
    subdirs: dict[str, Path],
) -> dict[str, str] | None:
    source_path = asset.path.resolve()
    if not source_path.exists():
        return None

    destination_path = subdirs[asset.target_subdir] / source_path.name
    shutil.copy2(source_path, destination_path)
    return {
        "label": asset.label,
        "source_path": project_relative_path(source_path),
        "workspace_output_path": project_relative_path(destination_path),
        "note": asset.note,
    }


def copy_static_workspace_assets(
    *,
    mode: str,
    subdirs: dict[str, Path],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    copied: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    assets = COMMON_WORKSPACE_ASSETS + MODE_SPECIFIC_WORKSPACE_ASSETS.get(mode, ())

    for asset in assets:
        copied_entry = copy_workspace_asset(asset, subdirs)
        if copied_entry is None:
            missing.append(
                {
                    "label": asset.label,
                    "expected_source_path": project_relative_path(asset.path.resolve()),
                }
            )
            continue
        copied.append(copied_entry)

    return copied, missing


def copy_mode_evaluation_artifacts(
    *,
    mode: str,
    evaluation_dir: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    copied: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    mode_artifacts_dir = evaluation_dir / "current_mode_artifacts"
    mode_artifacts_dir.mkdir(parents=True, exist_ok=False)

    for source in MODE_CONFIGS[mode]["sources"]:
        source_path = source.path.resolve()
        if not source_path.exists():
            missing.append(
                {
                    "label": source.label,
                    "expected_source_path": project_relative_path(source_path),
                }
            )
            continue

        destination_path = mode_artifacts_dir / source_path.name
        shutil.copy2(source_path, destination_path)
        copied.append(
            {
                "label": source.label,
                "source_path": project_relative_path(source_path),
                "workspace_output_path": project_relative_path(destination_path),
                "note": "Latest existing mode-specific evaluation or comparison artifact.",
            }
        )

    return copied, missing


def copy_latest_pilot_package_artifact(
    *,
    mode: str,
    evaluation_dir: Path,
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    try:
        source_package_dir, source_manifest_path, _, source_resolution = (
            find_latest_pilot_package(mode)
        )
    except FileNotFoundError:
        return None, {
            "label": "latest_pilot_package",
            "expected_source_path": project_relative_path(
                ARTIFACTS_DIR / "pilot_packages"
            ),
        }

    destination_dir = evaluation_dir / "latest_pilot_package"
    shutil.copytree(source_package_dir, destination_dir)
    return (
        {
            "label": "latest_pilot_package",
            "source_path": project_relative_path(source_package_dir),
            "workspace_output_path": project_relative_path(destination_dir),
            "source_manifest_path": project_relative_path(source_manifest_path),
            "note": f"Latest existing pilot package for mode '{mode}' ({source_resolution}).",
        },
        None,
    )


def resolve_manifest_sort_key(
    manifest: dict[str, Any],
    artifact_dir: Path,
) -> tuple[datetime, str]:
    generated_at_raw = manifest.get("generated_at")
    if isinstance(generated_at_raw, str):
        try:
            return datetime.fromisoformat(generated_at_raw), artifact_dir.name
        except ValueError:
            pass
    return datetime.fromtimestamp(artifact_dir.stat().st_mtime).astimezone(), artifact_dir.name


def find_latest_handoff_bundle(
    mode: str,
) -> tuple[Path, Path, dict[str, Any]] | None:
    if not PILOT_HANDOFF_BUNDLES_DIR.exists():
        return None

    candidates: list[tuple[datetime, str, Path, Path, dict[str, Any]]] = []
    for handoff_dir in PILOT_HANDOFF_BUNDLES_DIR.iterdir():
        if not handoff_dir.is_dir():
            continue

        manifest_path = handoff_dir / HANDOFF_MANIFEST_FILENAME
        if not manifest_path.exists():
            continue

        try:
            manifest = load_json(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue

        if manifest.get("selected_mode") != mode:
            continue

        sort_time, sort_name = resolve_manifest_sort_key(manifest, handoff_dir)
        candidates.append((sort_time, sort_name, handoff_dir, manifest_path, manifest))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    _, _, handoff_dir, manifest_path, manifest = candidates[0]
    return handoff_dir, manifest_path, manifest


def copy_latest_handoff_bundle_artifact(
    *,
    mode: str,
    evaluation_dir: Path,
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    latest_handoff = find_latest_handoff_bundle(mode)
    if latest_handoff is None:
        return None, {
            "label": "latest_pilot_handoff_bundle",
            "expected_source_path": project_relative_path(PILOT_HANDOFF_BUNDLES_DIR),
        }

    source_handoff_dir, source_manifest_path, _ = latest_handoff
    destination_dir = evaluation_dir / "latest_pilot_handoff_bundle"
    shutil.copytree(source_handoff_dir, destination_dir)
    return (
        {
            "label": "latest_pilot_handoff_bundle",
            "source_path": project_relative_path(source_handoff_dir),
            "workspace_output_path": project_relative_path(destination_dir),
            "source_manifest_path": project_relative_path(source_manifest_path),
            "note": f"Latest existing pilot handoff bundle for mode '{mode}'.",
        },
        None,
    )


def build_manifest(
    *,
    mode: str,
    workspace_dir: Path,
    subdirs: dict[str, Path],
    copied_sources: list[dict[str, str]],
    missing_sources: list[dict[str, str]],
    generated_at: str,
) -> dict[str, Any]:
    manifest_path = workspace_dir / WORKSPACE_MANIFEST_FILENAME
    return {
        "workspace_type": "support_v1_real_pilot_workspace",
        "selected_mode": mode,
        "workspace_path": project_relative_path(workspace_dir),
        "workspace_path_absolute": str(workspace_dir.resolve()),
        "generated_at": generated_at,
        "description": (
            "Clean operator workspace for the first real support_v1 pilot. Use intake "
            "for onboarding templates, inputs for the real export drop, evaluation for "
            "the latest evidence bundle, decision for scorecard and memo drafting, and "
            "references for readiness, runbook, and ROI context."
        ),
        "subfolders": {
            key: project_relative_path(path) for key, path in subdirs.items()
        },
        "source_artifacts_copied_in": copied_sources,
        "optional_artifacts_missing": missing_sources,
        "manifest_path": project_relative_path(manifest_path),
        "project_root": str(PROJECT_ROOT.resolve()),
    }


def main() -> None:
    args = parse_args()
    workspace_dir = build_workspace_dir(args.mode, args.workspace_name)
    subdirs = ensure_workspace_layout(workspace_dir)

    copied_sources: list[dict[str, str]] = []
    missing_sources: list[dict[str, str]] = []

    copied_static_assets, missing_static_assets = copy_static_workspace_assets(
        mode=args.mode,
        subdirs=subdirs,
    )
    copied_sources.extend(copied_static_assets)
    missing_sources.extend(missing_static_assets)

    copied_mode_artifacts, missing_mode_artifacts = copy_mode_evaluation_artifacts(
        mode=args.mode,
        evaluation_dir=subdirs["evaluation"],
    )
    copied_sources.extend(copied_mode_artifacts)
    missing_sources.extend(missing_mode_artifacts)

    copied_package, missing_package = copy_latest_pilot_package_artifact(
        mode=args.mode,
        evaluation_dir=subdirs["evaluation"],
    )
    if copied_package is not None:
        copied_sources.append(copied_package)
    if missing_package is not None:
        missing_sources.append(missing_package)

    copied_handoff, missing_handoff = copy_latest_handoff_bundle_artifact(
        mode=args.mode,
        evaluation_dir=subdirs["evaluation"],
    )
    if copied_handoff is not None:
        copied_sources.append(copied_handoff)
    if missing_handoff is not None:
        missing_sources.append(missing_handoff)

    generated_at = datetime.now().astimezone().isoformat()
    manifest = build_manifest(
        mode=args.mode,
        workspace_dir=workspace_dir,
        subdirs=subdirs,
        copied_sources=copied_sources,
        missing_sources=missing_sources,
        generated_at=generated_at,
    )
    manifest_path = workspace_dir / WORKSPACE_MANIFEST_FILENAME
    write_json(manifest_path, manifest)

    print(f"selected_mode: {args.mode}")
    print(f"workspace_output_folder: {project_relative_path(workspace_dir)}")
    print(f"manifest_path: {project_relative_path(manifest_path)}")


if __name__ == "__main__":
    main()
