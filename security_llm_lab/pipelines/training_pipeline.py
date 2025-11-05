"""Training pipeline combining dataset building, fine-tuning, and RAG indexing."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..config import AppConfig
from ..logging_utils import configure_logging
from ..rag import TfidfIndexer
from ..training import DatasetBuilder, FineTuner


class TrainingPipeline:
    def __init__(self, config: AppConfig) -> None:
        if not config.training:
            raise ValueError("Training configuration is required")
        self.config = config
        self.logger = configure_logging(name=self.__class__.__name__)
        self.dataset_builder = DatasetBuilder(config.workspace / "datasets")
        self.fine_tuner = FineTuner(config.training)
        self.indexer = TfidfIndexer(config.rag_dir, config.rag.index_name)

    def run(self, artifacts: Iterable[Path]) -> None:
        artifacts = list(artifacts)
        if not artifacts:
            raise ValueError("No artifacts provided for training")

        dataset_path = self.dataset_builder.build_dataset(artifacts, self.config.training.dataset_name or "security_corpus")
        self.fine_tuner.run(dataset_path)
        self.indexer.build(artifacts)
        self.logger.info("Training pipeline finished")


__all__ = ["TrainingPipeline"]
