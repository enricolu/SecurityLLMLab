"""Command line entry point for Security LLM Lab."""

from __future__ import annotations

import argparse
from pathlib import Path

from security_llm_lab import AppConfig, DataPipeline, TrainingPipeline
from security_llm_lab.logging_utils import configure_logging
from security_llm_lab.rag import RagRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Security LLM Lab orchestration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a default configuration file")
    init_parser.add_argument("--workspace", type=Path, required=True, help="Workspace directory")

    collect_parser = subparsers.add_parser("collect", help="Run data collection pipeline")
    collect_parser.add_argument("--config", type=Path, required=True, help="Path to configuration YAML")

    train_parser = subparsers.add_parser("train", help="Run training pipeline")
    train_parser.add_argument("--config", type=Path, required=True)

    rag_parser = subparsers.add_parser("rag-query", help="Query the RAG index")
    rag_parser.add_argument("--workspace", type=Path, required=True)
    rag_parser.add_argument("--question", type=str, required=True)

    return parser.parse_args()


def cmd_init(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    config_path = workspace / "config.yaml"
    if config_path.exists():
        raise FileExistsError(f"{config_path} already exists")

    config = AppConfig(
        workspace=workspace,
        local_sources=[],
        remote_sources=[],
        siem=None,
        soar=None,
    )
    config.ensure_directories()
    config.dump(config_path)
    print(f"Created configuration at {config_path}")


def cmd_collect(config_path: Path) -> None:
    config = AppConfig.load(config_path)
    pipeline = DataPipeline(config)
    artifacts = pipeline.run()
    print("Artifacts:", ", ".join(str(path) for path in artifacts))


def cmd_train(config_path: Path) -> None:
    config = AppConfig.load(config_path)
    pipeline = DataPipeline(config)
    artifacts = pipeline.run()
    training = TrainingPipeline(config)
    training.run(artifacts)


def cmd_rag_query(workspace: Path, question: str) -> None:
    config_path = workspace / "config.yaml"
    config = AppConfig.load(config_path)
    index_path = config.rag_dir / config.rag.index_name / "index.joblib"
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found at {index_path}")
    retriever = RagRetriever(index_path)
    results = retriever.query(question, top_k=config.rag.top_k)
    for item in results:
        print(f"Score: {item['score']:.3f} | Source: {item.get('source_file', 'N/A')} | Text: {item.get('raw') or item.get('response')}")


def main() -> None:
    args = parse_args()
    configure_logging()
    if args.command == "init":
        cmd_init(args.workspace)
    elif args.command == "collect":
        cmd_collect(args.config)
    elif args.command == "train":
        cmd_train(args.config)
    elif args.command == "rag-query":
        cmd_rag_query(args.workspace, args.question)
    else:
        raise ValueError(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
