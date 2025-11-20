"""Tests for configuration module."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from security_llm_lab.config import AppConfig, SIEMConfig, SOARConfig


class TestSIEMConfig:
    """Test SIEMConfig class."""

    def test_from_mapping_with_env_var(self, monkeypatch):
        """Test that environment variable takes precedence over config."""
        monkeypatch.setenv("SIEM_API_KEY", "env_api_key")
        data = {
            "base_url": "https://siem.example.com",
            "api_key": "config_api_key",
            "verify_ssl": True,
            "default_index": "test-index",
        }
        config = SIEMConfig.from_mapping(data)
        assert config.api_key == "env_api_key"
        assert config.base_url == "https://siem.example.com"
        assert config.verify_ssl is True
        assert config.default_index == "test-index"

    def test_from_mapping_without_env_var(self):
        """Test that config value is used when env var is not set."""
        data = {
            "base_url": "https://siem.example.com",
            "api_key": "config_api_key",
        }
        config = SIEMConfig.from_mapping(data)
        assert config.api_key == "config_api_key"

    def test_from_mapping_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        data = {
            "base_url": "https://siem.example.com",
        }
        with pytest.raises(ValueError, match="SIEM API key must be provided"):
            SIEMConfig.from_mapping(data)


class TestSOARConfig:
    """Test SOARConfig class."""

    def test_from_mapping_with_env_var(self, monkeypatch):
        """Test that environment variable takes precedence over config."""
        monkeypatch.setenv("SOAR_API_KEY", "env_soar_key")
        data = {
            "base_url": "https://soar.example.com",
            "api_key": "config_soar_key",
        }
        config = SOARConfig.from_mapping(data)
        assert config.api_key == "env_soar_key"

    def test_from_mapping_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        data = {
            "base_url": "https://soar.example.com",
        }
        with pytest.raises(ValueError, match="SOAR API key must be provided"):
            SOARConfig.from_mapping(data)


class TestAppConfig:
    """Test AppConfig class."""

    def test_load_and_validate(self, tmp_path):
        """Test loading and validating a configuration file."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "workspace": str(tmp_path / "workspace"),
            "local_sources": [],
            "remote_sources": [],
        }
        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        config = AppConfig.load(config_path)
        assert config.workspace == tmp_path / "workspace"
        assert config.workspace.exists()

    def test_validate_invalid_siem_url(self, tmp_path):
        """Test validation catches invalid SIEM URL."""
        config = AppConfig(
            workspace=tmp_path / "workspace",
            local_sources=[],
            remote_sources=[],
            siem=SIEMConfig(
                base_url="not-a-valid-url",
                api_key="test-key",
            ),
        )
        with pytest.raises(ValueError, match="Invalid SIEM base_url"):
            config.validate()

    def test_validate_invalid_training_config(self, tmp_path):
        """Test validation catches invalid training configuration."""
        from security_llm_lab.config import TrainingConfig

        config = AppConfig(
            workspace=tmp_path / "workspace",
            local_sources=[],
            remote_sources=[],
            training=TrainingConfig(
                model_name="test-model",
                per_device_train_batch_size=0,  # Invalid
                learning_rate=-1.0,  # Invalid
            ),
        )
        with pytest.raises(ValueError):
            config.validate()

    def test_validate_local_source_path(self, tmp_path):
        """Test validation catches non-existent local source paths."""
        from security_llm_lab.config import LocalSourceConfig

        config = AppConfig(
            workspace=tmp_path / "workspace",
            local_sources=[
                LocalSourceConfig(path=tmp_path / "nonexistent"),
            ],
            remote_sources=[],
        )
        with pytest.raises(ValueError, match="path does not exist"):
            config.validate()

