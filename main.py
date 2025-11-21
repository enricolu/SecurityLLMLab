"""Command line entry point for Security LLM Lab."""

from __future__ import annotations

import argparse
from pathlib import Path

from security_llm_lab import AppConfig, DataPipeline, TrainingPipeline
from security_llm_lab.logging_utils import configure_logging
from security_llm_lab.agent.core import SecurityAgent
from security_llm_lab.rules.generator import RuleGenerator


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

    rule_parser = subparsers.add_parser("generate-rule", help="Generate a security rule")
    rule_parser.add_argument("--workspace", type=Path, required=True)
    rule_parser.add_argument("--type", choices=["sigma", "splunk"], required=True, help="Type of rule to generate")
    rule_parser.add_argument("--description", type=str, required=True, help="Description of the rule")

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
    
    print(f"Initializing Security Agent with backend: {config.llm.backend}")
    agent = SecurityAgent(config)
    
    print(f"Question: {question}")
    response = agent.run(question)
    print(f"Answer: {response}")


def cmd_generate_rule(workspace: Path, rule_type: str, description: str) -> None:
    config_path = workspace / "config.yaml"
    config = AppConfig.load(config_path)
    
    generator = RuleGenerator(config)
    
    print(f"Generating {rule_type} rule for: {description}")
    if rule_type == "sigma":
        result = generator.generate_sigma(description)
    elif rule_type == "splunk":
        result = generator.generate_splunk(description)
    else:
        raise ValueError(f"Unknown rule type: {rule_type}")
        
    print("\nGenerated Rule:\n")
    print(result)


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
    elif args.command == "generate-rule":
        cmd_generate_rule(args.workspace, args.type, args.description)
    else:
        raise ValueError(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()
