"""Orchestrate ingestion of local and remote datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, List

from ..collectors.local_collector import LocalCollector, LocalCollectorConfig
from ..config import AppConfig, LocalSourceConfig, RemoteSourceConfig
from ..datasets import AwesomeCyberDatasetCatalog, CyberInstructDataset, LogHubDataset
from ..datasets.base import SecurityDataset
from ..integrations import UTMStackClient
from ..logging_utils import configure_logging
from ..utils.files import ensure_jsonl


class DataPipeline:
    """Coordinate the collection of telemetry and curation of datasets."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = configure_logging(name=self.__class__.__name__)

    def run(self) -> List[Path]:
        self.logger.info("Starting data pipeline")
        artifacts: List[Path] = []
        artifacts.extend(self._collect_local_sources(self.config.local_sources))
        artifacts.extend(self._collect_remote_sources(self.config.remote_sources))
        self.logger.info("Data pipeline completed with %d artifacts", len(artifacts))
        return artifacts

    def _collect_local_sources(self, sources: Iterable[LocalSourceConfig]) -> List[Path]:
        results: List[Path] = []
        for source in sources:
            collector = LocalCollector(LocalCollectorConfig(path=source.path, glob=source.glob, metadata=source.metadata))
            output = collector.collect(self.config.data_lake_dir)
            results.append(output)
            if self.config.siem:
                self._forward_to_siem(output)
        return results

    def _collect_remote_sources(self, sources: Iterable[RemoteSourceConfig]) -> List[Path]:
        datasets: List[SecurityDataset] = [LogHubDataset(), CyberInstructDataset(), AwesomeCyberDatasetCatalog()]
        results: List[Path] = []

        for dataset in datasets:
            destination = self.config.data_lake_dir / dataset.__class__.__name__
            for artifact in dataset.prepare(destination):
                self.logger.info("Prepared dataset %s at %s", artifact.name, artifact.path)
                ensured = ensure_jsonl(artifact.path)
                if ensured:
                    results.append(ensured)
                    if self.config.siem and ensured.suffix == ".jsonl":
                        self._forward_to_siem(ensured)

        for source in sources:
            if not source.enabled:
                continue
            file_path = self._download_remote_source(source)
            ensured = ensure_jsonl(file_path)
            if ensured:
                results.append(ensured)
                if self.config.siem and ensured.suffix == ".jsonl":
                    self._forward_to_siem(ensured)

        return results

    def _download_remote_source(self, source: RemoteSourceConfig) -> Path:
        import requests
        from tqdm import tqdm

        destination = source.destination or Path(source.url.split("/")[-1])
        target = self.config.data_lake_dir / "remote_sources" / source.name / destination
        if target.exists():
            self.logger.info("Remote source %s already downloaded", source.name)
            return target

        target.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(source.url, stream=True, timeout=120) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            with target.open("wb") as handle:
                progress = tqdm(total=total, unit="B", unit_scale=True, desc=f"Remote:{source.name}")
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                        progress.update(len(chunk))
                progress.close()
        return target

    def _forward_to_siem(self, jsonl_path: Path) -> None:
        if not self.config.siem:
            return
        client = UTMStackClient(
            base_url=self.config.siem.base_url,
            api_key=self.config.siem.api_key,
            verify_ssl=self.config.siem.verify_ssl,
            default_index=self.config.siem.default_index,
        )
        client.test_connection()
        events = self._load_jsonl(jsonl_path)
        client.send_events(events)

    def _load_jsonl(self, path: Path) -> Iterator[dict]:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


__all__ = ["DataPipeline"]
