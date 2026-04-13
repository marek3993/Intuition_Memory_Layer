from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from build_support_v1_pilot_execution_bundle import MODE_CONFIGS, SCRIPT_DIR, project_relative_path


REAL_PILOT_WORKSPACES_DIR = SCRIPT_DIR / "artifacts" / "real_pilot_workspaces"
WORKSPACE_MANIFEST_FILENAME = "workspace_manifest.json"
VALIDATION_RESULT_FILENAME = "validation_result.json"
SUMMARY_JSON_PATH = SCRIPT_DIR / "artifacts" / "support_v1_real_pilot_workspace_summary.json"
SUMMARY_MARKDOWN_PATH = SCRIPT_DIR / "artifacts" / "support_v1_real_pilot_workspace_summary.md"


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


def resolve_mode(
    workspace_name: str,
    manifest: dict[str, Any] | None,
    validation_payload: dict[str, Any] | None,
) -> str | None:
    for payload in (manifest, validation_payload):
        if isinstance(payload, dict):
            mode_value = payload.get("selected_mode")
            if isinstance(mode_value, str) and mode_value in MODE_CONFIGS:
                return mode_value

    for mode in MODE_CONFIGS:
        if workspace_name == mode or workspace_name.startswith(f"{mode}_"):
            return mode
    return None


def resolve_generated_at(
    workspace_dir: Path,
    manifest: dict[str, Any] | None,
) -> tuple[str | None, datetime]:
    manifest_generated_at = None
    if isinstance(manifest, dict):
        generated_at_value = manifest.get("generated_at")
        if isinstance(generated_at_value, str) and generated_at_value.strip():
            manifest_generated_at = generated_at_value.strip()

    parsed_generated_at = parse_datetime(manifest_generated_at)
    if parsed_generated_at is not None:
        return manifest_generated_at, parsed_generated_at
    return manifest_generated_at, fallback_sort_time(workspace_dir)


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
        "payload": payload,
        "path": project_relative_path(validation_path),
        "validated_at": validated_at if isinstance(validated_at, str) else None,
        "validated_at_sort": parse_datetime(validated_at) or fallback_sort_time(validation_path),
        "passed": passed,
        "warning_count": warning_count if isinstance(warning_count, int) else None,
        "error_count": error_count if isinstance(error_count, int) else None,
    }
    return snapshot, notes


