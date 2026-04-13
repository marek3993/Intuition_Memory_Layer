from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
BUNDLES_DIR = ARTIFACTS_DIR / "pilot_execution_bundles"
MANIFEST_FILENAME = "bundle_manifest.json"


@dataclass(frozen=True)
class BundleSource:
    label: str
    path: Path
    required: bool = False


@dataclass(frozen=True)
class DocumentReference:
    label: str
    path: Path
    note: str


COMMON_DOCUMENT_REFERENCES: tuple[DocumentReference, ...] = (
    DocumentReference(
        label="readiness_memo",
        path=ARTIFACTS_DIR / "support_v1_readiness_memo.md",
        note="Top-level readiness summary built from existing support_v1 artifacts.",
    ),
    DocumentReference(
        label="pilot_runbook",
        path=SCRIPT_DIR / "FIRST_LIVE_PILOT_RUNBOOK.md",
        note="Operational runbook for the first live pilot handoff and execution.",
    ),
    DocumentReference(
        label="pilot_handoff_summary",
        path=SCRIPT_DIR / "pilot_handoff_summary.md",
        note="Compact pilot handoff summary for human reviewers and operators.",
    ),
    DocumentReference(
        label="pilot_decision_memo",
        path=SCRIPT_DIR / "support_v1_pilot_decision_memo.md",
        note="Decision memo template for turning pilot evidence into a go/no-go call.",
    ),
    DocumentReference(
        label="pilot_scorecard",
        path=SCRIPT_DIR / "support_v1_pilot_scorecard.md",
        note="Scorecard for tracking pilot review conclusions and readiness signals.",
    ),
)

