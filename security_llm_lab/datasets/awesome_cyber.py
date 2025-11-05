"""Reference catalog pointing to Awesome Cybersecurity Datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .base import DatasetArtifact, SecurityDataset


@dataclass(slots=True)
class AwesomeDatasetEntry:
    name: str
    url: str
    description: str


AWESOME_DATASETS: List[AwesomeDatasetEntry] = [
    AwesomeDatasetEntry(
        name="AI-enhanced-SIEM",
        url="https://github.com/M-Mowina/AI-enhanced-SIEM-solution-with-LLMs",
        description="Reference implementation for augmenting SIEM with LLMs.",
    ),
    AwesomeDatasetEntry(
        name="LLM-as-a-SOAR-Tool",
        url="https://github.com/SuhasAC123/LLM-as-a-SOAR-Tool",
        description="Automation playbooks leveraging LLMs for SOAR orchestration.",
    ),
]


class AwesomeCyberDatasetCatalog(SecurityDataset):
    """Expose the Awesome Cybersecurity Datasets list as artifacts."""

    def prepare(self, destination: Path):
        destination.mkdir(parents=True, exist_ok=True)
        for entry in AWESOME_DATASETS:
            metadata_path = destination / f"{entry.name}.url"
            metadata_path.write_text(entry.url, encoding="utf-8")
            yield DatasetArtifact(name=entry.name, path=metadata_path, description=entry.description)

    def describe_sources(self) -> Iterable[str]:
        yield "https://github.com/shramos/Awesome-Cybersecurity-Datasets"


__all__ = ["AwesomeCyberDatasetCatalog", "AwesomeDatasetEntry", "AWESOME_DATASETS"]
