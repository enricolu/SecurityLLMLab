"""Client utilities for interacting with the Wazuh REST API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional

import requests

from ..logging_utils import configure_logging


@dataclass(slots=True)
class WazuhClient:
    """Lightweight wrapper around the Wazuh management API.

    The client supports token acquisition, reading alerts, listing agents,
    and submitting test events via the ``/manager/logtest`` endpoint. The
    implementation intentionally keeps to the core REST primitives so it can
    operate in constrained environments.
    """

    base_url: str
    verify_ssl: bool = True
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None

    def __post_init__(self) -> None:
        self.logger = configure_logging(name=self.__class__.__name__)
        if not self.token:
            if not (self.username and self.password):
                raise ValueError("username/password or token must be provided for Wazuh API access")
            self.token = self._authenticate()

    def _authenticate(self) -> str:
        endpoint = f"{self.base_url.rstrip('/')}/security/user/authenticate"
        self.logger.info("Requesting Wazuh token from %s", endpoint)
        response = requests.post(
            endpoint,
            auth=(self.username or "", self.password or ""),
            headers={"Content-Type": "application/json"},
            verify=self.verify_ssl,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("data", {}).get("token")
        if not token:
            raise ValueError("Failed to obtain Wazuh token")
        return token

    def _headers(self) -> Mapping[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, path: str, params: Optional[MutableMapping[str, object]] = None) -> dict:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        response = requests.get(url, headers=self._headers(), params=params, verify=self.verify_ssl, timeout=60)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: Mapping[str, object]) -> dict:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        response = requests.post(url, headers=self._headers(), json=payload, verify=self.verify_ssl, timeout=60)
        response.raise_for_status()
        return response.json()

    def list_agents(self, limit: int = 50) -> dict:
        """Return the registered agents with pagination support."""

        params: MutableMapping[str, object] = {"limit": limit}
        return self._get("agents", params=params)

    def search_alerts(self, query: str, limit: int = 50) -> dict:
        """Search alerts using the ``q`` filter expression.

        Example query: ``agent.name=ossec AND rule.level:>=8``.
        """

        params: MutableMapping[str, object] = {"q": query, "limit": limit}
        return self._get("alerts", params=params)

    def submit_logtest(self, message: str, agent_id: Optional[str] = None) -> dict:
        """Send a synthetic log entry to the Wazuh manager.

        This calls ``/manager/logtest`` which can be used for pipeline validation
        or to trigger custom rules.
        """

        payload: MutableMapping[str, object] = {"logtest": message}
        if agent_id:
            payload["agent"] = agent_id
        return self._post("manager/logtest", payload)

    def index_custom_event(self, data: Mapping[str, object]) -> dict:
        """Store a custom event by forwarding it through the logtest endpoint."""

        message = json.dumps(data, ensure_ascii=False)
        return self.submit_logtest(message)


__all__ = ["WazuhClient"]
