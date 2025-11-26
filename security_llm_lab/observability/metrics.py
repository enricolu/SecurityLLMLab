"""Prometheus metrics helpers for Security LLM Lab pipelines."""

from __future__ import annotations

import os
from typing import Optional

try:  # pragma: no cover - prefer real prometheus client when available
    from prometheus_client import CollectorRegistry, Counter, Gauge, Summary, start_http_server
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback for offline environments
    class CollectorRegistry:
        def __init__(self) -> None:
            self.metrics: dict[str, object] = {}

        def register(self, name: str, metric: object) -> None:
            self.metrics[name] = metric

        def get_sample_value(self, name: str) -> float | None:
            base_name = name.replace("_sum", "").replace("_count", "")
            metric = self.metrics.get(name) or self.metrics.get(base_name)
            if metric and hasattr(metric, "sample_value"):
                return metric.sample_value(name)
            return None

    class _BaseMetric:
        def __init__(self, name: str, registry: CollectorRegistry | None) -> None:
            self.name = name
            if registry is not None:
                registry.register(name, self)

    class Counter(_BaseMetric):
        def __init__(self, name: str, documentation: str, registry: CollectorRegistry | None = None) -> None:
            super().__init__(name, registry)
            self.value = 0.0

        def inc(self, amount: float = 1.0) -> None:
            self.value += amount

        def sample_value(self, name: str) -> float:
            return self.value

    class Gauge(_BaseMetric):
        def __init__(self, name: str, documentation: str, registry: CollectorRegistry | None = None) -> None:
            super().__init__(name, registry)
            self.value = 0.0

        def set(self, value: float) -> None:
            self.value = value

        def sample_value(self, name: str) -> float:
            return self.value

    class Summary(_BaseMetric):
        def __init__(self, name: str, documentation: str, registry: CollectorRegistry | None = None) -> None:
            super().__init__(name, registry)
            self._count = 0.0
            self._sum = 0.0

        def observe(self, value: float) -> None:
            self._count += 1
            self._sum += value

        def sample_value(self, name: str) -> float:
            if name.endswith("_sum"):
                return self._sum
            if name.endswith("_count"):
                return self._count
            return self._sum

    def start_http_server(port: int, registry: CollectorRegistry | None = None) -> None:
        return None

DEFAULT_METRICS_PORT = 9000


class MetricsEmitter:
    """Expose lightweight metrics for pipeline execution."""

    def __init__(self, enabled: bool = True, registry: Optional[CollectorRegistry] = None) -> None:
        self.enabled = enabled
        self.registry = registry
        if not enabled:
            self.pipeline_runs: Optional[Counter] = None
            self.pipeline_duration: Optional[Summary] = None
            self.last_artifact_count: Optional[Gauge] = None
            return

        self.pipeline_runs = Counter(
            "security_llm_lab_pipeline_runs_total",
            "Number of data pipeline executions.",
            registry=registry,
        )
        self.pipeline_duration = Summary(
            "security_llm_lab_pipeline_duration_seconds",
            "Pipeline runtime in seconds.",
            registry=registry,
        )
        self.last_artifact_count = Gauge(
            "security_llm_lab_last_artifact_count",
            "Number of artifacts produced by the most recent pipeline run.",
            registry=registry,
        )

    def start_server(self, port: int = DEFAULT_METRICS_PORT) -> None:
        """Start an HTTP server for Prometheus scraping."""

        if not self.enabled:
            return
        start_http_server(port, registry=self.registry)

    def record_pipeline_run(self, artifact_count: int, duration_seconds: float) -> None:
        """Record metrics for a pipeline run."""

        if not self.enabled:
            return
        self.pipeline_runs.inc()
        self.pipeline_duration.observe(duration_seconds)
        self.last_artifact_count.set(artifact_count)


def metrics_from_env() -> MetricsEmitter:
    """Create a metrics emitter using environment toggles."""

    enabled = os.getenv("ENABLE_PIPELINE_METRICS", "0") == "1"
    port = int(os.getenv("METRICS_PORT", str(DEFAULT_METRICS_PORT)))
    emitter = MetricsEmitter(enabled=enabled)
    if enabled:
        emitter.start_server(port)
    return emitter


__all__ = [
    "MetricsEmitter",
    "metrics_from_env",
    "CollectorRegistry",
    "DEFAULT_METRICS_PORT",
]
