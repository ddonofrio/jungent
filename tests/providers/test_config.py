"""Tests for provider configuration."""

import json
import tempfile
from pathlib import Path

from jungent.providers.config import ProviderConfig


class TestProviderConfig:
    """Tests for ProviderConfig class."""

    def test_init_default_path(self):
        """Test initializing with default path."""
        config = ProviderConfig(config_path="/tmp/test_config.json")
        assert config._config_path == "/tmp/test_config.json"

    def test_load_nonexistent_config(self):
        """Test loading a non-existent config file."""
        config = ProviderConfig(config_path="/tmp/nonexistent/config.json")
        assert config.disabled_providers == []
        assert config.enabled_providers is None

    def test_disabled_providers_empty(self):
        """Test disabled_providers with empty config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            assert config.disabled_providers == []
        finally:
            Path(config_path).unlink()

    def test_disabled_providers_with_values(self):
        """Test disabled_providers with values."""
        config_data = {"disabled_providers": ["kilo", "openai"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            assert "kilo" in config.disabled_providers
            assert "openai" in config.disabled_providers
        finally:
            Path(config_path).unlink()

    def test_enabled_providers_none(self):
        """Test enabled_providers when None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            assert config.enabled_providers is None
        finally:
            Path(config_path).unlink()

    def test_enabled_providers_with_values(self):
        """Test enabled_providers with values."""
        config_data = {"enabled_providers": ["anthropic", "openai"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            assert config.enabled_providers == ["anthropic", "openai"]
        finally:
            Path(config_path).unlink()

    def test_is_provider_disabled_by_disabled_list(self):
        """Test checking if provider is disabled via disabled list."""
        config_data = {"disabled_providers": ["kilo", "openai"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            assert config.is_provider_disabled("kilo") is True
            assert config.is_provider_disabled("openai") is True
            assert config.is_provider_disabled("anthropic") is False
        finally:
            Path(config_path).unlink()

    def test_is_provider_disabled_by_enabled_list(self):
        """Test checking if provider is disabled via enabled list."""
        config_data = {"enabled_providers": ["anthropic", "openai"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            assert config.is_provider_disabled("anthropic") is False
            assert config.is_provider_disabled("openai") is False
            assert config.is_provider_disabled("kilo") is True
        finally:
            Path(config_path).unlink()

    def test_disable_provider(self):
        """Test disabling a provider."""
        config_data = {"disabled_providers": ["kilo"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            config.disable_provider("openai")

            assert "openai" in config.disabled_providers
        finally:
            Path(config_path).unlink()

    def test_enable_provider(self):
        """Test enabling a provider."""
        config_data = {"disabled_providers": ["kilo", "openai"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            config.enable_provider("openai")

            assert "openai" not in config.disabled_providers
            assert "kilo" in config.disabled_providers
        finally:
            Path(config_path).unlink()

    def test_set_api_key(self):
        """Test setting an API key."""
        config = ProviderConfig(config_path="/tmp/test_config_set_key.json")
        config.set_api_key("anthropic", "test-key-123")

        assert config.get_api_key("anthropic") == "test-key-123"

    def test_get_api_key_not_set(self):
        """Test getting an unset API key."""
        config = ProviderConfig(config_path="/tmp/test_config_get_key.json")

        assert config.get_api_key("anthropic") is None

    def test_to_dict(self):
        """Test converting config to dict."""
        config_data = {"disabled_providers": ["kilo"]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ProviderConfig(config_path=config_path)
            config_dict = config.to_dict()

            assert "disabled_providers" in config_dict
            assert config_dict["disabled_providers"] == ["kilo"]
        finally:
            Path(config_path).unlink()