def discover_workspaces() -> list[dict[str, Any]]:
    if not REAL_PILOT_WORKSPACES_DIR.exists():
        return []

    discovered: list[dict[str, Any]] = []
    for workspace_dir in sorted(REAL_PILOT_WORKSPACES_DIR.iterdir()):
        try:
            if not workspace_dir.is_dir():
                continue
        except OSError:
            continue

        manifest_path = workspace_dir / WORKSPACE_MANIFEST_FILENAME
        manifest: dict[str, Any] | None = None
        notes: list[str] = []

        if manifest_path.exists():
            try:
                manifest = load_json_object(manifest_path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                notes.append(f"{WORKSPACE_MANIFEST_FILENAME} unreadable: {exc}")
        else:
            notes.append(f"{WORKSPACE_MANIFEST_FILENAME} missing")

        generated_at_value, generated_at_sort = resolve_generated_at(workspace_dir, manifest)
        validation_path = workspace_dir / VALIDATION_RESULT_FILENAME
        validation_snapshot, validation_notes = build_validation_snapshot(validation_path=validation_path)
        notes.extend(validation_notes)

        validation_payload = validation_snapshot["payload"] if validation_snapshot is not None else None
        mode = resolve_mode(workspace_dir.name, manifest, validation_payload)

        if validation_snapshot is None:
            validation_status = "WARN"
            validation_present = False
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
                "workspace_name": workspace_dir.name,
                "workspace_path": project_relative_path(workspace_dir),
                "workspace_dir": workspace_dir,
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
    workspace_entries: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    latest_by_mode: dict[str, dict[str, Any]] = {}

    for mode in MODE_CONFIGS:
        candidates = [
            entry
            for entry in workspace_entries
            if entry["mode"] == mode and entry["validation_present"] and entry["validated_at_sort"] is not None
        ]
        if not candidates:
            continue

        latest_entry = max(
            candidates,
            key=lambda entry: (entry["validated_at_sort"], entry["workspace_name"]),
        )
        latest_by_mode[mode] = {
            "workspace_path": latest_entry["workspace_path"],
            "manifest_path": latest_entry["manifest_path"],
            "validation_result_path": latest_entry["validation_result_path"],
            "generated_at": latest_entry["generated_at"],
            "validated_at": latest_entry["validated_at"],
            "validation_status": latest_entry["validation_status"],
            "warning_count": latest_entry["warning_count"],
            "error_count": latest_entry["error_count"],
        }

    return latest_by_mode


def build_latest_workspace_overall(
    workspace_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not workspace_entries:
        return None

    preferred_entries = [
        entry for entry in workspace_entries if entry["manifest_path"] is not None
    ]
    candidate_entries = preferred_entries or workspace_entries
    latest_entry = max(
        candidate_entries,
        key=lambda entry: (entry["generated_at_sort"], entry["workspace_name"]),
    )
    return {
        "workspace_path": latest_entry["workspace_path"],
        "mode": latest_entry["mode"],
        "manifest_path": latest_entry["manifest_path"],
        "validation_result_path": latest_entry["validation_result_path"],
        "generated_at": latest_entry["generated_at"],
        "validated_at": latest_entry["validated_at"],
        "validation_status": latest_entry["validation_status"],
        "warning_count": latest_entry["warning_count"],
        "error_count": latest_entry["error_count"],
        "notes": latest_entry["notes"],
    }


def build_workspace_overview(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered_entries = sorted(
        entries,
        key=lambda entry: (
            entry["generated_at_sort"],
            entry["workspace_name"],
        ),
        reverse=True,
    )

    overview: list[dict[str, Any]] = []
    for entry in ordered_entries:
        overview.append(
            {
                "status": entry["validation_status"],
                "mode": entry["mode"],
                "workspace_path": entry["workspace_path"],
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


def build_summary(workspace_entries: list[dict[str, Any]]) -> dict[str, Any]:
    validated_pass_count = sum(1 for entry in workspace_entries if entry["validation_status"] == "PASS")
    validated_fail_count = sum(1 for entry in workspace_entries if entry["validation_status"] == "FAIL")
    missing_validation_count = sum(1 for entry in workspace_entries if entry["validation_status"] == "WARN")

    return {
        "summary_type": "support_v1_real_pilot_workspace_summary",
        "generated_at": datetime.now().astimezone().isoformat(),
        "real_pilot_workspaces_root": project_relative_path(REAL_PILOT_WORKSPACES_DIR),
        "supported_modes": list(MODE_CONFIGS.keys()),
        "total_workspaces_found": len(workspace_entries),
        "validated_pass_count": validated_pass_count,
        "validated_fail_count": validated_fail_count,
        "missing_validation_count": missing_validation_count,
        "latest_validated_workspace_per_mode": build_latest_validated_by_mode(workspace_entries),
        "latest_workspace_overall": build_latest_workspace_overall(workspace_entries),
        "workspace_overview": build_workspace_overview(workspace_entries),
        "notes": (
            "Compact support_v1 workspace-readiness snapshot built from existing real pilot "
            "workspace folders. It reads validation_result.json when present and does not "
            "rerun workspace validation automatically."
        ),
    }


def render_latest_validated_table(
    latest_by_mode: dict[str, dict[str, Any]],
) -> list[str]:
    lines = [
        "## Latest Validated Workspace Per Mode",
        "",
        "| Mode | Workspace path | Status | Validated at | Warning count | Error count |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]

    for mode in MODE_CONFIGS:
        entry = latest_by_mode.get(mode)
        if entry is None:
            lines.append(f"| `{mode}` | missing | missing | missing | 0 | 0 |")
            continue
        lines.append(
            f"| `{mode}` | `{entry['workspace_path']}` | `{entry['validation_status']}` | "
            f"`{entry['validated_at']}` | {entry['warning_count'] or 0} | {entry['error_count'] or 0} |"
        )

    lines.append("")
    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Support V1 Real Pilot Workspace Summary",
        "",
        (
            "Compact top-level readiness snapshot across the existing real pilot workspaces. "
            "This summary reads `validation_result.json` when present and never reruns "
            "workspace validation."
        ),
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Real pilot workspaces root: `{summary['real_pilot_workspaces_root']}`",
        f"- Total workspaces found: {summary['total_workspaces_found']}",
        f"- Validated pass count: {summary['validated_pass_count']}",
        f"- Validated fail count: {summary['validated_fail_count']}",
        f"- Missing validation count: {summary['missing_validation_count']}",
    ]

    latest_workspace_overall = summary.get("latest_workspace_overall")
    if isinstance(latest_workspace_overall, dict):
        mode = latest_workspace_overall["mode"]
        lines.extend(
            [
                "",
                "## Latest Workspace Overall",
                "",
                f"- Workspace path: `{latest_workspace_overall['workspace_path']}`",
                f"- Mode: `{mode}`" if mode else "- Mode: unknown",
                f"- Status: `{latest_workspace_overall['validation_status']}`",
                (
                    f"- Generated at: `{latest_workspace_overall['generated_at']}`"
                    if latest_workspace_overall["generated_at"]
                    else "- Generated at: missing"
                ),
                (
                    f"- Validated at: `{latest_workspace_overall['validated_at']}`"
                    if latest_workspace_overall["validated_at"]
                    else "- Validated at: missing"
                ),
            ]
        )

    lines.extend(render_latest_validated_table(summary["latest_validated_workspace_per_mode"]))

    lines.extend(
        [
            "## Workspace Overview",
            "",
            "| Status | Mode | Workspace path | Validated at | Note |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    for entry in summary["workspace_overview"]:
        notes = "; ".join(entry["notes"]) if entry["notes"] else "ok"
        mode = f"`{entry['mode']}`" if entry["mode"] else "unknown"
        validated_at = f"`{entry['validated_at']}`" if entry["validated_at"] else "missing"
        lines.append(
            f"| `{entry['status']}` | {mode} | `{entry['workspace_path']}` | {validated_at} | {notes} |"
        )

    lines.append("")
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    temp_path = path.with_name(f"{path.stem}.{uuid4().hex}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(content)
    temp_path.replace(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_name(f"{path.stem}.{uuid4().hex}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_path.replace(path)


def main() -> None:
    workspace_entries = discover_workspaces()
    summary = build_summary(workspace_entries)
    markdown = render_markdown(summary)

    write_json(SUMMARY_JSON_PATH, summary)
    write_text(SUMMARY_MARKDOWN_PATH, markdown)

    print(f"total_workspaces_scanned: {summary['total_workspaces_found']}")
    print(f"validated_pass_count: {summary['validated_pass_count']}")
    print(f"validated_fail_count: {summary['validated_fail_count']}")
    print(f"missing_validation_count: {summary['missing_validation_count']}")
    print(f"summary_json_path: {project_relative_path(SUMMARY_JSON_PATH)}")
    print(f"summary_markdown_path: {project_relative_path(SUMMARY_MARKDOWN_PATH)}")


if __name__ == "__main__":
    main()
