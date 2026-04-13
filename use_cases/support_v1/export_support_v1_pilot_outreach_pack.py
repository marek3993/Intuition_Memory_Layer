from __future__ import annotations

import argparse
import json
import os
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
PILOT_OUTREACH_PACKS_DIR = ARTIFACTS_DIR / "pilot_outreach_packs"
MANIFEST_FILENAME = "outreach_pack_manifest.json"
SUPPORTED_MODES = (
    "raw_ingest",
    "csv_ingest",
    "mapped_ingest",
    "zendesk_like",
    "labeled_support",
)
EXCLUDED_DIR_NAMES = {"__pycache__", "pilot_outreach_packs"}


@dataclass(frozen=True)
class OutreachDocument:
    filename: str
    note: str


REQUIRED_DOCUMENTS: tuple[OutreachDocument, ...] = (
    OutreachDocument(
        filename="pilot_readiness_decision_brief.md",
        note="Decision-facing recommendation for whether to start first pilot outreach now.",
    ),
    OutreachDocument(
        filename="pilot_handoff_summary.md",
        note="Short practical handoff summary for the first external pilot conversation.",
    ),
    OutreachDocument(
        filename="pilot_handoff_email_template.md",
        note="Starter email template for requesting the first external export slice.",
    ),
    OutreachDocument(
        filename="support_v1_readiness_memo.md",
        note="Current top-level readiness summary built from existing support_v1 artifacts.",
    ),
    OutreachDocument(
        filename="real_export_onboarding_checklist.md",
        note="Checklist for onboarding the first real export slice.",
    ),
    OutreachDocument(
        filename="real_export_intake_template.md",
        note="Fill-in intake template for the first real export conversation.",
    ),
    OutreachDocument(
        filename="real_export_field_inventory_template.csv",
        note="Field inventory template for documenting the partner export.",
    ),
    OutreachDocument(
        filename="helpdesk_export_contract.md",
        note="Minimum export contract required before normalization and review.",
    ),
    OutreachDocument(
        filename="executive_status_brief.md",
        note="Executive-facing status snapshot for the pilot conversation.",
    ),
    OutreachDocument(
        filename="investor_value_brief.md",
        note="High-level value framing for the first pilot conversation.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export one minimal support_v1 pilot outreach pack from the latest existing "
            "decision, onboarding, and stakeholder materials already present in the repo."
        )
    )
    parser.add_argument(
        "--pack-name",
        help=(
            "Optional output folder name. Defaults to a timestamped folder under "
            "use_cases/support_v1/artifacts/pilot_outreach_packs/."
        ),
    )
    return parser.parse_args()


