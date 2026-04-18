from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4
from pilot_ops.io import write_manifest as write_json_manifest, write_report

from build_support_v1_pilot_execution_bundle import MODE_CONFIGS, SCRIPT_DIR, project_relative_path


PILOT_PACKAGES_DIR = SCRIPT_DIR / "artifacts" / "pilot_packages"
PILOT_HANDOFF_BUNDLES_DIR = SCRIPT_DIR / "artifacts" / "pilot_handoff_bundles"
PILOT_PACKAGE_MANIFEST_FILENAME = "pilot_package_manifest.json"
HANDOFF_MANIFEST_FILENAME = "handoff_manifest.json"
VALIDATION_RESULT_FILENAME = "validation_result.json"
SUMMARY_JSON_PATH = SCRIPT_DIR / "artifacts" / "support_v1_pilot_bundle_validation_summary.json"
SUMMARY_MARKDOWN_PATH = SCRIPT_DIR / "artifacts" / "support_v1_pilot_bundle_validation_summary.md"


def load_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {project_relative_path(path)}")
    return payload


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def fallback_sort_time(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone()


def resolve_mode(bundle_name: str, manifest: dict[str, Any] | None) -> str | None:
    if isinstance(manifest, dict):
        mode_value = manifest.get("selected_mode")
        if isinstance(mode_value, str) and mode_value in MODE_CONFIGS:
            return mode_value

    for mode in MODE_CONFIGS:
        if bundle_name == mode or bundle_name.startswith(f"{mode}_"):
            return mode
    return None


def resolve_generated_at(bundle_dir: Path, manifest: dict[str, Any] | None) -> tuple[str | None, datetime]:
    manifest_generated_at = None
    if isinstance(manifest, dict):
        generated_at_value = manifest.get("generated_at")
        if isinstance(generated_at_value, str) and generated_at_value.strip():
            manifest_generated_at = generated_at_value.strip()

    parsed_generated_at = parse_datetime(manifest_generated_at)
    if parsed_generated_at is not None:
        return manifest_generated_at, parsed_generated_at
    return manifest_generated_at, fallback_sort_time(bundle_dir)


def build_validation_snapshot(
    *,
    validation_path: Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    notes: list[str] = []
    if not validation_path.exists():
        notes.append("validation_result.json missing")
        return None, notes

    try:
        payload = load_json_object(validation_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        notes.append(f"validation_result.json unreadable: {exc}")
        return None, notes

    passed = payload.get("passed")
    if not isinstance(passed, bool):
        notes.append("validation_result.json is missing boolean field 'passed'")
        return None, notes

    warning_count = payload.get("warning_count")
    error_count = payload.get("error_count")
    validated_at = payload.get("validated_at")

    snapshot = {
        "path": project_relative_path(validation_path),
        "validated_at": validated_at if isinstance(validated_at, str) else None,
        "validated_at_sort": parse_datetime(validated_at) or fallback_sort_time(validation_path),
        "passed": passed,
        "warning_count": warning_count if isinstance(warning_count, int) else None,
        "error_count": error_count if isinstance(error_count, int) else None,
        "bundle_type_detected": payload.get("bundle_type_detected"),
    }
    return snapshot, notes


def discover_bundles(
    *,
    root_dir: Path,
    bundle_category: str,
    manifest_filename: str,
) -> list[dict[str, Any]]:
    if not root_dir.exists():
        return []

    discovered: list[dict[str, Any]] = []
    for bundle_dir in sorted(root_dir.iterdir()):
        if not bundle_dir.is_dir():
            continue

        manifest_path = bundle_dir / manifest_filename
        manifest: dict[str, Any] | None = None
        notes: list[str] = []

        if manifest_path.exists():
            try:
                manifest = load_json_object(manifest_path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                notes.append(f"{manifest_filename} unreadable: {exc}")
        else:
            notes.append(f"{manifest_filename} missing")

        mode = resolve_mode(bundle_dir.name, manifest)
        generated_at_value, generated_at_sort = resolve_generated_at(bundle_dir, manifest)
        validation_path = bundle_dir / VALIDATION_RESULT_FILENAME
        validation_snapshot, validation_notes = build_validation_snapshot(
            validation_path=validation_path,
        )
        notes.extend(validation_notes)

        if validation_snapshot is None:
            validation_status = "WARN"
            validation_present = validation_path.exists()
            validated_at = None
            validated_at_sort = None
            passed = None
            warning_count = None
            error_count = None
        else:
            validation_status = "PASS" if validation_snapshot["passed"] else "FAIL"
            validation_present = True
            validated_at = validation_snapshot["validated_at"]
            validated_at_sort = validation_snapshot["validated_at_sort"]
            passed = validation_snapshot["passed"]
            warning_count = validation_snapshot["warning_count"]
            error_count = validation_snapshot["error_count"]

        discovered.append(
            {
                "bundle_category": bundle_category,
                "bundle_name": bundle_dir.name,
                "bundle_path": project_relative_path(bundle_dir),
                "bundle_dir": bundle_dir,
                "mode": mode,
                "manifest_path": project_relative_path(manifest_path) if manifest_path.exists() else None,
                "generated_at": generated_at_value,
                "generated_at_sort": generated_at_sort,
                "validation_result_path": project_relative_path(validation_path),
                "validation_present": validation_present,
                "validation_status": validation_status,
                "validated_at": validated_at,
                "validated_at_sort": validated_at_sort,
                "passed": passed,
                "warning_count": warning_count,
                "error_count": error_count,
                "notes": notes,
            }
        )

    return discovered


def build_latest_validated_by_mode(
    bundle_entries: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    latest_by_mode: dict[str, dict[str, Any]] = {}

    for mode in MODE_CONFIGS:
        candidates = [
            entry
            for entry in bundle_entries
            if entry["mode"] == mode and entry["validation_present"] and entry["validated_at_sort"] is not None
        ]
        if not candidates:
            continue

        latest_entry = max(
            candidates,
            key=lambda entry: (entry["validated_at_sort"], entry["bundle_name"]),
        )
        latest_by_mode[mode] = {
            "bundle_path": latest_entry["bundle_path"],
            "manifest_path": latest_entry["manifest_path"],
            "validation_result_path": latest_entry["validation_result_path"],
            "generated_at": latest_entry["generated_at"],
            "validated_at": latest_entry["validated_at"],
            "validation_status": latest_entry["validation_status"],
            "warning_count": latest_entry["warning_count"],
            "error_count": latest_entry["error_count"],
        }

    return latest_by_mode


def build_bundle_overview(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered_entries = sorted(
        entries,
        key=lambda entry: (
            entry["bundle_category"],
            entry["mode"] or "",
            entry["generated_at_sort"],
            entry["bundle_name"],
        ),
        reverse=True,
    )

    overview: list[dict[str, Any]] = []
    for entry in ordered_entries:
        overview.append(
            {
                "status": entry["validation_status"],
                "bundle_category": entry["bundle_category"],
                "mode": entry["mode"],
                "bundle_path": entry["bundle_path"],
                "manifest_path": entry["manifest_path"],
                "generated_at": entry["generated_at"],
                "validation_result_path": entry["validation_result_path"],
                "validated_at": entry["validated_at"],
                "warning_count": entry["warning_count"],
                "error_count": entry["error_count"],
                "notes": entry["notes"],
            }
        )
    return overview


def build_summary(
    package_entries: list[dict[str, Any]],
    handoff_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    all_entries = [*package_entries, *handoff_entries]
    missing_validation_paths = [
        entry["bundle_path"] for entry in all_entries if "validation_result.json missing" in entry["notes"]
    ]

    validated_pass_count = sum(1 for entry in all_entries if entry["validation_status"] == "PASS")
    validated_fail_count = sum(1 for entry in all_entries if entry["validation_status"] == "FAIL")
    missing_validation_count = len(missing_validation_paths)

    return {
        "summary_type": "support_v1_pilot_bundle_validation_summary",
        "generated_at": datetime.now().astimezone().isoformat(),
        "pilot_packages_root": project_relative_path(PILOT_PACKAGES_DIR),
        "pilot_handoff_bundles_root": project_relative_path(PILOT_HANDOFF_BUNDLES_DIR),
        "supported_modes": list(MODE_CONFIGS.keys()),
        "total_pilot_packages_found": len(package_entries),
        "total_handoff_bundles_found": len(handoff_entries),
        "total_bundles_scanned": len(all_entries),
        "validated_pass_count": validated_pass_count,
        "validated_fail_count": validated_fail_count,
        "missing_validation_count": missing_validation_count,
        "latest_validated_package_per_mode": build_latest_validated_by_mode(package_entries),
        "latest_validated_handoff_bundle_per_mode": build_latest_validated_by_mode(handoff_entries),
        "bundles_missing_validation_result": missing_validation_paths,
        "bundle_overview": build_bundle_overview(all_entries),
        "notes": (
            "Compact support_v1 bundle-health snapshot built from existing pilot package and "
            "pilot handoff bundle folders. It reads validation_result.json when present and "
            "does not rerun validation automatically."
        ),
    }


def render_latest_validated_table(
    title: str,
    latest_by_mode: dict[str, dict[str, Any]],
) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Mode | Bundle path | Status | Validated at | Warning count | Error count |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]

    for mode in MODE_CONFIGS:
        entry = latest_by_mode.get(mode)
        if entry is None:
            lines.append(f"| `{mode}` | missing | missing | missing | 0 | 0 |")
            continue
        lines.append(
            f"| `{mode}` | `{entry['bundle_path']}` | `{entry['validation_status']}` | "
            f"`{entry['validated_at']}` | {entry['warning_count'] or 0} | {entry['error_count'] or 0} |"
        )

    lines.append("")
    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Support V1 Pilot Bundle Validation Summary",
        "",
        (
            "Compact snapshot of pilot package and pilot handoff bundle validation health "
            "built from the existing artifact folders. This summary reads "
            "`validation_result.json` when present and never reruns validation."
        ),
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Pilot packages root: `{summary['pilot_packages_root']}`",
        f"- Pilot handoff bundles root: `{summary['pilot_handoff_bundles_root']}`",
        f"- Total pilot packages found: {summary['total_pilot_packages_found']}",
        f"- Total handoff bundles found: {summary['total_handoff_bundles_found']}",
        f"- Total bundles scanned: {summary['total_bundles_scanned']}",
        f"- Validated pass count: {summary['validated_pass_count']}",
        f"- Validated fail count: {summary['validated_fail_count']}",
        f"- Missing validation count: {summary['missing_validation_count']}",
    ]

    lines.extend(
        render_latest_validated_table(
            "Latest Validated Pilot Package Per Mode",
            summary["latest_validated_package_per_mode"],
        )
    )
    lines.extend(
        render_latest_validated_table(
            "Latest Validated Handoff Bundle Per Mode",
            summary["latest_validated_handoff_bundle_per_mode"],
        )
    )

    lines.extend(
        [
            "## Missing validation_result.json",
            "",
        ]
    )
    missing_validation_paths = summary["bundles_missing_validation_result"]
    if missing_validation_paths:
        for bundle_path in missing_validation_paths:
            lines.append(f"- `{bundle_path}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Bundle Overview",
            "",
            "| Status | Bundle type | Mode | Bundle path | Validated at | Note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    for entry in summary["bundle_overview"]:
        notes = "; ".join(entry["notes"]) if entry["notes"] else "ok"
        mode = f"`{entry['mode']}`" if entry["mode"] else "unknown"
        validated_at = f"`{entry['validated_at']}`" if entry["validated_at"] else "missing"
        lines.append(
            f"| `{entry['status']}` | `{entry['bundle_category']}` | {mode} | "
            f"`{entry['bundle_path']}` | {validated_at} | {notes} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    package_entries = discover_bundles(
        root_dir=PILOT_PACKAGES_DIR,
        bundle_category="pilot_package",
        manifest_filename=PILOT_PACKAGE_MANIFEST_FILENAME,
    )
    handoff_entries = discover_bundles(
        root_dir=PILOT_HANDOFF_BUNDLES_DIR,
        bundle_category="pilot_handoff_bundle",
        manifest_filename=HANDOFF_MANIFEST_FILENAME,
    )
    summary = build_summary(package_entries, handoff_entries)
    markdown = render_markdown(summary)

    write_json_manifest(SUMMARY_JSON_PATH, summary)
    write_report(SUMMARY_MARKDOWN_PATH, markdown)

    print(f"total_bundles_scanned: {summary['total_bundles_scanned']}")
    print(f"validated_pass_count: {summary['validated_pass_count']}")
    print(f"validated_fail_count: {summary['validated_fail_count']}")
    print(f"missing_validation_count: {summary['missing_validation_count']}")
    print(f"summary_json_path: {project_relative_path(SUMMARY_JSON_PATH)}")
    print(f"summary_markdown_path: {project_relative_path(SUMMARY_MARKDOWN_PATH)}")


if __name__ == "__main__":
    main()
