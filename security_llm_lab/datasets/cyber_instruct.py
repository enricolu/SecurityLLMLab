"""Loader for the CyberLLMInstruct dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import requests
from tqdm import tqdm

from .base import DatasetArtifact, SecurityDataset

CYBER_INSTRUCT_URL = "https://raw.githubusercontent.com/Adelsamir01/CyberLLMInstruct/main/data/security_instruct.json"


class CyberInstructDataset(SecurityDataset):
    """Download the CyberLLMInstruct instruction-response dataset."""

    def prepare(self, destination: Path) -> Iterator[DatasetArtifact]:
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / "cyber_instruct.json"
        if target.exists():
            yield DatasetArtifact(name="CyberLLMInstruct", path=target, description="Existing download")
            return

        with requests.get(CYBER_INSTRUCT_URL, stream=True, timeout=120) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            with target.open("wb") as handle:
                progress = tqdm(total=total, unit="B", unit_scale=True, desc="CyberLLMInstruct")
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                        progress.update(len(chunk))
                progress.close()

        yield DatasetArtifact(name="CyberLLMInstruct", path=target, description="Instruction dataset")

    def describe_sources(self) -> Iterator[str]:
        yield "https://github.com/Adelsamir01/CyberLLMInstruct"


__all__ = ["CyberInstructDataset"]
