"""File helpers for working with different dataset formats."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from ..logging_utils import configure_logging

logger = configure_logging(name=__name__)


def ensure_jsonl(path: Path) -> Optional[Path]:
    """Convert known formats (CSV/JSON) to JSONL if necessary."""

    if path.suffix == ".jsonl":
        return path
    if path.suffix == ".json":
        return _json_to_jsonl(path)
    if path.suffix == ".csv":
        return _csv_to_jsonl(path)
    logger.debug("Skipping conversion for %s", path)
    return None


def _json_to_jsonl(path: Path) -> Path:
    target = path.with_suffix(".jsonl")
    with path.open("r", encoding="utf-8") as src, target.open("w", encoding="utf-8") as dst:
        data = json.load(src)
        if isinstance(data, list):
            for item in data:
                dst.write(json.dumps(item, ensure_ascii=False) + "\n")
        elif isinstance(data, dict):
            dst.write(json.dumps(data, ensure_ascii=False) + "\n")
        else:
            raise ValueError("Unsupported JSON structure for conversion")
    return target


def _csv_to_jsonl(path: Path) -> Path:
    target = path.with_suffix(".jsonl")
    with path.open("r", encoding="utf-8") as src, target.open("w", encoding="utf-8") as dst:
        reader = csv.DictReader(src)
        for row in reader:
            dst.write(json.dumps(row, ensure_ascii=False) + "\n")
    return target


__all__ = ["ensure_jsonl"]
