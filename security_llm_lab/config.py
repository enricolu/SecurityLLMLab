"""Application configuration models and helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

import yaml


@dataclass(slots=True)
class LocalSourceConfig:
    """Configuration for collecting local telemetry files."""

    path: Path
    glob: str = "**/*.log"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_mapping(data: Dict[str, Any]) -> "LocalSourceConfig":
        return LocalSourceConfig(
            path=Path(data["path"]),
            glob=data.get("glob", "**/*.log"),
            metadata=data.get("metadata", {}),
        )


@dataclass(slots=True)
class RemoteSourceConfig:
    """Configuration for remote dataset repositories."""

    name: str
    url: str
    enabled: bool = True
    destination: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_mapping(data: Dict[str, Any]) -> "RemoteSourceConfig":
        return RemoteSourceConfig(
            name=data["name"],
            url=data["url"],
            enabled=data.get("enabled", True),
            destination=Path(data["destination"]) if data.get("destination") else None,
            metadata=data.get("metadata", {}),
        )


@dataclass(slots=True)
class SIEMConfig:
    base_url: str
    api_key: str
    verify_ssl: bool = True
    default_index: str = "security-events"

    @staticmethod
    def from_mapping(data: Dict[str, Any]) -> "SIEMConfig":
        api_key = os.getenv("SIEM_API_KEY", data.get("api_key"))
        if not api_key:
            raise ValueError("SIEM API key must be provided")
        return SIEMConfig(
            base_url=data["base_url"],
            api_key=api_key,
            verify_ssl=data.get("verify_ssl", True),
            default_index=data.get("default_index", "security-events"),
        )


@dataclass(slots=True)
class SOARConfig:
    base_url: str
    api_key: str
    verify_ssl: bool = True

    @staticmethod
    def from_mapping(data: Dict[str, Any]) -> "SOARConfig":
        api_key = os.getenv("SOAR_API_KEY", data.get("api_key"))
        if not api_key:
            raise ValueError("SOAR API key must be provided")
        return SOARConfig(
            base_url=data["base_url"],
            api_key=api_key,
            verify_ssl=data.get("verify_ssl", True),
        )


@dataclass(slots=True)
class RAGConfig:
    index_name: str = "security-rag"
    top_k: int = 5


@dataclass(slots=True)
class TrainingConfig:
    model_name: str
    dataset_name: Optional[str] = None
    output_dir: Path = Path("./models")
    max_steps: Optional[int] = None
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 1
    learning_rate: float = 5e-5
    warmup_steps: int = 0
    save_steps: int = 100
    logging_steps: int = 10



@dataclass(slots=True)
class LLMConfig:
    backend: str = "huggingface"
    model_name: str = "mistralai/Mistral-7B-Instruct"
    base_url: Optional[str] = None


@dataclass(slots=True)
class AgentConfig:
    max_iterations: int = 5
    tools: List[str] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    """Top level application configuration."""

    workspace: Path
    local_sources: List[LocalSourceConfig] = field(default_factory=list)
    remote_sources: List[RemoteSourceConfig] = field(default_factory=list)
    siem: Optional[SIEMConfig] = None
    soar: Optional[SOARConfig] = None
    rag: RAGConfig = field(default_factory=RAGConfig)
    training: Optional[TrainingConfig] = None
    llm: LLMConfig = field(default_factory=LLMConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @property
    def data_lake_dir(self) -> Path:
        """Return the path to the curated data lake directory."""

        return self.workspace / "data_lake"

    @property
    def models_dir(self) -> Path:
        return self.workspace / "models"

    @property
    def rag_dir(self) -> Path:
        return self.workspace / "rag"

    def ensure_directories(self) -> None:
        """Create directories required for the workflow."""

        for path in [self.workspace, self.data_lake_dir, self.models_dir, self.rag_dir]:
            path.mkdir(parents=True, exist_ok=True)

    def to_mapping(self) -> Dict[str, Any]:
        """Serialize the config back to a Python mapping."""

        def serialize_list(items: Iterable[Any]) -> List[Any]:
            result: List[Any] = []
            for item in items:
                if hasattr(item, "__dict__"):
                    result.append({k: v for k, v in item.__dict__.items() if not k.startswith("_")})
                else:
                    result.append(item)
            return result

        data: Dict[str, Any] = {
            "workspace": str(self.workspace),
            "local_sources": serialize_list(self.local_sources),
            "remote_sources": serialize_list(self.remote_sources),
            "rag": self.rag.__dict__,
        }
        if self.siem:
            data["siem"] = self.siem.__dict__
        if self.soar:
            data["soar"] = self.soar.__dict__
        if self.training:
            training = self.training.__dict__.copy()
            training["output_dir"] = str(self.training.output_dir)
            data["training"] = training
        data["llm"] = self.llm.__dict__
        data["agent"] = self.agent.__dict__
        return data

    def dump(self, path: Path) -> None:
        """Persist the configuration to disk."""

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(self.to_mapping(), handle, allow_unicode=True)

    @staticmethod
    def from_mapping(data: Dict[str, Any]) -> "AppConfig":
        local_sources = [LocalSourceConfig.from_mapping(item) for item in data.get("local_sources", [])]
        remote_sources = [RemoteSourceConfig.from_mapping(item) for item in data.get("remote_sources", [])]

        siem = None
        if "siem" in data and data["siem"]:
            siem = SIEMConfig.from_mapping(data["siem"])

        soar = None
        if "soar" in data and data["soar"]:
            soar = SOARConfig.from_mapping(data["soar"])

        rag_map = data.get("rag", {})
        rag = RAGConfig(
            index_name=rag_map.get("index_name", "security-rag"),
            top_k=rag_map.get("top_k", 5),
        )

        training = None
        if "training" in data and data["training"]:
            train_map = data["training"]
            training = TrainingConfig(
                model_name=train_map["model_name"],
                dataset_name=train_map.get("dataset_name"),
                output_dir=Path(train_map.get("output_dir", "./models")),
                max_steps=train_map.get("max_steps"),
                per_device_train_batch_size=train_map.get("per_device_train_batch_size", 1),
                gradient_accumulation_steps=train_map.get("gradient_accumulation_steps", 1),
                learning_rate=train_map.get("learning_rate", 5e-5),
                warmup_steps=train_map.get("warmup_steps", 0),
                save_steps=train_map.get("save_steps", 100),
                logging_steps=train_map.get("logging_steps", 10),

            )

        llm_map = data.get("llm", {})
        llm = LLMConfig(
            backend=llm_map.get("backend", "huggingface"),
            model_name=llm_map.get("model_name", "mistralai/Mistral-7B-Instruct"),
            base_url=llm_map.get("base_url"),
        )

        agent_map = data.get("agent", {})
        agent = AgentConfig(
            max_iterations=agent_map.get("max_iterations", 5),
            tools=agent_map.get("tools", []),
        )

        return AppConfig(
            workspace=Path(data["workspace"]).expanduser(),
            local_sources=local_sources,
            remote_sources=remote_sources,
            siem=siem,
            soar=soar,
            rag=rag,
            training=training,
            llm=llm,
            agent=agent,
        )

    @staticmethod
    def load(path: Path) -> "AppConfig":
        """Load configuration from YAML file."""

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        config = AppConfig.from_mapping(data)
        config.ensure_directories()
        return config

    def validate(self) -> None:
        """Validate configuration values and raise ValueError on invalid input."""

        if self.siem:
            parsed = urlparse(self.siem.base_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("Invalid SIEM base_url")

        if self.training:
            if self.training.per_device_train_batch_size <= 0:
                raise ValueError("per_device_train_batch_size must be positive")
            if self.training.learning_rate <= 0:
                raise ValueError("learning_rate must be positive")

        for source in self.local_sources:
            if not source.path.exists():
                raise ValueError(f"Local source path does not exist: {source.path}")


__all__ = [
    "AppConfig",
    "LocalSourceConfig",
    "RemoteSourceConfig",
    "SIEMConfig",
    "SOARConfig",
    "RAGConfig",
    "TrainingConfig",
    "LLMConfig",
    "AgentConfig",
]
