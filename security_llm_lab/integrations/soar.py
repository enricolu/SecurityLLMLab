"""Generic SOAR client for automation workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import requests

from ..logging_utils import configure_logging


@dataclass(slots=True)
class SOARClient:
    base_url: str
    api_key: str
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        self.logger = configure_logging(name=self.__class__.__name__)

    def _headers(self) -> Mapping[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def create_playbook_run(self, name: str, inputs: Mapping[str, object]) -> dict:
        endpoint = f"{self.base_url.rstrip('/')}/playbooks/{name}/run"
        response = requests.post(endpoint, json=inputs, headers=self._headers(), verify=self.verify_ssl, timeout=60)
        response.raise_for_status()
        self.logger.info("Triggered SOAR playbook %s", name)
        return response.json()

    def list_playbooks(self) -> Iterable[dict]:
        endpoint = f"{self.base_url.rstrip('/')}/playbooks"
        response = requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data.get("items", [])
        return data


__all__ = ["SOARClient"]
