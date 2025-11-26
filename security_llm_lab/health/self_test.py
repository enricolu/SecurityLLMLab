"""Health and self-test utilities for SIEM/SOAR connectivity."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from security_llm_lab.config import AppConfig, SIEMConfig
from security_llm_lab.integrations import UTMStackClient
from security_llm_lab.logging_utils import configure_logging


@dataclass(slots=True)
class SelfTestResult:
    """Outcome of a self-test run."""

    synthetic_event_path: Path
    siem_forwarded: bool


class SelfTestRunner:
    """Generate a synthetic event to validate pipeline and SIEM connectivity."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = configure_logging(name=self.__class__.__name__)

    def run(self) -> SelfTestResult:
        """Write a synthetic event and optionally forward it to the SIEM."""

        self.config.ensure_directories()
        event = self._build_synthetic_event()
        event_path = self._write_event(event)
        siem_forwarded = self._maybe_forward_to_siem([event])
        return SelfTestResult(synthetic_event_path=event_path, siem_forwarded=siem_forwarded)

    def _build_synthetic_event(self) -> dict:
        return {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "severity": "medium",
            "category": "self_test",
            "message": "Security LLM Lab synthetic end-to-end test event",
            "collector": "self-test",
        }

    def _write_event(self, event: dict) -> Path:
        health_dir = self.config.workspace / "health"
        health_dir.mkdir(parents=True, exist_ok=True)
        output = health_dir / "self_test_event.jsonl"
        with output.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        self.logger.info("Self-test event written to %s", output)
        return output

    def _maybe_forward_to_siem(self, events: List[dict]) -> bool:
        siem_config: SIEMConfig | None = self.config.siem
        if not siem_config:
            self.logger.info("Skipping SIEM forwarding because no SIEM configuration is set")
            return False

        client = UTMStackClient(
            base_url=siem_config.base_url,
            api_key=siem_config.api_key,
            verify_ssl=siem_config.verify_ssl,
            default_index=siem_config.default_index,
        )
        client.test_connection()
        client.send_events(events)
        return True


__all__ = ["SelfTestRunner", "SelfTestResult"]
