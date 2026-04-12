from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from evaluate_support_labels import format_percent, project_relative_path


ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
EXPORT_PATH = ARTIFACTS_DIR / "support_v1_readiness_memo.md"
RUN_COMMAND = "py use_cases/support_v1/build_support_v1_readiness_memo.py"

INGEST_COMPARISON_PATH = ARTIFACTS_DIR / "support_ingest_modality_comparison.json"
CONTRACT_VALIDATION_PATH = ARTIFACTS_DIR / "helpdesk_export_contract_validation.json"

PACK_COMPARISON_CONFIGS: tuple[dict[str, str], ...] = (
    {
        "modality": "labeled_support_packs",
        "display_name": "labeled support packs",
        "artifact_path": "support_label_pack_comparison.json",
    },
    {
        "modality": "raw_ingest_packs",
        "display_name": "raw-ingest packs",
        "artifact_path": "support_raw_ingest_pack_comparison.json",
    },
    {
        "modality": "csv_ingest_packs",
        "display_name": "csv-ingest packs",
        "artifact_path": "support_csv_ingest_pack_comparison.json",
    },
    {
        "modality": "mapped_ingest_packs",
        "display_name": "mapped-ingest packs",
        "artifact_path": "support_mapped_ingest_pack_comparison.json",
    },
    {
        "modality": "zendesk_like_ingest_packs",
        "display_name": "Zendesk-like ingest packs",
        "artifact_path": "support_zendesk_like_pack_comparison.json",
    },
)
ACCURACY_TOLERANCE = 1e-12


def accuracies_match(left: float, right: float) -> bool:
    return abs(left - right) <= ACCURACY_TOLERANCE


def format_delta(value: float) -> str:
    if value > 0:
        return f"+{format_percent(value)}"
    if value < 0:
        return f"-{format_percent(abs(value))}"
    return format_percent(0.0)


def format_method_names(method_names: Iterable[str]) -> str:
    quoted = [f"`{method_name}`" for method_name in method_names]
    if not quoted:
        return ""
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} and {quoted[1]}"
    return f"{', '.join(quoted[:-1])}, and {quoted[-1]}"


