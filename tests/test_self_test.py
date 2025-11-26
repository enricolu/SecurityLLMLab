"""Tests for synthetic self-test runner."""

from unittest.mock import patch

from security_llm_lab.config import AppConfig, SIEMConfig
from security_llm_lab.health.self_test import SelfTestRunner


def test_self_test_writes_event(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config = AppConfig(workspace=workspace, local_sources=[], remote_sources=[])

    runner = SelfTestRunner(config)
    result = runner.run()

    assert result.synthetic_event_path.exists()
    content = result.synthetic_event_path.read_text(encoding="utf-8").strip()
    assert "self_test" in content
    assert not result.siem_forwarded


@patch("security_llm_lab.health.self_test.UTMStackClient")
def test_self_test_forwards_to_siem(mock_client_cls, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    siem_config = SIEMConfig(base_url="https://siem.example", api_key="abc123")
    config = AppConfig(workspace=workspace, local_sources=[], remote_sources=[], siem=siem_config)

    runner = SelfTestRunner(config)
    result = runner.run()

    mock_client_cls.assert_called_once()
    client_instance = mock_client_cls.return_value
    client_instance.test_connection.assert_called_once()
    client_instance.send_events.assert_called_once()
    assert result.siem_forwarded
