"""TF-IDF based indexer for security knowledge base."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from ..logging_utils import configure_logging


class TfidfIndexer:
    """Create a TF-IDF index over JSONL knowledge artifacts."""

    def __init__(self, workspace: Path, index_name: str) -> None:
        self.workspace = workspace
        self.index_name = index_name
        self.logger = configure_logging(name=self.__class__.__name__)

    def build(self, artifacts: Iterable[Path]) -> Path:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import joblib

        documents: List[str] = []
        metadata: List[dict] = []
        for artifact in artifacts:
            with artifact.open("r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = record.get("raw") or record.get("response") or record.get("instruction")
                    if not text:
                        continue
                    documents.append(str(text))
                    metadata.append(record)
        if not documents:
            raise ValueError("No documents found for indexing")

        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(documents)

        index_dir = self.workspace / self.index_name
        index_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump({"vectorizer": vectorizer, "matrix": matrix, "metadata": metadata}, index_dir / "index.joblib")
        self.logger.info("Saved TF-IDF index with %d documents", len(documents))
        return index_dir / "index.joblib"


__all__ = ["TfidfIndexer"]