def load_json_artifact(path: Path, *, used_paths: list[Path], required: bool) -> dict[str, Any] | None:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required artifact not found: {project_relative_path(path)}")
        return None

    used_paths.append(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_pack_comparison_artifacts(
    *,
    used_paths: list[Path],
) -> list[dict[str, Any]]:
    pack_artifacts: list[dict[str, Any]] = []

    for config in PACK_COMPARISON_CONFIGS:
        path = ARTIFACTS_DIR / config["artifact_path"]
        payload = load_json_artifact(path, used_paths=used_paths, required=False)
        if payload is None:
            continue
        pack_artifacts.append(
            {
                "modality": config["modality"],
                "display_name": config["display_name"],
                "artifact_path": path,
                "payload": payload,
            }
        )

    if not pack_artifacts:
        raise FileNotFoundError(
            "No support_v1 pack comparison artifacts were found in use_cases/support_v1/artifacts."
        )

    return pack_artifacts


def build_modality_record(pack_artifact: dict[str, Any]) -> dict[str, Any]:
    slices = pack_artifact["payload"]["slices"]
    largest_slice_name, largest_slice = max(
        slices.items(),
        key=lambda item: (item[1]["total_labels"], item[0]),
    )
    calibrated_accuracy = float(largest_slice["accuracies"]["calibrated_iml"])
    iml_accuracy = float(largest_slice["accuracies"]["iml"])
    best_baseline_accuracy = max(
        float(largest_slice["accuracies"]["naive_summary"]),
        float(largest_slice["accuracies"]["full_history"]),
    )
    best_baseline_method_names = [
        method_name
        for method_name in ("naive_summary", "full_history")
        if accuracies_match(
            float(largest_slice["accuracies"][method_name]),
            best_baseline_accuracy,
        )
    ]
    best_non_calibrated_accuracy = max(
        iml_accuracy,
        float(largest_slice["accuracies"]["naive_summary"]),
        float(largest_slice["accuracies"]["full_history"]),
    )

    return {
        "modality": pack_artifact["modality"],
        "display_name": pack_artifact["display_name"],
        "largest_slice": largest_slice_name,
        "label_count": int(largest_slice["total_labels"]),
        "iml_accuracy": iml_accuracy,
        "calibrated_iml_accuracy": calibrated_accuracy,
        "best_baseline_accuracy": best_baseline_accuracy,
        "best_baseline_method_names": best_baseline_method_names,
        "beats_best_baseline": (
            calibrated_accuracy > best_baseline_accuracy
            and not accuracies_match(calibrated_accuracy, best_baseline_accuracy)
        ),
        "margin_vs_best_baseline": calibrated_accuracy - best_baseline_accuracy,
        "best_non_calibrated_accuracy": best_non_calibrated_accuracy,
        "margin_vs_best_non_calibrated": (
            calibrated_accuracy - best_non_calibrated_accuracy
        ),
    }


def build_overall_iml_position(pack_artifacts: list[dict[str, Any]]) -> dict[str, int]:
    improved_slices = 0
    tied_slices = 0
    regressed_slices = 0

    for pack_artifact in pack_artifacts:
        for slice_payload in pack_artifact["payload"]["slices"].values():
            calibrated_accuracy = float(slice_payload["accuracies"]["calibrated_iml"])
            iml_accuracy = float(slice_payload["accuracies"]["iml"])
            if accuracies_match(calibrated_accuracy, iml_accuracy):
                tied_slices += 1
            elif calibrated_accuracy > iml_accuracy:
                improved_slices += 1
            else:
                regressed_slices += 1

    return {
        "improved_slices": improved_slices,
        "tied_slices": tied_slices,
        "regressed_slices": regressed_slices,
        "total_slices": improved_slices + tied_slices + regressed_slices,
    }


def select_strongest_evidence(modality_records: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        modality_records,
        key=lambda record: (
            record["margin_vs_best_non_calibrated"],
            record["label_count"],
            record["calibrated_iml_accuracy"],
            record["modality"],
        ),
    )


def select_modality_needing_more_data(modality_records: list[dict[str, Any]]) -> dict[str, Any]:
    return min(
        modality_records,
        key=lambda record: (
            record["label_count"],
            record["margin_vs_best_baseline"],
            record["calibrated_iml_accuracy"],
            record["modality"],
        ),
    )


def build_main_gap_lines(
    *,
    modality_records: list[dict[str, Any]],
    contract_validation: dict[str, Any],
) -> list[str]:
    weakest_evidence = select_modality_needing_more_data(modality_records)
    thinnest_margin = min(
        modality_records,
        key=lambda record: (
            record["margin_vs_best_baseline"],
            record["label_count"],
            record["modality"],
        ),
    )
    input_names = [
        Path(str(input_result["input_path"])).name
        for input_result in contract_validation.get("inputs", [])
    ]

    return [
        (
            "- Ingest evidence is still small-sample outside the labeled pack comparison: "
            + ", ".join(
                f"{record['display_name']} {record['label_count']} labels"
                for record in modality_records
                if record["modality"] != "labeled_support_packs"
            )
            + "."
        ),
        (
            f"- The weakest evidence path by sample size is {weakest_evidence['display_name']} "
            f"at {weakest_evidence['label_count']} labels on `{weakest_evidence['largest_slice']}`, "
            f"while {thinnest_margin['display_name']} has the smallest largest-slice lead over "
            f"the best baseline at {format_delta(float(thinnest_margin['margin_vs_best_baseline']))}."
        ),
        (
            "- Current readiness is still based on included sample exports rather than a "
            "real customer export; the validator inputs in evidence are "
            + ", ".join(f"`{name}`" for name in input_names)
            + "."
        ),
    ]


def build_recommended_next_step(modality_needing_more_data: dict[str, Any]) -> str:
    if modality_needing_more_data["modality"] == "zendesk_like_ingest_packs":
        return (
            "Obtain one real Zendesk-like export, run it through the existing contract "
            "validator, and add it as one more labeled comparison slice."
        )
    return (
        f"Add one more labeled {modality_needing_more_data['display_name']} slice so the "
        "current weakest modality moves beyond its present evidence base."
    )


def build_markdown_report(
    *,
    ingest_comparison: dict[str, Any] | None,
    contract_validation: dict[str, Any],
    modality_records: list[dict[str, Any]],
    overall_iml_position: dict[str, int],
) -> str:
    strongest_evidence = select_strongest_evidence(modality_records)
    modality_needing_more_data = select_modality_needing_more_data(modality_records)
    contract_inputs = contract_validation.get("inputs", [])

    lines = [
        "# Support V1 Readiness Memo",
        "",
        f"Run with `{RUN_COMMAND}`.",
        "",
        (
            "This memo adds one compact top-level support_v1 readiness summary by "
            "consolidating the current ingest, validation, and evaluation artifacts "
            "already written in the repo."
        ),
        "",
        "## Current capability snapshot",
        "",
        (
            "- support_v1 currently has labeled pack evaluation, raw-ingest evaluation, "
            "CSV-ingest evaluation, mapped-ingest evaluation, Zendesk-like evaluation, "
            "and export contract validation."
        ),
        (
            "- The current prototype coverage spans raw JSON export ingest, flat CSV "
            "ingest, mapping-based CSV ingest, and Zendesk-like nested export ingest."
        ),
        "",
        "## Current evaluation position",
        "",
        (
            f"- Overall, calibrated IML {'never loses to' if overall_iml_position['regressed_slices'] == 0 else 'is mixed against'} "
            f"default IML across the loaded comparison artifacts: "
            f"{overall_iml_position['improved_slices']} improved, "
            f"{overall_iml_position['tied_slices']} tied, "
            f"{overall_iml_position['regressed_slices']} regressed, "
            f"{overall_iml_position['total_slices']} total slices."
        ),
    ]

    if ingest_comparison is not None:
        ingest_summary = ingest_comparison["top_level_summary"][
            "calibrated_iml_vs_default_iml_across_modalities"
        ]
        lines.append(
            (
                "- The unified ingest comparison artifact agrees on the implemented "
                "labeled/raw/CSV/Zendesk-like set: "
                f"{ingest_summary['improved_slice_count']} improved, "
                f"{ingest_summary['tied_slice_count']} tied, "
                f"{ingest_summary['total_slice_count']} total slices."
            )
        )

    lines.extend(
        [
            (
                f"- On the largest slice in each loaded modality, calibrated IML {'beats' if all(record['beats_best_baseline'] for record in modality_records) else 'does not beat'} "
                "the best baseline across "
                f"{sum(1 for record in modality_records if record['beats_best_baseline'])} "
                f"of {len(modality_records)} modalities."
            )
        ]
    )

    for record in modality_records:
        lines.append(
            (
                f"  - {record['display_name']}: `{record['largest_slice']}` "
                f"({record['label_count']} labels), calibrated IML "
                f"{format_percent(float(record['calibrated_iml_accuracy']))} vs best baseline "
                f"{format_percent(float(record['best_baseline_accuracy']))} "
                f"from {format_method_names(record['best_baseline_method_names'])} "
                f"({format_delta(float(record['margin_vs_best_baseline']))})."
            )
        )

    lines.extend(
        [
            (
                f"- Strongest current evidence: {strongest_evidence['display_name']} on "
                f"`{strongest_evidence['largest_slice']}` with "
                f"{strongest_evidence['label_count']} labels and a "
                f"{format_delta(float(strongest_evidence['margin_vs_best_non_calibrated']))} "
                "lead over the best non-calibrated method."
            ),
            (
                f"- Modality needing more data: {modality_needing_more_data['display_name']} "
                f"because its current largest slice is only {modality_needing_more_data['label_count']} labels."
            ),
            "",
            "## Ingest readiness",
            "",
            (
                "- Export styles supported in prototype form today: raw JSON exports, "
                "flat CSV exports, mapping-based CSV exports, and Zendesk-like nested exports."
            ),
            (
                f"- The included export contract validator currently {'passes' if contract_validation.get('overall_passed') else 'does not pass'} "
                f"for the bundled sample inputs ({len(contract_inputs)} inputs checked)."
            ),
        ]
    )

    for input_result in contract_inputs:
        lines.append(
            (
                f"  - `{Path(str(input_result['input_path'])).name}`: "
                f"{'pass' if input_result['passed'] else 'fail'} "
                f"({input_result['detected_format']}, "
                f"{input_result['error_count']} errors, "
                f"{input_result['warning_count']} warnings)."
            )
        )

    lines.extend(
        [
            "",
            "## Main gaps",
            "",
        ]
    )
    lines.extend(build_main_gap_lines(modality_records=modality_records, contract_validation=contract_validation))
    lines.extend(
        [
            "",
            "## Recommended next step",
            "",
            f"- {build_recommended_next_step(modality_needing_more_data)}",
            "",
        ]
    )
    return "\n".join(lines)


def export_markdown_report(markdown_report: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_export_path = EXPORT_PATH.with_name(f"{EXPORT_PATH.stem}.{uuid4().hex}.tmp")
    with temp_export_path.open("w", encoding="utf-8") as handle:
        handle.write(markdown_report)
        if not markdown_report.endswith("\n"):
            handle.write("\n")
    temp_export_path.replace(EXPORT_PATH)
    return EXPORT_PATH


def print_summary(*, used_paths: list[Path], export_path: Path) -> None:
    for path in used_paths:
        print(f"source_artifact: {project_relative_path(path)}")
    print(f"output_memo: {project_relative_path(export_path)}")


def main() -> None:
    used_paths: list[Path] = []
    ingest_comparison = load_json_artifact(
        INGEST_COMPARISON_PATH,
        used_paths=used_paths,
        required=False,
    )
    contract_validation = load_json_artifact(
        CONTRACT_VALIDATION_PATH,
        used_paths=used_paths,
        required=True,
    )
    pack_artifacts = load_pack_comparison_artifacts(used_paths=used_paths)
    modality_records = [build_modality_record(pack_artifact) for pack_artifact in pack_artifacts]
    overall_iml_position = build_overall_iml_position(pack_artifacts)
    markdown_report = build_markdown_report(
        ingest_comparison=ingest_comparison,
        contract_validation=contract_validation,
        modality_records=modality_records,
        overall_iml_position=overall_iml_position,
    )
    export_path = export_markdown_report(markdown_report)
    print_summary(used_paths=used_paths, export_path=export_path)


if __name__ == "__main__":
    main()