def project_relative_path(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")


def sanitize_output_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    sanitized = sanitized.strip("._-")
    if not sanitized:
        raise ValueError("Pack name must contain at least one alphanumeric character.")
    return sanitized


def build_output_dir(pack_name: str | None) -> Path:
    if pack_name is None:
        folder_name = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
    else:
        folder_name = sanitize_output_name(pack_name)

    output_dir = PILOT_OUTREACH_PACKS_DIR / folder_name
    if output_dir.exists():
        raise FileExistsError(
            "Outreach output folder already exists: "
            f"{project_relative_path(output_dir)}"
        )
    return output_dir


def iter_candidate_paths(filename: str) -> list[Path]:
    candidates: list[Path] = []
    for root, dirnames, filenames in os.walk(SCRIPT_DIR, onerror=lambda _: None):
        dirnames[:] = [
            dirname for dirname in dirnames if dirname not in EXCLUDED_DIR_NAMES
        ]
        if filename not in filenames:
            continue
        candidates.append((Path(root) / filename).resolve())
    return candidates


def select_latest_document(filename: str) -> Path:
    candidates = iter_candidate_paths(filename)
    if not candidates:
        raise FileNotFoundError(
            "Required outreach source document not found: "
            f"use_cases/support_v1/**/{filename}"
        )

    candidates.sort(
        key=lambda path: (
            path.stat().st_mtime,
            project_relative_path(path),
        ),
        reverse=True,
    )
    return candidates[0]


def copy_required_documents(output_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    included_docs: list[dict[str, Any]] = []
    selected_sources: dict[str, Path] = {}

    for document in REQUIRED_DOCUMENTS:
        source_path = select_latest_document(document.filename)
        destination_path = output_dir / document.filename
        shutil.copy2(source_path, destination_path)
        selected_sources[document.filename] = source_path
        included_docs.append(
            {
                "filename": document.filename,
                "source_path": project_relative_path(source_path),
                "output_path": project_relative_path(destination_path),
                "source_modified_at": datetime.fromtimestamp(
                    source_path.stat().st_mtime
                ).astimezone().isoformat(),
                "note": document.note,
            }
        )

    return included_docs, selected_sources


def read_text_if_present(path: Path | None) -> str | None:
    if path is None:
        return None
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def normalize_mode_label(mode_label: str) -> str | None:
    normalized = mode_label.strip().lower().replace("-", "_")
    if normalized in SUPPORTED_MODES:
        return normalized
    return None


def extract_recommended_mode(text: str | None) -> tuple[str, str]:
    if not text:
        return (
            "raw_ingest",
            "Defaulted to raw_ingest because no explicit recommendation text was available.",
        )

    explicit_patterns = (
        r"`(?P<mode>raw_ingest|csv_ingest|mapped_ingest|zendesk_like|labeled_support)`\s+is the strongest starting path",
        r"Prefer\s+`(?P<mode>raw_ingest|csv_ingest|mapped_ingest|zendesk_like|labeled_support)`\s+first",
        r"preferably\s+`(?P<mode>raw_ingest|csv_ingest|mapped_ingest|zendesk_like|labeled_support)`",
        r"Start with\s+`(?P<mode>raw_ingest|csv_ingest|mapped_ingest|zendesk_like|labeled_support)`",
    )
    for pattern in explicit_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            mode = normalize_mode_label(match.group("mode"))
            if mode is not None:
                return (
                    mode,
                    "Selected from the latest pilot_readiness_decision_brief.md wording.",
                )

    if "Strongest current evidence: raw-ingest" in text:
        return (
            "raw_ingest",
            "Selected from the latest readiness memo strongest-evidence note.",
        )
    if "Strongest current evidence: csv-ingest" in text:
        return (
            "csv_ingest",
            "Selected from the latest readiness memo strongest-evidence note.",
        )
    if "Strongest current evidence: mapped-ingest" in text:
        return (
            "mapped_ingest",
            "Selected from the latest readiness memo strongest-evidence note.",
        )
    if "Strongest current evidence: Zendesk-like" in text:
        return (
            "zendesk_like",
            "Selected from the latest readiness memo strongest-evidence note.",
        )

    return (
        "raw_ingest",
        "Defaulted to raw_ingest because the latest materials did not explicitly recommend a different starting mode.",
    )


def determine_recommended_mode(selected_sources: dict[str, Path]) -> tuple[str, str]:
    decision_brief_text = read_text_if_present(
        selected_sources.get("pilot_readiness_decision_brief.md")
    )
    if decision_brief_text:
        return extract_recommended_mode(decision_brief_text)

    readiness_memo_text = read_text_if_present(
        selected_sources.get("support_v1_readiness_memo.md")
    )
    return extract_recommended_mode(readiness_memo_text)


def build_manifest(
    *,
    output_dir: Path,
    generated_at: str,
    included_docs: list[dict[str, Any]],
    recommended_mode: str,
    recommended_mode_note: str,
) -> dict[str, Any]:
    manifest_path = output_dir / MANIFEST_FILENAME
    output_paths = [project_relative_path(output_dir)]
    output_paths.extend(document["output_path"] for document in included_docs)
    output_paths.append(project_relative_path(manifest_path))

    return {
        "generated_at": generated_at,
        "included_docs": included_docs,
        "output_paths": output_paths,
        "purpose_note": (
            "Minimum decision and onboarding materials needed to start the first real "
            "external support_v1 pilot conversation without rerunning evaluations."
        ),
        "recommended_starting_mode": recommended_mode,
        "recommended_starting_mode_note": recommended_mode_note,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_name(f"{path.stem}.{uuid4().hex}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_path.replace(path)


def main() -> None:
    args = parse_args()
    output_dir = build_output_dir(args.pack_name)
    output_dir.mkdir(parents=True, exist_ok=False)

    included_docs, selected_sources = copy_required_documents(output_dir)
    recommended_mode, recommended_mode_note = determine_recommended_mode(
        selected_sources
    )
    generated_at = datetime.now().astimezone().isoformat()
    manifest = build_manifest(
        output_dir=output_dir,
        generated_at=generated_at,
        included_docs=included_docs,
        recommended_mode=recommended_mode,
        recommended_mode_note=recommended_mode_note,
    )
    manifest_path = output_dir / MANIFEST_FILENAME
    write_json(manifest_path, manifest)

    print(f"outreach_output_folder: {project_relative_path(output_dir)}")
    print(f"manifest_path: {project_relative_path(manifest_path)}")


if __name__ == "__main__":
    main()
