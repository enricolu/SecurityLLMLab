"""Downloader for the LogHub dataset collection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, List
import requests
from tqdm import tqdm

from .base import DatasetArtifact, SecurityDataset

LOGHUB_INDEX_URL = "https://raw.githubusercontent.com/logpai/loghub/master/loghub.json"


class LogHubDataset(SecurityDataset):
    """Download datasets listed in the LogHub repository."""

    def __init__(self, datasets: List[str] | None = None) -> None:
        self.datasets = datasets

    def _load_index(self) -> List[dict]:
        response = requests.get(LOGHUB_INDEX_URL, timeout=60)
        response.raise_for_status()
        return json.loads(response.text)

    def prepare(self, destination: Path) -> Iterator[DatasetArtifact]:
        destination.mkdir(parents=True, exist_ok=True)
        index = self._load_index()
        selected = {name for name in self.datasets} if self.datasets else None

        for entry in index:
            dataset_name = entry["dataset"].strip()
            if selected and dataset_name not in selected:
                continue

            url = entry["link"].strip()
            if not url:
                continue

            file_name = url.split("/")[-1]
            target = destination / dataset_name / file_name
            if target.exists():
                yield DatasetArtifact(name=dataset_name, path=target, description="Existing download")
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(url, stream=True, timeout=120) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", 0))
                with target.open("wb") as handle:
                    progress = tqdm(total=total, unit="B", unit_scale=True, desc=f"LogHub:{dataset_name}")
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
                            progress.update(len(chunk))
                    progress.close()

            yield DatasetArtifact(name=dataset_name, path=target, description=entry.get("abstract", ""))

    def describe_sources(self) -> Iterator[str]:
        yield "https://github.com/logpai/loghub"


__all__ = ["LogHubDataset"]
