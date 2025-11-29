"""Ingestion API for accepting telemetry from local agents."""

from .server import IngestApiConfig, run_ingest_api_server

__all__ = ["IngestApiConfig", "run_ingest_api_server"]
