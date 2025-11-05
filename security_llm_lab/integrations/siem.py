"""Client for interacting with UTMStack-compatible SIEM platforms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

import requests

from ..logging_utils import configure_logging


@dataclass(slots=True)
class UTMStackClient:
    base_url: str
    api_key: str
    verify_ssl: bool = True
    default_index: str = "security-events"

    def __post_init__(self) -> None:
        self.logger = configure_logging(name=self.__class__.__name__)

    def _headers(self) -> Mapping[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def send_events(self, events: Iterable[Mapping[str, object]], index: Optional[str] = None) -> None:
        payload = list(events)
        if not payload:
            self.logger.warning("No events provided to send to SIEM")
            return

        endpoint = f"{self.base_url.rstrip('/')}/events"
        params = {"index": index or self.default_index}
        self.logger.info("Sending %d events to %s", len(payload), endpoint)
        response = requests.post(endpoint, json=payload, headers=self._headers(), params=params, verify=self.verify_ssl)
        if response.status_code >= 400:
            self.logger.error("Failed to send events: %s", response.text)
            response.raise_for_status()

    def test_connection(self) -> bool:
        endpoint = f"{self.base_url.rstrip('/')}/status"
        response = requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)
        if response.ok:
            self.logger.info("SIEM connection succeeded")
            return True
        self.logger.error("SIEM connection failed: %s", response.text)
        return False


__all__ = ["UTMStackClient"]
