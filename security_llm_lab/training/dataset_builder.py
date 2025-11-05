"""Utilities to assemble datasets for model fine-tuning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, List, Mapping

from ..logging_utils import configure_logging


class DatasetBuilder:
    """Merge JSONL artifacts into a Hugging Face dataset format."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.logger = configure_logging(name=self.__class__.__name__)

    def build_dataset(self, artifacts: Iterable[Path], dataset_name: str) -> str:
        from datasets import Dataset, DatasetDict

        rows: List[Mapping[str, object]] = []
        for artifact in artifacts:
            rows.extend(self._load_jsonl(artifact))
        if not rows:
            raise ValueError("No rows available to build dataset")

        dataset = Dataset.from_list(list(rows))
        dataset_dict = DatasetDict({"train": dataset})
        dataset_dir = self.workspace / dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        dataset_dict.save_to_disk(str(dataset_dir))
        self.logger.info("Saved dataset to %s", dataset_dir)
        return str(dataset_dir)

    def _load_jsonl(self, path: Path) -> Iterator[Mapping[str, object]]:
        self.logger.debug("Loading %s", path)
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


__all__ = ["DatasetBuilder"]
