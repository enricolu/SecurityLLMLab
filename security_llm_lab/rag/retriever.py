"""Retriever for TF-IDF index."""

from __future__ import annotations

from pathlib import Path
from typing import List

import joblib
from sklearn.metrics.pairwise import cosine_similarity

from ..logging_utils import configure_logging


class RagRetriever:
    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path
        self.logger = configure_logging(name=self.__class__.__name__)
        self.store = joblib.load(index_path)

    def query(self, question: str, top_k: int = 5) -> List[dict]:
        vectorizer = self.store["vectorizer"]
        matrix = self.store["matrix"]
        metadata = self.store["metadata"]
        query_vec = vectorizer.transform([question])
        scores = cosine_similarity(query_vec, matrix)[0]
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        results: List[dict] = []
        for idx, score in ranked:
            item = metadata[idx].copy()
            item["score"] = float(score)
            results.append(item)
        return results


__all__ = ["RagRetriever"]
