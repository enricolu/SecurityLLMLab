"""Tests for data pipeline."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from security_llm_lab.config import AppConfig, LocalSourceConfig
from security_llm_lab.pipelines.data_pipeline import DataPipeline


class TestDataPipeline:
    """Test DataPipeline class."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test configuration."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        return AppConfig(
            workspace=workspace,
            local_sources=[],
            remote_sources=[],
        )

    @pytest.fixture
    def pipeline(self, config):
        """Create a test pipeline."""
        return DataPipeline(config)

    def test_collect_local_sources_success(self, pipeline, tmp_path):
        """Test successful collection from local sources."""
        # Create a test log file
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "test.log"
        log_file.write_text("test log line 1\ntest log line 2\n")

        source = LocalSourceConfig(path=log_dir, glob="*.log")
        pipeline.config.local_sources = [source]

        results = pipeline._collect_local_sources([source])
        assert len(results) == 1
        assert results[0].exists()
        assert results[0].suffix == ".jsonl"

        # Verify content
        with results[0].open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2
            for line in lines:
                record = json.loads(line)
                assert "timestamp" in record
                assert "raw" in record
                assert record["raw"] in ["test log line 1", "test log line 2"]

    def test_collect_local_sources_nonexistent_path(self, pipeline):
        """Test that non-existent paths are handled gracefully."""
        source = LocalSourceConfig(path=Path("/nonexistent/path"), glob="*.log")
        results = pipeline._collect_local_sources([source])
        # Should continue despite error
        assert isinstance(results, list)

    def test_load_jsonl(self, pipeline, tmp_path):
        """Test loading JSONL files."""
        jsonl_file = tmp_path / "test.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            json.dump({"key": "value1"}, f)
            f.write("\n")
            json.dump({"key": "value2"}, f)
            f.write("\n")
            f.write("invalid json\n")  # Should be skipped

        records = list(pipeline._load_jsonl(jsonl_file))
        assert len(records) == 2
        assert records[0]["key"] == "value1"
        assert records[1]["key"] == "value2"

    @patch("security_llm_lab.pipelines.data_pipeline.requests.get")
    def test_download_remote_source_retry(self, mock_get, pipeline, tmp_path):
        """Test that download retries on failure."""
        from requests.exceptions import ConnectionError

        # First two attempts fail, third succeeds
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        mock_get.side_effect = [
            ConnectionError("Connection failed"),
            ConnectionError("Connection failed"),
            mock_response,
        ]

        from security_llm_lab.config import RemoteSourceConfig

        source = RemoteSourceConfig(
            name="test",
            url="https://example.com/test.txt",
            enabled=True,
        )

        result = pipeline._download_remote_source(source)
        assert result.exists()
        assert mock_get.call_count == 3

