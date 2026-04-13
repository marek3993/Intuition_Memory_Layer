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
    BUNDLES_DIR,
    MANIFEST_FILENAME as EXECUTION_BUNDLE_MANIFEST_FILENAME,
    MODE_CONFIGS,
    PROJECT_ROOT,
    SCRIPT_DIR,
    project_relative_path,
    sanitize_bundle_name,
)


PILOT_PACKAGES_DIR = SCRIPT_DIR / "artifacts" / "pilot_packages"
PILOT_PACKAGE_MANIFEST_FILENAME = "pilot_package_manifest.json"
PILOT_PACKAGE_INDEX_FILENAME = "PILOT_PACKAGE_INDEX.md"
EXECUTION_BUNDLE_DIRNAME = "execution_bundle"
DOCS_DIRNAME = "docs"


@dataclass(frozen=True)
class PilotDocument:
    label: str
    path: Path
    note: str


PILOT_DOCUMENTS: tuple[PilotDocument, ...] = (
    PilotDocument(
        label="support_v1_readiness_memo",
        path=SCRIPT_DIR / "artifacts" / "support_v1_readiness_memo.md",
        note="Compact readiness memo built from the current support_v1 artifacts.",
    ),
    PilotDocument(
        label="real_export_onboarding_checklist",
        path=SCRIPT_DIR / "real_export_onboarding_checklist.md",
        note="Checklist for onboarding the first real helpdesk export.",
    ),
    PilotDocument(
        label="pilot_handoff_summary",
        path=SCRIPT_DIR / "pilot_handoff_summary.md",
        note="Short handoff summary for pilot reviewers and operators.",
    ),
    PilotDocument(
        label="support_v1_pilot_scorecard",
        path=SCRIPT_DIR / "support_v1_pilot_scorecard.md",
        note="Scorecard for evaluating pilot success and readiness.",
    ),
    PilotDocument(
        label="support_v1_pilot_decision_memo_template",
        path=SCRIPT_DIR / "support_v1_pilot_decision_memo_template.md",
        note="Template for the post-pilot go/no-go decision memo.",
    ),
    PilotDocument(
        label="first_live_pilot_runbook",
        path=SCRIPT_DIR / "FIRST_LIVE_PILOT_RUNBOOK.md",
        note="Operational runbook for the first live pilot run.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build one reviewer-ready support_v1 pilot package by combining the latest "
            "existing execution bundle for a mode with the key readiness, onboarding, "
            "handoff, and runbook documents."
        )
    )
    parser.add_argument(
        "mode",
        choices=tuple(MODE_CONFIGS.keys()),
        help="Select which support_v1 pilot mode to package.",
    )
    parser.add_argument(
        "--package-name",
        help=(
            "Optional output folder name. Defaults to a mode-prefixed timestamp under "
            "use_cases/support_v1/artifacts/pilot_packages/."
        ),
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {project_relative_path(path)}")
    return data


def build_package_dir(mode: str, package_name: str | None) -> Path:
    if package_name is None:
        timestamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
        folder_name = f"{mode}_{timestamp}"
    else:
        folder_name = sanitize_bundle_name(package_name)

    package_dir = PILOT_PACKAGES_DIR / folder_name
    if package_dir.exists():
        raise FileExistsError(
            "Pilot package output folder already exists: "
            f"{project_relative_path(package_dir)}"
        )
    return package_dir


def resolve_bundle_sort_key(bundle_manifest: dict[str, Any], bundle_dir: Path) -> tuple[datetime, str]:
    generated_at_raw = bundle_manifest.get("generated_at")
    if isinstance(generated_at_raw, str):
        try:
            return datetime.fromisoformat(generated_at_raw), bundle_dir.name
        except ValueError:
            pass
    return datetime.fromtimestamp(bundle_dir.stat().st_mtime).astimezone(), bundle_dir.name


def find_latest_execution_bundle(mode: str) -> tuple[Path, Path, dict[str, Any]]:
    if not BUNDLES_DIR.exists():
        raise FileNotFoundError(
            "Execution bundle directory not found: "
            f"{project_relative_path(BUNDLES_DIR)}"
        )

    candidates: list[tuple[datetime, str, Path, Path, dict[str, Any]]] = []
    for bundle_dir in BUNDLES_DIR.iterdir():
        if not bundle_dir.is_dir():
            continue
        manifest_path = bundle_dir / EXECUTION_BUNDLE_MANIFEST_FILENAME
        if not manifest_path.exists():
            continue
        try:
            manifest = load_json(manifest_path)
        except (json.JSONDecodeError, OSError, ValueError):
            continue
        if manifest.get("bundle_type") != mode:
            continue
        sort_time, sort_name = resolve_bundle_sort_key(manifest, bundle_dir)
        candidates.append((sort_time, sort_name, bundle_dir, manifest_path, manifest))

    if not candidates:
        raise FileNotFoundError(
            "No execution bundle found for mode "
            f"'{mode}'. Build one first with "
            f"'py use_cases/support_v1/build_support_v1_pilot_execution_bundle.py {mode}'."
        )

    candidates.sort(reverse=True)
    _, _, bundle_dir, manifest_path, manifest = candidates[0]
    return bundle_dir, manifest_path, manifest


def copy_execution_bundle(*, source_bundle_dir: Path, package_dir: Path) -> tuple[Path, list[str]]:
    package_bundle_dir = package_dir / EXECUTION_BUNDLE_DIRNAME
    shutil.copytree(source_bundle_dir, package_bundle_dir)

    copied_paths = [project_relative_path(package_bundle_dir)]
    copied_paths.extend(
        project_relative_path(path)
        for path in sorted(package_bundle_dir.rglob("*"))
        if path.is_file()
    )
    return package_bundle_dir, copied_paths


def render_package_index(
    *,
    mode: str,
    source_bundle_dir: Path,
    included_docs: list[dict[str, Any]],
    missing_docs: list[dict[str, str]],
) -> str:
    lines = [
        "# Support V1 Pilot Package Index",
        "",
        (
            "This package combines the selected execution bundle with the key support_v1 "
            "pilot documents needed for reviewer handoff, onboarding, readiness review, "
            "and first-live execution."
        ),
        "",
        f"- Selected mode: `{mode}`",
        f"- Source execution bundle: `{project_relative_path(source_bundle_dir)}`",
        f"- Project root: `{project_relative_path(PROJECT_ROOT)}`",
        "",
        "## Package Contents",
        "",
        f"- `{EXECUTION_BUNDLE_DIRNAME}/` - Copied execution bundle contents for the selected mode.",
        f"- `{DOCS_DIRNAME}/` - Pilot, readiness, onboarding, and runbook documents for reviewers.",
        f"- `{PILOT_PACKAGE_MANIFEST_FILENAME}` - Machine-readable package manifest.",
        "",
        "## Included Docs",
        "",
    ]

    for doc in included_docs:
        lines.append(f"- `{Path(doc['package_output_path']).name}` - {doc['note']}")

    if missing_docs:
        lines.extend(
            [
                "",
                "## Docs Not Included",
                "",
            ]
        )
        for doc in missing_docs:
            lines.append(
                f"- `{Path(doc['expected_source_path']).name}` - missing from the repo, so it was not copied."
            )

    lines.append("")
    return "\n".join(lines)


def copy_pilot_docs(
    *,
    mode: str,
    source_bundle_dir: Path,
    package_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
    docs_dir = package_dir / DOCS_DIRNAME
    docs_dir.mkdir(parents=True, exist_ok=False)

    included_docs: list[dict[str, Any]] = []
    missing_docs: list[dict[str, str]] = []
    output_paths = [project_relative_path(docs_dir)]

    for document in PILOT_DOCUMENTS:
        source_path = document.path.resolve()
        if not source_path.exists():
            missing_docs.append(
                {
                    "label": document.label,
                    "expected_source_path": project_relative_path(source_path),
                }
            )
            continue

        destination_path = docs_dir / source_path.name
        shutil.copy2(source_path, destination_path)
        included_docs.append(
            {
                "label": document.label,
                "source_path": project_relative_path(source_path),
                "package_output_path": project_relative_path(destination_path),
                "note": document.note,
            }
        )
        output_paths.append(project_relative_path(destination_path))

    index_path = docs_dir / PILOT_PACKAGE_INDEX_FILENAME
    index_content = render_package_index(
        mode=mode,
        source_bundle_dir=source_bundle_dir,
        included_docs=included_docs,
        missing_docs=missing_docs,
    )
    with index_path.open("w", encoding="utf-8") as handle:
        handle.write(index_content)

    included_docs.append(
        {
            "label": "pilot_package_index",
            "source_path": None,
            "package_output_path": project_relative_path(index_path),
            "note": "Generated package index for reviewer navigation.",
        }
    )
    output_paths.append(project_relative_path(index_path))

    return included_docs, missing_docs, output_paths


def build_manifest(
    *,
    mode: str,
    package_dir: Path,
    source_bundle_dir: Path,
    source_bundle_manifest_path: Path,
    source_bundle_manifest: dict[str, Any],
    included_docs: list[dict[str, Any]],
    missing_docs: list[dict[str, str]],
    execution_bundle_output_paths: list[str],
    doc_output_paths: list[str],
    generated_at: str,
) -> dict[str, Any]:
    manifest_path = project_relative_path(package_dir / PILOT_PACKAGE_MANIFEST_FILENAME)
    output_paths = [
        project_relative_path(package_dir),
        *execution_bundle_output_paths,
        *doc_output_paths,
        manifest_path,
    ]

    return {
        "package_type": "support_v1_pilot_package",
        "selected_mode": mode,
        "generated_at": generated_at,
        "package_output_folder": project_relative_path(package_dir),
        "source_execution_bundle_used": {
            "bundle_output_folder": project_relative_path(source_bundle_dir),
            "bundle_manifest_path": project_relative_path(source_bundle_manifest_path),
            "bundle_type": source_bundle_manifest.get("bundle_type"),
            "bundle_generated_at": source_bundle_manifest.get("generated_at"),
        },
        "included_docs": included_docs,
        "output_paths": output_paths,
        "notes": (
            "Reviewer-ready pilot package that combines one existing support_v1 execution "
            "bundle with the key readiness, onboarding, handoff, scorecard, and first-live "
            "pilot documents."
        ),
        "optional_docs_missing": missing_docs,
    }


def write_manifest(package_dir: Path, manifest: dict[str, Any]) -> Path:
    manifest_path = package_dir / PILOT_PACKAGE_MANIFEST_FILENAME
    temp_manifest_path = manifest_path.with_name(
        f"{manifest_path.stem}.{uuid4().hex}.tmp"
    )
    with temp_manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    temp_manifest_path.replace(manifest_path)
    return manifest_path


def main() -> None:
    args = parse_args()
    source_bundle_dir, source_bundle_manifest_path, source_bundle_manifest = (
        find_latest_execution_bundle(args.mode)
    )
    package_dir = build_package_dir(args.mode, args.package_name)
    package_dir.mkdir(parents=True, exist_ok=False)

    _, execution_bundle_output_paths = copy_execution_bundle(
        source_bundle_dir=source_bundle_dir,
        package_dir=package_dir,
    )
    included_docs, missing_docs, doc_output_paths = copy_pilot_docs(
        mode=args.mode,
        source_bundle_dir=source_bundle_dir,
        package_dir=package_dir,
    )
    generated_at = datetime.now().astimezone().isoformat()
    manifest = build_manifest(
        mode=args.mode,
        package_dir=package_dir,
        source_bundle_dir=source_bundle_dir,
        source_bundle_manifest_path=source_bundle_manifest_path,
        source_bundle_manifest=source_bundle_manifest,
        included_docs=included_docs,
        missing_docs=missing_docs,
        execution_bundle_output_paths=execution_bundle_output_paths,
        doc_output_paths=doc_output_paths,
        generated_at=generated_at,
    )
    manifest_path = write_manifest(package_dir, manifest)

    print(f"selected_mode: {args.mode}")
    print(f"package_output_folder: {project_relative_path(package_dir)}")
    print(f"manifest_path: {project_relative_path(manifest_path)}")


if __name__ == "__main__":
    main()