MODE_CONFIGS: dict[str, dict[str, Any]] = {
    "labeled_support": {
        "note": (
            "Human review bundle for the default labeled support_v1 decision-point "
            "evaluation, including focused error and route-change review files when available."
        ),
        "sources": (
            BundleSource(
                label="main_json_evaluation_artifact",
                path=ARTIFACTS_DIR / "latest_support_label_evaluation.json",
                required=True,
            ),
            BundleSource(
                label="review_csv",
                path=ARTIFACTS_DIR / "latest_support_label_review.csv",
            ),
            BundleSource(
                label="focused_error_csv",
                path=ARTIFACTS_DIR / "latest_support_label_errors.csv",
            ),
            BundleSource(
                label="route_change_csv",
                path=ARTIFACTS_DIR / "latest_support_label_route_changes.csv",
            ),
            BundleSource(
                label="comparison_json",
                path=ARTIFACTS_DIR / "support_label_pack_comparison.json",
            ),
            BundleSource(
                label="comparison_markdown",
                path=ARTIFACTS_DIR / "support_label_pack_comparison.md",
            ),
            BundleSource(
                label="decision_memo_markdown",
                path=ARTIFACTS_DIR / "support_label_pack_decision_memo.md",
            ),
        ),
    },
    "raw_ingest": {
        "note": (
            "Human review bundle for the raw-ingest pilot flow, combining the latest raw-ingest "
            "evaluation with comparison and contract-validation evidence when present."
        ),
        "sources": (
            BundleSource(
                label="main_json_evaluation_artifact",
                path=ARTIFACTS_DIR / "latest_support_raw_ingest_label_evaluation.json",
                required=True,
            ),
            BundleSource(
                label="review_csv",
                path=ARTIFACTS_DIR / "latest_support_raw_ingest_label_review.csv",
            ),
            BundleSource(
                label="comparison_json",
                path=ARTIFACTS_DIR / "support_raw_ingest_pack_comparison.json",
            ),
            BundleSource(
                label="comparison_markdown",
                path=ARTIFACTS_DIR / "support_raw_ingest_pack_comparison.md",
            ),
            BundleSource(
                label="ingest_comparison_json",
                path=ARTIFACTS_DIR / "support_ingest_modality_comparison.json",
            ),
            BundleSource(
                label="ingest_comparison_markdown",
                path=ARTIFACTS_DIR / "support_ingest_modality_comparison.md",
            ),
            BundleSource(
                label="contract_validation_json",
                path=ARTIFACTS_DIR / "helpdesk_export_contract_validation.json",
            ),
        ),
    },
    "csv_ingest": {
        "note": (
            "Human review bundle for the CSV-ingest pilot flow, centered on the latest CSV "
            "evaluation and the supporting comparison and contract artifacts."
        ),
        "sources": (
            BundleSource(
                label="main_json_evaluation_artifact",
                path=ARTIFACTS_DIR / "latest_support_csv_ingest_label_evaluation.json",
                required=True,
            ),
            BundleSource(
                label="review_csv",
                path=ARTIFACTS_DIR / "latest_support_csv_ingest_label_review.csv",
            ),
            BundleSource(
                label="comparison_json",
                path=ARTIFACTS_DIR / "support_csv_ingest_pack_comparison.json",
            ),
            BundleSource(
                label="comparison_markdown",
                path=ARTIFACTS_DIR / "support_csv_ingest_pack_comparison.md",
            ),
            BundleSource(
                label="ingest_comparison_json",
                path=ARTIFACTS_DIR / "support_ingest_modality_comparison.json",
            ),
            BundleSource(
                label="ingest_comparison_markdown",
                path=ARTIFACTS_DIR / "support_ingest_modality_comparison.md",
            ),
            BundleSource(
                label="contract_validation_json",
                path=ARTIFACTS_DIR / "helpdesk_export_contract_validation.json",
            ),
        ),
    },
    "mapped_ingest": {
        "note": (
            "Human review bundle for the mapped-ingest pilot flow, using the latest mapped "
            "evaluation plus the relevant comparison and contract-validation artifacts."
        ),
        "sources": (
            BundleSource(
                label="main_json_evaluation_artifact",
                path=ARTIFACTS_DIR / "latest_support_mapped_ingest_label_evaluation.json",
                required=True,
            ),
            BundleSource(
                label="review_csv",
                path=ARTIFACTS_DIR / "latest_support_mapped_ingest_label_review.csv",
            ),
            BundleSource(
                label="comparison_json",
                path=ARTIFACTS_DIR / "support_mapped_ingest_pack_comparison.json",
            ),
            BundleSource(
                label="comparison_markdown",
                path=ARTIFACTS_DIR / "support_mapped_ingest_pack_comparison.md",
            ),
            BundleSource(
                label="ingest_comparison_json",
                path=ARTIFACTS_DIR / "support_ingest_modality_comparison.json",
            ),
            BundleSource(
                label="ingest_comparison_markdown",
                path=ARTIFACTS_DIR / "support_ingest_modality_comparison.md",
            ),
            BundleSource(
                label="contract_validation_json",
                path=ARTIFACTS_DIR / "helpdesk_export_contract_validation.json",
            ),
        ),
    },
    "zendesk_like": {
        "note": (
            "Human review bundle for the Zendesk-like pilot flow, collecting the latest "
            "Zendesk-like evaluation and the supporting ingest comparison evidence."
        ),
        "sources": (
            BundleSource(
                label="main_json_evaluation_artifact",
                path=ARTIFACTS_DIR / "latest_support_zendesk_like_label_evaluation.json",
                required=True,
            ),
            BundleSource(
                label="review_csv",
                path=ARTIFACTS_DIR / "latest_support_zendesk_like_label_review.csv",
            ),
            BundleSource(
                label="comparison_json",
                path=ARTIFACTS_DIR / "support_zendesk_like_pack_comparison.json",
            ),
            BundleSource(
                label="comparison_markdown",
                path=ARTIFACTS_DIR / "support_zendesk_like_pack_comparison.md",
            ),
            BundleSource(
                label="ingest_comparison_json",
                path=ARTIFACTS_DIR / "support_ingest_modality_comparison.json",
            ),
            BundleSource(
                label="ingest_comparison_markdown",
                path=ARTIFACTS_DIR / "support_ingest_modality_comparison.md",
            ),
            BundleSource(
                label="contract_validation_json",
                path=ARTIFACTS_DIR / "helpdesk_export_contract_validation.json",
            ),
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build one compact support_v1 pilot execution bundle from existing artifacts "
            "so a human reviewer can inspect the latest run without hunting across files."
        )
    )
    parser.add_argument(
        "mode",
        choices=tuple(MODE_CONFIGS.keys()),
        help="Select which support_v1 pilot flow to bundle.",
    )
    parser.add_argument(
        "--bundle-name",
        help=(
            "Optional output folder name. Defaults to a mode-prefixed timestamp under "
            "use_cases/support_v1/artifacts/pilot_execution_bundles/."
        ),
    )
    return parser.parse_args()


def project_relative_path(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")


def sanitize_bundle_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    sanitized = sanitized.strip("._-")
    if not sanitized:
        raise ValueError("Bundle name must contain at least one alphanumeric character.")
    return sanitized


def build_bundle_dir(mode: str, bundle_name: str | None) -> Path:
    if bundle_name is None:
        timestamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
        folder_name = f"{mode}_{timestamp}"
    else:
        folder_name = sanitize_bundle_name(bundle_name)

    bundle_dir = BUNDLES_DIR / folder_name
    if bundle_dir.exists():
        raise FileExistsError(
            "Bundle output folder already exists: "
            f"{project_relative_path(bundle_dir)}"
        )
    return bundle_dir


def copy_source_artifacts(
    *,
    sources: tuple[BundleSource, ...],
    bundle_dir: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    copied: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []

    for source in sources:
        source_path = source.path.resolve()
        if not source_path.exists():
            if source.required:
                raise FileNotFoundError(
                    "Required source artifact not found: "
                    f"{project_relative_path(source_path)}"
                )
            missing.append(
                {
                    "label": source.label,
                    "expected_source_path": project_relative_path(source_path),
                }
            )
            continue

        destination_path = bundle_dir / source_path.name
        shutil.copy2(source_path, destination_path)
        copied.append(
            {
                "label": source.label,
                "source_path": project_relative_path(source_path),
                "bundle_output_path": project_relative_path(destination_path),
            }
        )

    return copied, missing


def build_document_references() -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for reference in COMMON_DOCUMENT_REFERENCES:
        exists = reference.path.exists()
        references.append(
            {
                "label": reference.label,
                "path": project_relative_path(reference.path),
                "exists": exists,
                "note": reference.note,
            }
        )
    return references


def build_manifest(
    *,
    mode: str,
    bundle_dir: Path,
    copied_artifacts: list[dict[str, str]],
    missing_artifacts: list[dict[str, str]],
    generated_at: str,
) -> dict[str, Any]:
    config = MODE_CONFIGS[mode]
    output_paths = [artifact["bundle_output_path"] for artifact in copied_artifacts]
    manifest_path = project_relative_path(bundle_dir / MANIFEST_FILENAME)

    return {
        "bundle_type": mode,
        "generated_at": generated_at,
        "bundle_output_folder": project_relative_path(bundle_dir),
        "source_artifacts_used": copied_artifacts,
        "bundle_output_paths": output_paths + [manifest_path],
        "notes": config["note"],
        "optional_source_artifacts_missing": missing_artifacts,
        "document_references": build_document_references(),
    }


def write_manifest(bundle_dir: Path, manifest: dict[str, Any]) -> Path:
    manifest_path = bundle_dir / MANIFEST_FILENAME
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
    config = MODE_CONFIGS[args.mode]
    bundle_dir = build_bundle_dir(args.mode, args.bundle_name)
    bundle_dir.mkdir(parents=True, exist_ok=False)

    copied_artifacts, missing_artifacts = copy_source_artifacts(
        sources=config["sources"],
        bundle_dir=bundle_dir,
    )
    generated_at = datetime.now().astimezone().isoformat()
    manifest = build_manifest(
        mode=args.mode,
        bundle_dir=bundle_dir,
        copied_artifacts=copied_artifacts,
        missing_artifacts=missing_artifacts,
        generated_at=generated_at,
    )
    manifest_path = write_manifest(bundle_dir, manifest)

    print(f"selected_mode: {args.mode}")
    print(f"bundle_output_folder: {project_relative_path(bundle_dir)}")
    print(f"manifest_path: {project_relative_path(manifest_path)}")


if __name__ == "__main__":
    main()
