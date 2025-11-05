"""Local telemetry collector supporting configurable glob patterns."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

from ..logging_utils import configure_logging


@dataclass(slots=True)
class LocalCollectorConfig:
    path: Path
    glob: str = "**/*.log"
    metadata: Dict[str, str] | None = None


class LocalCollector:
    """Collect files from local directories and normalize them into JSON lines."""

    def __init__(self, config: LocalCollectorConfig) -> None:
        self.config = config
        self.logger = configure_logging(name=self.__class__.__name__)

    def collect(self, destination: Path) -> Path:
        """Collect matching files and return the path to the consolidated JSONL file."""

        destination.mkdir(parents=True, exist_ok=True)
        output = destination / f"local_{self._fingerprint()}.jsonl"
        self.logger.info("Collecting telemetry from %s", self.config.path)

        with output.open("w", encoding="utf-8") as handle:
            for file_path in self._iter_files():
                with file_path.open("r", encoding="utf-8", errors="ignore") as source:
                    for line in source:
                        record = self._normalize_record(line.strip(), file_path)
                        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return output

    def _iter_files(self) -> Iterable[Path]:
        yield from self.config.path.glob(self.config.glob)

    def _fingerprint(self) -> str:
        data = f"{self.config.path}:{self.config.glob}:{self.config.metadata}".encode()
        return hashlib.md5(data, usedforsecurity=False).hexdigest()  # noqa: S324

    def _normalize_record(self, line: str, source: Path) -> Dict[str, object]:
        metadata = self.config.metadata or {}
        return {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
            "raw": line,
            "source_file": str(source),
            "collector": "local",
            "metadata": metadata,
        }


__all__ = ["LocalCollector", "LocalCollectorConfig"]
