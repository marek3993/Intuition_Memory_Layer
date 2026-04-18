from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Sequence

from evaluate_support_labels import (
    LabelEvaluationResult,
    format_percent,
    load_support_labels,
    validate_label,
)
from use_cases.support_v1.shared.io_utils import atomic_write_json


def resolve_output_path(path: Path | None, default_path: Path) -> Path:
    return (default_path if path is None else path).expanduser().resolve()


def export_json_results(output_path: Path, payload: dict[str, Any]) -> Path:
    return atomic_write_json(output_path, payload)


def load_and_validate_label_set(
    labels_path: Path,
    cases_by_ticket_id: dict[str, Any],
    entity_events: dict[str, list[Any]],
    *,
    format_dataset_path: Callable[[Path], str],
) -> list[Any]:
    try:
        labels = load_support_labels(labels_path)
        for label in labels:
            validate_label(label, cases_by_ticket_id, entity_events)
        return labels
    except ValueError as exc:
        raise ValueError(
            "Label set does not align with the normalized raw export. "
            f"labels_path={format_dataset_path(labels_path)}. "
            f"Validation error: {exc}"
        ) from exc


def summarize_correctness(results: Sequence[LabelEvaluationResult]) -> str:
    correct_predictions = sum(1 for result in results if result.correct)
    incorrect_predictions = len(results) - correct_predictions
    accuracy = correct_predictions / len(results) if results else 0.0
    return " | ".join(
        [
            f"total_labels={len(results)}",
            f"correct={correct_predictions}",
            f"incorrect={incorrect_predictions}",
            f"accuracy={format_percent(accuracy)}",
        ]
    )
