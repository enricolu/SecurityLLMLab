"""Tests for Rule Generation."""

import pytest
from unittest.mock import MagicMock, patch
from security_llm_lab.config import AppConfig, LLMConfig
from security_llm_lab.rules.generator import RuleGenerator

@pytest.fixture
def mock_config():
    config = MagicMock(spec=AppConfig)
    config.llm = LLMConfig(backend="ollama", model_name="mistral")
    return config

@patch("security_llm_lab.rules.generator.get_llm_client")
def test_generate_sigma(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_llm = MagicMock()
    mock_client.get_chat_model.return_value = mock_llm
    
    mock_llm.invoke.return_value = MagicMock(content="title: Test Rule\nlogsource:\n  product: windows")
    
    generator = RuleGenerator(mock_config)
    result = generator.generate_sigma("Detect failed logins")
    
    assert "title: Test Rule" in result
    mock_llm.invoke.assert_called_once()

@patch("security_llm_lab.rules.generator.get_llm_client")
def test_generate_splunk(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_llm = MagicMock()
    mock_client.get_chat_model.return_value = mock_llm
    
    mock_llm.invoke.return_value = MagicMock(content="index=security action=failure")
    
    generator = RuleGenerator(mock_config)
    result = generator.generate_splunk("Detect failed logins")
    
    assert result == "index=security action=failure"
    mock_llm.invoke.assert_called_once()
