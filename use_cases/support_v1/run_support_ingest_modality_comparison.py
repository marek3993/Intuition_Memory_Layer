from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

for candidate in (PROJECT_ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from calibration import CALIBRATION_NAME, CALIBRATION_VERSION, WINNING_SETTINGS
from evaluate_support_labels import format_percent, project_relative_path
from run_support_csv_ingest_pack_comparison import (
    CSV_SAMPLE_A_LABELS_PATH,
    CSV_SAMPLE_A_PATH,
    CSV_SAMPLE_B_LABELS_PATH,
    CSV_SAMPLE_B_PATH,
    evaluate_slice as evaluate_csv_slice,
)
from run_support_mapped_ingest_pack_comparison import (
    MAPPED_SAMPLE_A_LABELS_PATH,
    MAPPED_SAMPLE_A_PATH,
    MAPPED_SAMPLE_B_LABELS_PATH,
    MAPPED_SAMPLE_B_PATH,
    MAPPED_SAMPLE_C_LABELS_PATH,
    MAPPED_SAMPLE_C_PATH,
    DEFAULT_MAPPING_PATH as MAPPED_MAPPING_PATH,
    evaluate_slice as evaluate_mapped_slice,
    load_mapping as load_mapped_mapping,
)
from run_support_label_pack_comparison import (
    PACK_A_CASES_PATH,
    PACK_A_LABELS_PATH,
    PACK_B_CASES_PATH,
    PACK_B_LABELS_PATH,
    PACK_C_CASES_PATH,
    PACK_C_LABELS_PATH,
    PACK_D_CASES_PATH,
    PACK_D_LABELS_PATH,
    evaluate_slice as evaluate_labeled_slice,
)
from run_support_raw_ingest_pack_comparison import (
    RAW_SAMPLE_A_LABELS_PATH,
    RAW_SAMPLE_A_PATH,
    RAW_SAMPLE_B_LABELS_PATH,
    RAW_SAMPLE_B_PATH,
    evaluate_slice as evaluate_raw_slice,
)
from run_support_zendesk_like_pack_comparison import (
    ZENDESK_SAMPLE_A_LABELS_PATH,
    ZENDESK_SAMPLE_A_PATH,
    ZENDESK_SAMPLE_B_LABELS_PATH,
    ZENDESK_SAMPLE_B_PATH,
    ZENDESK_SAMPLE_C_LABELS_PATH,
    ZENDESK_SAMPLE_C_PATH,
    evaluate_slice as evaluate_zendesk_slice,
)


ARTIFACTS_DIR = SCRIPT_DIR / "artifacts"
EXPORT_PATH = ARTIFACTS_DIR / "support_ingest_modality_comparison.json"
MARKDOWN_EXPORT_PATH = ARTIFACTS_DIR / "support_ingest_modality_comparison.md"
RUN_COMMAND = "py use_cases/support_v1/run_support_ingest_modality_comparison.py"
METHOD_NAMES: tuple[str, ...] = (
    "iml",
    "calibrated_iml",
    "naive_summary",
    "full_history",
)
ACCURACY_TOLERANCE = 1e-12


SliceEvaluator = Callable[..., dict[str, Any]]


def accuracies_match(left: float, right: float) -> bool:
    return abs(left - right) <= ACCURACY_TOLERANCE


def format_delta(value: float) -> str:
    if value > 0:
        return f"+{format_percent(value)}"
    if value < 0:
        return f"-{format_percent(abs(value))}"
    return format_percent(0.0)


def build_modality_configs() -> tuple[dict[str, Any], ...]:
    mapped_mapping = load_mapped_mapping(MAPPED_MAPPING_PATH)

    return (
        {
            "modality": "labeled_support_packs",
            "display_name": "labeled support packs",
            "slices": (
                {
                    "slice_name": "pack_a",
                    "evaluator": evaluate_labeled_slice,
                    "kwargs": {
                        "cases_paths": (PACK_A_CASES_PATH,),
                        "labels_paths": (PACK_A_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "pack_b",
                    "evaluator": evaluate_labeled_slice,
                    "kwargs": {
                        "cases_paths": (PACK_B_CASES_PATH,),
                        "labels_paths": (PACK_B_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "pack_c",
                    "evaluator": evaluate_labeled_slice,
                    "kwargs": {
                        "cases_paths": (PACK_C_CASES_PATH,),
                        "labels_paths": (PACK_C_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "pack_d",
                    "evaluator": evaluate_labeled_slice,
                    "kwargs": {
                        "cases_paths": (PACK_D_CASES_PATH,),
                        "labels_paths": (PACK_D_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "combined_abcd",
                    "evaluator": evaluate_labeled_slice,
                    "kwargs": {
                        "cases_paths": (
                            PACK_A_CASES_PATH,
                            PACK_B_CASES_PATH,
                            PACK_C_CASES_PATH,
                            PACK_D_CASES_PATH,
                        ),
                        "labels_paths": (
                            PACK_A_LABELS_PATH,
                            PACK_B_LABELS_PATH,
                            PACK_C_LABELS_PATH,
                            PACK_D_LABELS_PATH,
                        ),
                    },
                },
            ),
        },
        {
            "modality": "raw_ingest_packs",
            "display_name": "raw-ingest packs",
            "slices": (
                {
                    "slice_name": "raw_sample_a",
                    "evaluator": evaluate_raw_slice,
                    "kwargs": {
                        "raw_paths": (RAW_SAMPLE_A_PATH,),
                        "labels_paths": (RAW_SAMPLE_A_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "raw_sample_b",
                    "evaluator": evaluate_raw_slice,
                    "kwargs": {
                        "raw_paths": (RAW_SAMPLE_B_PATH,),
                        "labels_paths": (RAW_SAMPLE_B_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "combined_ab",
                    "evaluator": evaluate_raw_slice,
                    "kwargs": {
                        "raw_paths": (RAW_SAMPLE_A_PATH, RAW_SAMPLE_B_PATH),
                        "labels_paths": (
                            RAW_SAMPLE_A_LABELS_PATH,
                            RAW_SAMPLE_B_LABELS_PATH,
                        ),
                    },
                },
            ),
        },
        {
            "modality": "csv_ingest_packs",
            "display_name": "csv-ingest packs",
            "slices": (
                {
                    "slice_name": "csv_sample_a",
                    "evaluator": evaluate_csv_slice,
                    "kwargs": {
                        "csv_paths": (CSV_SAMPLE_A_PATH,),
                        "labels_paths": (CSV_SAMPLE_A_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "csv_sample_b",
                    "evaluator": evaluate_csv_slice,
                    "kwargs": {
                        "csv_paths": (CSV_SAMPLE_B_PATH,),
                        "labels_paths": (CSV_SAMPLE_B_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "combined_ab",
                    "evaluator": evaluate_csv_slice,
                    "kwargs": {
                        "csv_paths": (CSV_SAMPLE_A_PATH, CSV_SAMPLE_B_PATH),
                        "labels_paths": (
                            CSV_SAMPLE_A_LABELS_PATH,
                            CSV_SAMPLE_B_LABELS_PATH,
                        ),
                    },
                },
            ),
        },
        {
            "modality": "mapped_ingest_packs",
            "display_name": "mapped-ingest packs",
            "slices": (
                {
                    "slice_name": "mapped_sample_a",
                    "evaluator": evaluate_mapped_slice,
                    "kwargs": {
                        "csv_paths": (MAPPED_SAMPLE_A_PATH,),
                        "labels_paths": (MAPPED_SAMPLE_A_LABELS_PATH,),
                        "mapping": mapped_mapping,
                        "mapping_path": MAPPED_MAPPING_PATH,
                    },
                },
                {
                    "slice_name": "mapped_sample_b",
                    "evaluator": evaluate_mapped_slice,
                    "kwargs": {
                        "csv_paths": (MAPPED_SAMPLE_B_PATH,),
                        "labels_paths": (MAPPED_SAMPLE_B_LABELS_PATH,),
                        "mapping": mapped_mapping,
                        "mapping_path": MAPPED_MAPPING_PATH,
                    },
                },
                {
                    "slice_name": "mapped_sample_c",
                    "evaluator": evaluate_mapped_slice,
                    "kwargs": {
                        "csv_paths": (MAPPED_SAMPLE_C_PATH,),
                        "labels_paths": (MAPPED_SAMPLE_C_LABELS_PATH,),
                        "mapping": mapped_mapping,
                        "mapping_path": MAPPED_MAPPING_PATH,
                    },
                },
                {
                    "slice_name": "combined_abc",
                    "evaluator": evaluate_mapped_slice,
                    "kwargs": {
                        "csv_paths": (
                            MAPPED_SAMPLE_A_PATH,
                            MAPPED_SAMPLE_B_PATH,
                            MAPPED_SAMPLE_C_PATH,
                        ),
                        "labels_paths": (
                            MAPPED_SAMPLE_A_LABELS_PATH,
                            MAPPED_SAMPLE_B_LABELS_PATH,
                            MAPPED_SAMPLE_C_LABELS_PATH,
                        ),
                        "mapping": mapped_mapping,
                        "mapping_path": MAPPED_MAPPING_PATH,
                    },
                },
            ),
        },
        {
            "modality": "zendesk_like_ingest_packs",
            "display_name": "zendesk-like ingest packs",
            "slices": (
                {
                    "slice_name": "zendesk_sample_a",
                    "evaluator": evaluate_zendesk_slice,
                    "kwargs": {
                        "export_paths": (ZENDESK_SAMPLE_A_PATH,),
                        "labels_paths": (ZENDESK_SAMPLE_A_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "zendesk_sample_b",
                    "evaluator": evaluate_zendesk_slice,
                    "kwargs": {
                        "export_paths": (ZENDESK_SAMPLE_B_PATH,),
                        "labels_paths": (ZENDESK_SAMPLE_B_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "zendesk_sample_c",
                    "evaluator": evaluate_zendesk_slice,
                    "kwargs": {
                        "export_paths": (ZENDESK_SAMPLE_C_PATH,),
                        "labels_paths": (ZENDESK_SAMPLE_C_LABELS_PATH,),
                    },
                },
                {
                    "slice_name": "combined_abc",
                    "evaluator": evaluate_zendesk_slice,
                    "kwargs": {
                        "export_paths": (
                            ZENDESK_SAMPLE_A_PATH,
                            ZENDESK_SAMPLE_B_PATH,
                            ZENDESK_SAMPLE_C_PATH,
                        ),
                        "labels_paths": (
                            ZENDESK_SAMPLE_A_LABELS_PATH,
                            ZENDESK_SAMPLE_B_LABELS_PATH,
                            ZENDESK_SAMPLE_C_LABELS_PATH,
                        ),
                    },
                },
            ),
        },
    )


def evaluate_modality_slice(
    modality: str,
    display_name: str,
    slice_name: str,
    evaluator: SliceEvaluator,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    slice_result = evaluator(slice_name, **kwargs)
    return {
        "modality": modality,
        "modality_display_name": display_name,
        **slice_result,
    }


def build_modality_results() -> list[dict[str, Any]]:
    modality_results: list[dict[str, Any]] = []

    for modality_config in build_modality_configs():
        slice_results = [
            evaluate_modality_slice(
                modality=modality_config["modality"],
                display_name=modality_config["display_name"],
                slice_name=slice_config["slice_name"],
                evaluator=slice_config["evaluator"],
                kwargs=dict(slice_config["kwargs"]),
            )
            for slice_config in modality_config["slices"]
        ]
        largest_slice = max(
            slice_results,
            key=lambda result: (result["total_labels"], result["slice_name"]),
        )
        modality_results.append(
            {
                "modality": modality_config["modality"],
                "display_name": modality_config["display_name"],
                "largest_slice_name": largest_slice["slice_name"],
                "slice_names": [slice_result["slice_name"] for slice_result in slice_results],
                "slices": slice_results,
            }
        )

    return modality_results


def build_summary_rows(modality_results: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "modality": slice_result["modality"],
            "slice": slice_result["slice_name"],
            "label_count": slice_result["total_labels"],
            "iml_accuracy": slice_result["accuracies"]["iml"],
            "calibrated_iml_accuracy": slice_result["accuracies"]["calibrated_iml"],
            "naive_summary_accuracy": slice_result["accuracies"]["naive_summary"],
            "full_history_accuracy": slice_result["accuracies"]["full_history"],
        }
        for modality_result in modality_results
        for slice_result in modality_result["slices"]
    ]


def build_calibrated_vs_iml_summary(
    modality_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    modality_breakdown: list[dict[str, Any]] = []
    improved_slice_count = 0
    tied_slice_count = 0
    total_slice_count = 0

    for modality_result in modality_results:
        improved_slices = 0
        tied_slices = 0
        regressed_slices = 0
        slice_notes: list[dict[str, Any]] = []

        for slice_result in modality_result["slices"]:
            calibrated_accuracy = float(slice_result["accuracies"]["calibrated_iml"])
            default_accuracy = float(slice_result["accuracies"]["iml"])
            delta = calibrated_accuracy - default_accuracy
            total_slice_count += 1

            if accuracies_match(calibrated_accuracy, default_accuracy):
                tied_slices += 1
                tied_slice_count += 1
                relation = "ties"
            elif calibrated_accuracy > default_accuracy:
                improved_slices += 1
                improved_slice_count += 1
                relation = "beats"
            else:
                regressed_slices += 1
                relation = "loses_to"

            slice_notes.append(
                {
                    "slice": slice_result["slice_name"],
                    "relation": relation,
                    "accuracy_delta": delta,
                }
            )

        modality_breakdown.append(
            {
                "modality": modality_result["modality"],
                "display_name": modality_result["display_name"],
                "improved_slices": improved_slices,
                "tied_slices": tied_slices,
                "regressed_slices": regressed_slices,
                "slice_notes": slice_notes,
            }
        )

    if improved_slice_count == total_slice_count:
        overall = "calibrated_iml_beats_default_iml_on_every_slice"
    elif improved_slice_count + tied_slice_count == total_slice_count:
        overall = "calibrated_iml_never_loses_to_default_iml_but_not_every_slice_improves"
    else:
        overall = "calibrated_iml_is_mixed_against_default_iml"

    return {
        "overall": overall,
        "improved_slice_count": improved_slice_count,
        "tied_slice_count": tied_slice_count,
        "total_slice_count": total_slice_count,
        "modality_breakdown": modality_breakdown,
    }


def build_largest_slice_baseline_summary(
    modality_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    modality_breakdown: list[dict[str, Any]] = []
    beats_both_count = 0

    for modality_result in modality_results:
        largest_slice = next(
            slice_result
            for slice_result in modality_result["slices"]
            if slice_result["slice_name"] == modality_result["largest_slice_name"]
        )
        calibrated_accuracy = float(largest_slice["accuracies"]["calibrated_iml"])
        naive_accuracy = float(largest_slice["accuracies"]["naive_summary"])
        full_history_accuracy = float(largest_slice["accuracies"]["full_history"])
        best_baseline_accuracy = max(naive_accuracy, full_history_accuracy)
        beats_both = (
            calibrated_accuracy > naive_accuracy
            and not accuracies_match(calibrated_accuracy, naive_accuracy)
            and calibrated_accuracy > full_history_accuracy
            and not accuracies_match(calibrated_accuracy, full_history_accuracy)
        )
        if beats_both:
            beats_both_count += 1

        modality_breakdown.append(
            {
                "modality": modality_result["modality"],
                "display_name": modality_result["display_name"],
                "largest_slice": largest_slice["slice_name"],
                "label_count": largest_slice["total_labels"],
                "calibrated_iml_accuracy": calibrated_accuracy,
                "best_baseline_accuracy": best_baseline_accuracy,
                "best_baseline_method_names": [
                    method_name
                    for method_name in ("naive_summary", "full_history")
                    if accuracies_match(
                        float(largest_slice["accuracies"][method_name]),
                        best_baseline_accuracy,
                    )
                ],
                "beats_both_baselines": beats_both,
                "accuracy_delta_vs_best_baseline": (
                    calibrated_accuracy - best_baseline_accuracy
                ),
            }
        )

    return {
        "all_modalities": beats_both_count == len(modality_results),
        "beats_both_count": beats_both_count,
        "total_modalities": len(modality_results),
        "modality_breakdown": modality_breakdown,
    }


def select_strongest_evidence_modality(
    modality_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []

    for modality_result in modality_results:
        largest_slice = next(
            slice_result
            for slice_result in modality_result["slices"]
            if slice_result["slice_name"] == modality_result["largest_slice_name"]
        )
        calibrated_accuracy = float(largest_slice["accuracies"]["calibrated_iml"])
        best_non_calibrated_accuracy = max(
            float(largest_slice["accuracies"][method_name])
            for method_name in ("iml", "naive_summary", "full_history")
        )
        candidates.append(
            {
                "modality": modality_result["modality"],
                "display_name": modality_result["display_name"],
                "largest_slice": largest_slice["slice_name"],
                "label_count": largest_slice["total_labels"],
                "calibrated_iml_accuracy": calibrated_accuracy,
                "best_non_calibrated_accuracy": best_non_calibrated_accuracy,
                "margin_vs_best_non_calibrated": (
                    calibrated_accuracy - best_non_calibrated_accuracy
                ),
            }
        )

    winner = max(
        candidates,
        key=lambda candidate: (
            candidate["margin_vs_best_non_calibrated"],
            candidate["label_count"],
            candidate["calibrated_iml_accuracy"],
            candidate["modality"],
        ),
    )
    winner["selection_basis"] = (
        "largest-slice calibrated_iml lead over the best non-calibrated method, "
        "tie-broken by largest-slice label count"
    )
    return winner


def select_modality_needing_more_data(
    modality_results: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []

    for modality_result in modality_results:
        largest_slice = next(
            slice_result
            for slice_result in modality_result["slices"]
            if slice_result["slice_name"] == modality_result["largest_slice_name"]
        )
        calibrated_accuracy = float(largest_slice["accuracies"]["calibrated_iml"])
        best_baseline_accuracy = max(
            float(largest_slice["accuracies"]["naive_summary"]),
            float(largest_slice["accuracies"]["full_history"]),
        )
        candidates.append(
            {
                "modality": modality_result["modality"],
                "display_name": modality_result["display_name"],
                "largest_slice": largest_slice["slice_name"],
                "label_count": largest_slice["total_labels"],
                "calibrated_iml_accuracy": calibrated_accuracy,
                "margin_vs_best_baseline": calibrated_accuracy - best_baseline_accuracy,
            }
        )

    candidate = min(
        candidates,
        key=lambda item: (
            item["label_count"],
            item["margin_vs_best_baseline"],
            item["calibrated_iml_accuracy"],
            item["modality"],
        ),
    )
    candidate["selection_basis"] = (
        "smallest largest-slice label count, tie-broken by weakest calibrated_iml "
        "margin over the best baseline"
    )
    return candidate


def build_top_level_summary(modality_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    calibrated_vs_iml = build_calibrated_vs_iml_summary(modality_results)
    baseline_on_largest = build_largest_slice_baseline_summary(modality_results)
    strongest_evidence = select_strongest_evidence_modality(modality_results)
    needs_more_data = select_modality_needing_more_data(modality_results)

    if baseline_on_largest["all_modalities"]:
        conclusion = (
            "Calibrated IML clears the best baseline on the largest slice in every "
            "implemented support_v1 modality."
        )
    else:
        conclusion = (
            "Calibrated IML improves across the comparison, but baseline pressure still "
            "depends on modality and slice size."
        )

    return {
        "run_command_powershell": RUN_COMMAND,
        "what_this_adds": (
            "One unified support_v1 runner that executes the existing labeled, raw, "
            "CSV, mapped, and Zendesk-like evaluation paths together and reports "
            "a single cross-modality accuracy table plus compact conclusion."
        ),
        "calibrated_iml_vs_default_iml_across_modalities": calibrated_vs_iml,
        "calibrated_iml_vs_baselines_on_largest_slice_per_modality": baseline_on_largest,
        "strongest_evidence_modality": strongest_evidence,
        "modality_needing_more_data": needs_more_data,
        "overall_conclusion": conclusion,
    }


def build_export_payload(modality_results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    top_level_summary = build_top_level_summary(modality_results)
    return {
        "run_metadata": {
            "evaluation_name": "support_v1_ingest_modality_comparison",
            "generated_at": datetime.now().astimezone().isoformat(),
            "runner_path": project_relative_path(Path(__file__).resolve()),
            "export_path": project_relative_path(EXPORT_PATH),
            "markdown_export_path": project_relative_path(MARKDOWN_EXPORT_PATH),
            "run_command_powershell": RUN_COMMAND,
            "modalities": [result["modality"] for result in modality_results],
            "calibration": {
                "name": CALIBRATION_NAME,
                "version": CALIBRATION_VERSION,
                "settings": asdict(WINNING_SETTINGS),
            },
        },
        "top_level_summary": top_level_summary,
        "modalities": {
            modality_result["modality"]: {
                "display_name": modality_result["display_name"],
                "largest_slice_name": modality_result["largest_slice_name"],
                "slice_names": modality_result["slice_names"],
                "slices": {
                    slice_result["slice_name"]: {
                        key: value
                        for key, value in slice_result.items()
                        if key not in {"modality", "modality_display_name", "slice_name"}
                    }
                    for slice_result in modality_result["slices"]
                },
            }
            for modality_result in modality_results
        },
        "summary_rows": build_summary_rows(modality_results),
    }


def build_markdown_report(
    modality_results: Sequence[dict[str, Any]],
    top_level_summary: dict[str, Any],
) -> str:
    lines = [
        "# Support V1 Ingest Modality Comparison",
        "",
        "## Run Command",
        "",
        f"```powershell\n{RUN_COMMAND}\n```",
        "",
        "## What This Adds",
        "",
        f"- {top_level_summary['what_this_adds']}",
        "",
        "## Summary Table",
        "",
        "| modality | slice | label count | iml | calibrated_iml | naive_summary | full_history |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in build_summary_rows(modality_results):
        lines.append(
            (
                f"| {row['modality']} | {row['slice']} | {row['label_count']} | "
                f"{format_percent(float(row['iml_accuracy']))} | "
                f"{format_percent(float(row['calibrated_iml_accuracy']))} | "
                f"{format_percent(float(row['naive_summary_accuracy']))} | "
                f"{format_percent(float(row['full_history_accuracy']))} |"
            )
        )

    calibrated_vs_iml = top_level_summary["calibrated_iml_vs_default_iml_across_modalities"]
    largest_slice_summary = top_level_summary[
        "calibrated_iml_vs_baselines_on_largest_slice_per_modality"
    ]
    strongest_evidence = top_level_summary["strongest_evidence_modality"]
    needs_more_data = top_level_summary["modality_needing_more_data"]

    lines.extend(
        [
            "",
            "## Aggregate Conclusion",
            "",
            (
                "- Calibrated IML vs default IML: "
                f"{calibrated_vs_iml['overall']} "
                f"({calibrated_vs_iml['improved_slice_count']} improved, "
                f"{calibrated_vs_iml['tied_slice_count']} tied, "
                f"{calibrated_vs_iml['total_slice_count']} total slices)."
            ),
            (
                "- Calibrated IML beats both baselines on the largest slice in each modality: "
                f"{'yes' if largest_slice_summary['all_modalities'] else 'no'} "
                f"({largest_slice_summary['beats_both_count']} of "
                f"{largest_slice_summary['total_modalities']} modalities)."
            ),
            (
                "- Strongest evidence modality: "
                f"`{strongest_evidence['modality']}` on `{strongest_evidence['largest_slice']}` "
                f"with a {format_delta(float(strongest_evidence['margin_vs_best_non_calibrated']))} "
                "lead over the best non-calibrated method."
            ),
            (
                "- Modality needing more data: "
                f"`{needs_more_data['modality']}` on `{needs_more_data['largest_slice']}` "
                f"because the largest slice is only {needs_more_data['label_count']} labels "
                "and carries the weakest evidence among the smallest-sample modalities."
            ),
            f"- Overall: {top_level_summary['overall_conclusion']}",
            "",
        ]
    )
    return "\n".join(lines)


def export_json_results(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_export_path = EXPORT_PATH.with_name(f"{EXPORT_PATH.stem}.{uuid4().hex}.tmp")
    with temp_export_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_export_path.replace(EXPORT_PATH)
    return EXPORT_PATH


def export_markdown_report(markdown_report: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_export_path = MARKDOWN_EXPORT_PATH.with_name(
        f"{MARKDOWN_EXPORT_PATH.stem}.{uuid4().hex}.tmp"
    )
    with temp_export_path.open("w", encoding="utf-8") as handle:
        handle.write(markdown_report)
        if not markdown_report.endswith("\n"):
            handle.write("\n")
    temp_export_path.replace(MARKDOWN_EXPORT_PATH)
    return MARKDOWN_EXPORT_PATH


def print_summary_table(
    modality_results: Sequence[dict[str, Any]],
    *,
    json_artifact_path: Path,
    markdown_artifact_path: Path,
) -> None:
    headers = (
        "modality",
        "slice",
        "label_count",
        "iml",
        "calibrated_iml",
        "naive_summary",
        "full_history",
    )
    rows = [
        (
            slice_result["modality"],
            slice_result["slice_name"],
            str(slice_result["total_labels"]),
            format_percent(float(slice_result["accuracies"]["iml"])),
            format_percent(float(slice_result["accuracies"]["calibrated_iml"])),
            format_percent(float(slice_result["accuracies"]["naive_summary"])),
            format_percent(float(slice_result["accuracies"]["full_history"])),
        )
        for modality_result in modality_results
        for slice_result in modality_result["slices"]
    ]
    widths = [
        max(len(header), max(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]

    def format_row(values: Sequence[str]) -> str:
        return " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(values)
        )

    print("support_v1 ingest modality comparison")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))
    print(f"json_artifact: {project_relative_path(json_artifact_path)}")
    print(f"markdown_artifact: {project_relative_path(markdown_artifact_path)}")


def main() -> None:
    modality_results = build_modality_results()
    export_payload = build_export_payload(modality_results)
    markdown_report = build_markdown_report(
        modality_results,
        export_payload["top_level_summary"],
    )
    json_artifact_path = export_json_results(export_payload)
    markdown_artifact_path = export_markdown_report(markdown_report)
    print_summary_table(
        modality_results,
        json_artifact_path=json_artifact_path,
        markdown_artifact_path=markdown_artifact_path,
    )


if __name__ == "__main__":
    main()
