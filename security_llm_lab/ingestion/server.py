"""Lightweight HTTP server to accept telemetry from local agents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable, List, Mapping

from ..logging_utils import configure_logging


@dataclass(slots=True)
class IngestApiConfig:
    """Runtime settings for the ingestion API server."""

    workspace: Path
    host: str = "0.0.0.0"
    port: int = 8080
    api_key: str | None = None

    @property
    def data_sink(self) -> Path:
        return self.workspace / "data_lake" / "ingest_api" / "ingested.jsonl"


class _IngestRequestHandler(BaseHTTPRequestHandler):
    """Request handler that validates and persists incoming telemetry."""

    server_version = "SecurityLLMLabIngest/1.0"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - match BaseHTTPRequestHandler signature
        if hasattr(self.server, "logger"):
            self.server.logger.info("%s - - %s", self.address_string(), format % args)
        else:  # pragma: no cover - fallback to default behaviour
            super().log_message(format, *args)

    def _send_json(self, code: HTTPStatus, payload: Mapping[str, object]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_body(self) -> List[Mapping[str, object]]:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            raise ValueError("Missing body")
        data = self.rfile.read(length)
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as exc:  # pragma: no cover - handled in calling code
            raise ValueError("Invalid JSON payload") from exc

        if isinstance(parsed, Mapping):
            return [parsed]
        if isinstance(parsed, list):
            if not all(isinstance(item, Mapping) for item in parsed):
                raise ValueError("Array payload must contain objects")
            return parsed
        raise ValueError("Payload must be a JSON object or array of objects")

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        server_config: IngestApiConfig = self.server.config  # type: ignore[attr-defined]
        if self.path.rstrip("/") != "/ingest":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not Found"})
            return

        expected_key = server_config.api_key
        provided_key = self.headers.get("X-API-Key")
        if expected_key and expected_key != provided_key:
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Invalid API key"})
            return

        try:
            events = self._parse_body()
            _persist_events(server_config.data_sink, events)
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        self._send_json(HTTPStatus.OK, {"ingested": len(events)})


class _IngestServer(ThreadingHTTPServer):
    """Custom HTTP server that exposes logging and configuration attributes."""

    def __init__(self, server_address: tuple[str, int], config: IngestApiConfig) -> None:
        handler = _IngestRequestHandler
        super().__init__(server_address, handler)
        self.config = config
        self.logger = configure_logging(name="IngestApiServer")


def _persist_events(path: Path, events: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as handle:
        for event in events:
            materialized = dict(event)
            materialized.setdefault("ingested_at", timestamp)
            handle.write(json.dumps(materialized, ensure_ascii=False) + "\n")


def run_ingest_api_server(config: IngestApiConfig) -> None:
    """Start a blocking HTTP server for local agent ingestion."""

    logger = configure_logging(name="IngestApi")
    server = _IngestServer((config.host, config.port), config)
    logger.info(
        "Starting ingestion API on http://%s:%s/ingest (workspace=%s)",
        config.host,
        config.port,
        config.workspace,
    )
    if config.api_key:
        logger.info("Ingestion API requires X-API-Key header")

    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual stop
        logger.info("Shutting down ingestion API")
    finally:
        server.server_close()


__all__ = ["IngestApiConfig", "run_ingest_api_server"]
