from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.io_utils import atomic_write_json, atomic_write_text


def write_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    return atomic_write_json(path, manifest)


def write_report(path: Path, content: str) -> Path:
    return atomic_write_text(path, content)
