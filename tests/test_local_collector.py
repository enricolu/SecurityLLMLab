"""Tests for local collector."""

import json
from datetime import timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from security_llm_lab.collectors.local_collector import LocalCollector, LocalCollectorConfig


class TestLocalCollector:
    """Test LocalCollector class."""

    def test_collect_creates_jsonl(self, tmp_path):
        """Test that collect creates a JSONL file."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "test.log"
        log_file.write_text("line 1\nline 2\nline 3\n")

        config = LocalCollectorConfig(path=log_dir, glob="*.log")
        collector = LocalCollector(config)

        output = collector.collect(tmp_path / "output")
        assert output.exists()
        assert output.suffix == ".jsonl"

        # Verify content
        with output.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 3
            for line in lines:
                record = json.loads(line)
                assert "timestamp" in record
                assert "raw" in record
                assert record["collector"] == "local"

    def test_normalize_record_uses_utc(self, tmp_path):
        """Test that normalize_record uses UTC timezone."""
        config = LocalCollectorConfig(path=tmp_path)
        collector = LocalCollector(config)

        with patch("security_llm_lab.collectors.local_collector.datetime") as mock_dt:
            from datetime import datetime

            mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.now.return_value = mock_now
            mock_dt.timezone = timezone

            record = collector._normalize_record("test line", Path("test.log"))
            assert record["timestamp"] == "2024-01-01T12:00:00+00:00"
            assert record["raw"] == "test line"
            assert record["collector"] == "local"

    def test_fingerprint_consistency(self, tmp_path):
        """Test that fingerprint is consistent for same config."""
        config1 = LocalCollectorConfig(path=tmp_path, glob="*.log")
        config2 = LocalCollectorConfig(path=tmp_path, glob="*.log")
        collector1 = LocalCollector(config1)
        collector2 = LocalCollector(config2)

        assert collector1._fingerprint() == collector2._fingerprint()

    def test_fingerprint_different_for_different_configs(self, tmp_path):
        """Test that fingerprint differs for different configs."""
        config1 = LocalCollectorConfig(path=tmp_path, glob="*.log")
        config2 = LocalCollectorConfig(path=tmp_path, glob="*.txt")
        collector1 = LocalCollector(config1)
        collector2 = LocalCollector(config2)

        assert collector1._fingerprint() != collector2._fingerprint()

