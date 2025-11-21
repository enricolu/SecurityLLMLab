"""Tests for the Security Agent."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from security_llm_lab.config import AppConfig, LLMConfig, AgentConfig
from security_llm_lab.agent.core import SecurityAgent

@pytest.fixture
def mock_config():
    config = MagicMock(spec=AppConfig)
    config.llm = LLMConfig(backend="ollama", model_name="mistral")
    config.agent = AgentConfig(max_iterations=2, tools=["query_siem"])
    config.rag_dir = Path("/tmp/rag")
    config.rag.index_name = "test_index"
    return config

@patch("security_llm_lab.agent.core.get_llm_client")
def test_agent_run_final_answer(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_llm = MagicMock()
    mock_client.get_chat_model.return_value = mock_llm
    
    # Mock LLM response to return Final Answer immediately
    mock_llm.invoke.return_value = MagicMock(content="Final Answer: Test Answer")
    
    agent = SecurityAgent(mock_config)
    result = agent.run("Test Question")
    
    assert result == "Test Answer"

@patch("security_llm_lab.agent.core.get_llm_client")
def test_agent_run_with_tool(mock_get_client, mock_config):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_llm = MagicMock()
    mock_client.get_chat_model.return_value = mock_llm
    
    # Mock LLM responses: 1. Call Tool, 2. Final Answer
    mock_llm.invoke.side_effect = [
        MagicMock(content="Action: query_siem\nAction Input: source_ip:1.2.3.4"),
        MagicMock(content="Final Answer: Found it")
    ]
    
    agent = SecurityAgent(mock_config)
    
    # Mock the tool execution
    with patch("security_llm_lab.agent.tools.query_siem") as mock_tool:
        mock_tool.name = "query_siem"
        mock_tool.description = "Query SIEM"
        mock_tool.invoke.return_value = "Found 1 event"
        
        # We need to inject this mock tool into the agent because get_tools creates new instances
        # Or we can patch get_tools
        with patch("security_llm_lab.agent.core.get_tools", return_value=[mock_tool]):
             agent = SecurityAgent(mock_config) # Re-init to pick up mocked tools
             result = agent.run("Test Question")
    
    assert result == "Found it"
    assert mock_llm.invoke.call_count == 2
