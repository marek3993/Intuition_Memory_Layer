from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4
from pilot_ops.io import write_manifest as write_json_manifest, write_report

from build_support_v1_pilot_execution_bundle import MODE_CONFIGS, SCRIPT_DIR, project_relative_path


PILOT_PACKAGES_DIR = SCRIPT_DIR / "artifacts" / "pilot_packages"
PILOT_PACKAGE_MANIFEST_FILENAME = "pilot_package_manifest.json"
SUMMARY_JSON_PATH = SCRIPT_DIR / "artifacts" / "support_v1_pilot_package_summary.json"
SUMMARY_MARKDOWN_PATH = SCRIPT_DIR / "artifacts" / "support_v1_pilot_package_summary.md"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {project_relative_path(path)}")
    return data


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


def discover_valid_packages() -> list[dict[str, Any]]:
    if not PILOT_PACKAGES_DIR.exists():
        return []

    discovered: list[dict[str, Any]] = []
    for package_dir in sorted(PILOT_PACKAGES_DIR.iterdir()):
        if not package_dir.is_dir():
            continue

        manifest_path = package_dir / PILOT_PACKAGE_MANIFEST_FILENAME
        if not manifest_path.exists():
            continue

        try:
            manifest = load_json(manifest_path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue

        selected_mode = manifest.get("selected_mode")
        if not isinstance(selected_mode, str) or selected_mode not in MODE_CONFIGS:
            continue

        source_execution_bundle_used = manifest.get("source_execution_bundle_used")
        if not isinstance(source_execution_bundle_used, dict):
            source_execution_bundle_used = {}

        included_docs = manifest.get("included_docs")
        included_docs_count = len(included_docs) if isinstance(included_docs, list) else 0
        sort_time, sort_name = resolve_package_sort_key(manifest, package_dir)

        discovered.append(
            {
                "mode": selected_mode,
                "package_dir": package_dir,
                "manifest_path": manifest_path,
                "manifest": manifest,
                "included_docs_count": included_docs_count,
                "source_execution_bundle_used": source_execution_bundle_used,
                "sort_time": sort_time,
                "sort_name": sort_name,
            }
        )

    return discovered


def build_mode_summary(package_entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "latest_package_folder": project_relative_path(package_entry["package_dir"]),
        "manifest_path": project_relative_path(package_entry["manifest_path"]),
        "generated_at": package_entry["manifest"].get("generated_at"),
        "source_execution_bundle_used": package_entry["source_execution_bundle_used"],
        "included_docs_count": package_entry["included_docs_count"],
    }


def build_summary(valid_packages: list[dict[str, Any]]) -> dict[str, Any]:
    supported_modes = list(MODE_CONFIGS.keys())
    latest_by_mode: dict[str, dict[str, Any]] = {}

    for mode in supported_modes:
        mode_packages = [entry for entry in valid_packages if entry["mode"] == mode]
        if not mode_packages:
            continue
        mode_packages.sort(
            key=lambda entry: (entry["sort_time"], entry["sort_name"]),
            reverse=True,
        )
        latest_by_mode[mode] = build_mode_summary(mode_packages[0])

    modes_with_package = [mode for mode in supported_modes if mode in latest_by_mode]
    modes_missing_package = [mode for mode in supported_modes if mode not in latest_by_mode]

    latest_package_overall: dict[str, Any] | None = None
    if valid_packages:
        latest_overall_entry = max(
            valid_packages,
            key=lambda entry: (entry["sort_time"], entry["sort_name"]),
        )
        latest_package_overall = {
            "mode": latest_overall_entry["mode"],
            **build_mode_summary(latest_overall_entry),
        }

    return {
        "summary_type": "support_v1_pilot_package_summary",
        "generated_at": datetime.now().astimezone().isoformat(),
        "pilot_packages_root": project_relative_path(PILOT_PACKAGES_DIR),
        "supported_modes": supported_modes,
        "total_package_count_found": len(valid_packages),
        "modes_with_package": modes_with_package,
        "modes_missing_package": modes_missing_package,
        "latest_package_overall": latest_package_overall,
        "packages_by_mode": latest_by_mode,
        "notes": (
            "Compact summary of the existing reviewer-ready support_v1 pilot packages, "
            "showing the latest package per supported mode without rebuilding any package "
            "or rerunning evaluations."
        ),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Support V1 Pilot Package Summary",
        "",
        (
            "Compact summary of the existing reviewer-ready pilot packages so a human can "
            "quickly see which mode already has a package and where the latest reviewer-ready "
            "folder lives."
        ),
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Pilot packages root: `{summary['pilot_packages_root']}`",
        f"- Total package count found: {summary['total_package_count_found']}",
        f"- Modes covered: {', '.join(summary['modes_with_package']) if summary['modes_with_package'] else 'none'}",
        (
            f"- Missing modes: {', '.join(summary['modes_missing_package'])}"
            if summary["modes_missing_package"]
            else "- Missing modes: none"
        ),
    ]

    latest_package_overall = summary.get("latest_package_overall")
    if isinstance(latest_package_overall, dict):
        lines.extend(
            [
                "",
                "## Latest Package Overall",
                "",
                f"- Mode: `{latest_package_overall['mode']}`",
                f"- Latest package folder: `{latest_package_overall['latest_package_folder']}`",
                f"- Manifest path: `{latest_package_overall['manifest_path']}`",
                f"- Generated at: `{latest_package_overall['generated_at']}`",
                f"- Source execution bundle used: `{latest_package_overall['source_execution_bundle_used'].get('bundle_output_folder', 'n/a')}`",
                f"- Included docs count: {latest_package_overall['included_docs_count']}",
            ]
        )

    lines.extend(
        [
            "",
            "## Mode Coverage",
            "",
            "| Mode | Latest package folder | Manifest path | Generated at | Source execution bundle used | Included docs count |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )

    for mode in summary["supported_modes"]:
        package = summary["packages_by_mode"].get(mode)
        if package is None:
            lines.append(f"| `{mode}` | missing | missing | missing | missing | 0 |")
            continue

        source_bundle_folder = package["source_execution_bundle_used"].get("bundle_output_folder", "n/a")
        lines.append(
            f"| `{mode}` | `{package['latest_package_folder']}` | `{package['manifest_path']}` | "
            f"`{package['generated_at']}` | `{source_bundle_folder}` | {package['included_docs_count']} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    valid_packages = discover_valid_packages()
    summary = build_summary(valid_packages)
    markdown = render_markdown(summary)

    write_json_manifest(SUMMARY_JSON_PATH, summary)
    write_report(SUMMARY_MARKDOWN_PATH, markdown)

    print(f"total_package_count_found: {summary['total_package_count_found']}")
    print(
        "modes_covered: "
        f"{', '.join(summary['modes_with_package']) if summary['modes_with_package'] else 'none'}"
    )
    print(f"summary_json_path: {project_relative_path(SUMMARY_JSON_PATH)}")
    print(f"summary_markdown_path: {project_relative_path(SUMMARY_MARKDOWN_PATH)}")


if __name__ == "__main__":
    main()
