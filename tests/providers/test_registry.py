"""Tests for provider registry."""

import pytest
from typing import Optional, Type

from jungent.providers import BaseProvider, ProviderModel, ProviderRegistry, ProviderConfig


def _create_mock_provider_class(provider_id: str) -> Type[BaseProvider]:
    """Factory function to create unique mock provider classes."""
    
    class MockProvider(BaseProvider):
        provider_name = ""

        def _get_default_api_base_url(self) -> str:
            return "https://mock.api.example.com"

        def __init__(self, api_key: Optional[str] = None, **kwargs):
            # Use a test API key by default
            super().__init__(api_key or "test-mock-key", **kwargs)
            self.models = [
                ProviderModel(
                    id=f"{provider_id}-model-1",
                    name=f"{provider_id} Model 1",
                    context_window=8000,
                ),
                ProviderModel(
                    id=f"{provider_id}-model-2",
                    name=f"{provider_id} Model 2",
                    context_window=16000,
                ),
            ]

        async def generate_response(
            self,
            prompt: str,
            model: str,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            tools=None,
        ) -> str:
            """Mock response generation."""
            return f"Mock response for {model}"

        def list_models(self) -> list:
            """Mock model listing."""
            return self.models

        @property
        def provider_id(self) -> str:
            return provider_id

    # Set provider_name using setattr to avoid class scope issues
    setattr(MockProvider, 'provider_name', f"Mock {provider_id}")

    return MockProvider


# Pre-create some provider classes for tests that need them
MockProvider1 = _create_mock_provider_class("mock1")
MockProvider2 = _create_mock_provider_class("mock2")
MockProvider3 = _create_mock_provider_class("mock3")
MockProvider = _create_mock_provider_class("mock")
OtherMockProvider = _create_mock_provider_class("other")


class TestProviderRegistry:
    """Tests for ProviderRegistry class."""

    def test_register_provider(self):
        """Test registering a provider class."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)

        assert "mock" in registry.list_available_providers()

    def test_get_provider(self):
        """Test getting a provider instance."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)

        provider = registry.get("mock")

        assert provider is not None
        assert provider.provider_id == "mock"

    def test_get_nonexistent_provider(self):
        """Test getting a non-existent provider."""
        registry = ProviderRegistry()

        provider = registry.get("non-existent")

        assert provider is None

    def test_register_instance(self):
        """Test registering a provider instance."""
        registry = ProviderRegistry()
        provider = MockProvider()
        registry.register_instance(provider)

        assert registry.get("mock") is not None

    def test_disable_provider(self):
        """Test disabling a provider."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.disable_provider("mock")

        assert registry.get("mock") is None

    def test_enable_provider(self):
        """Test enabling a provider."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.disable_provider("mock")

        provider = registry.enable_provider("mock")
        assert provider is not None
        assert provider.provider_id == "mock"

    def test_get_all_providers(self):
        """Test getting all provider instances."""
        registry = ProviderRegistry()
        registry.register("mock1", MockProvider1)
        registry.register("mock2", MockProvider2)
        # Get instances to create them
        registry.get("mock1")
        registry.get("mock2")

        providers = registry.get_all()
        assert len(providers) == 2

    def test_load_from_config_disabled(self):
        """Test loading config with disabled providers."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.register("other", OtherMockProvider)

        config = {"disabled_providers": ["mock"]}
        registry.load_from_config(config)

        # After loading config, disabled providers should return None
        assert registry.get("mock") is None
        assert registry.get("other") is not None

    def test_load_from_config_enabled(self):
        """Test loading config with enabled providers."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.register("other", OtherMockProvider)

        config = {"enabled_providers": ["mock"]}
        registry.load_from_config(config)

        assert registry.get("mock") is not None
        assert registry.get("other") is None

    def test_find_model(self):
        """Test finding a model across providers."""
        registry = ProviderRegistry()
        provider_instance = MockProvider()
        registry.register_instance(provider_instance)

        result = registry.find_model("mock-model-1")
        assert result is not None
        provider, model = result
        assert provider.provider_id == "mock"
        assert model.id == "mock-model-1"

    def test_find_model_not_found(self):
        """Test finding a non-existent model."""
        registry = ProviderRegistry()

        result = registry.find_model("non-existent")
        assert result is None

    def test_get_enabled_providers(self):
        """Test getting only enabled providers."""
        registry = ProviderRegistry()
        registry.register("mock1", MockProvider1)
        registry.register("mock2", MockProvider2)
        registry.register("mock3", MockProvider3)

        # Create instances
        registry.get("mock1")
        registry.get("mock2")
        registry.get("mock3")

        # Disable one
        registry.disable_provider("mock2")

        enabled = registry.get_enabled_providers()
        assert len(enabled) == 2
        provider_ids = [p.provider_id for p in enabled]
        assert "mock1" in provider_ids
        assert "mock2" not in provider_ids
        assert "mock3" in provider_ids

    def test_get_enabled_providers_with_enabled_list(self):
        """Test getting enabled providers with allowlist."""
        registry = ProviderRegistry()
        registry.register("mock1", MockProvider1)
        registry.register("mock2", MockProvider2)
        registry.register("mock3", MockProvider3)

        # Create instances
        registry.get("mock1")
        registry.get("mock2")
        registry.get("mock3")

        # Set enabled list (only mock1 should be enabled)
        registry.load_from_config({"enabled_providers": ["mock1"]})

        enabled = registry.get_enabled_providers()
        assert len(enabled) == 1
        assert enabled[0].provider_id == "mock1"

    def test_disable_provider_cleans_instance(self):
        """Test that disabling a provider removes its instance."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)

        # Create instance
        provider = registry.get("mock")
        assert provider is not None

        # Disable provider
        registry.disable_provider("mock")

        # Get should return None (should not reuse cached instance)
        assert registry.get("mock") is None

    def test_enable_provider_with_api_key(self):
        """Test enabling a provider with an API key."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)

        provider = registry.enable_provider("mock", api_key="test-key")

        assert provider is not None
        assert provider.api_key == "test-key"

    def test_load_from_config_with_enabled_and_disabled(self):
        """Test loading config with both enabled and disabled lists."""
        registry = ProviderRegistry()
        registry.register("mock1", MockProvider1)
        registry.register("mock2", MockProvider2)

        # enabled_providers takes precedence
        config = {
            "enabled_providers": ["mock1", "mock2"],
            "disabled_providers": ["mock2"]
        }
        registry.load_from_config(config)

        assert registry.get("mock1") is not None
        # mock2 should be disabled because it's in disabled list
        assert registry.get("mock2") is None

    def test_get_with_api_key_parameter(self):
        """Test getting a provider with API key from params."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)

        provider = registry.get("mock", api_key="param-key")

        assert provider is not None
        assert provider.api_key == "param-key"

    def test_registry_reuses_instances(self):
        """Test that registry reuses existing instances."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)

        provider1 = registry.get("mock")
        provider2 = registry.get("mock")

        assert provider1 is provider2


class TestProviderRegistryWithConfig:
    """Tests for ProviderRegistry with ProviderConfig integration."""

    def test_registry_uses_config_disabled(self, tmp_path):
        """Test registry respects ProviderConfig disabled providers."""
        config = ProviderConfig(config_path=str(tmp_path / "config.json"))
        config.disable_provider("mock")

        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.load_from_config(config.to_dict())

        assert registry.get("mock") is None

    def test_registry_uses_config_enabled(self, tmp_path):
        """Test registry respects ProviderConfig enabled providers."""
        config = ProviderConfig(config_path=str(tmp_path / "config.json"))
        config.enable_provider("mock")

        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.load_from_config(config.to_dict())

        assert registry.get("mock") is not None

    def test_registry_uses_config_api_keys(self, tmp_path):
        """Test registry gets API keys from ProviderConfig."""
        config = ProviderConfig(config_path=str(tmp_path / "config.json"))
        config.set_api_key("mock", "config-key")

        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.load_from_config(config.to_dict())

        provider = registry.get("mock")
        assert provider is not None
        assert provider.api_key == "config-key"


class TestProviderRegistryAsync:
    """Async tests for ProviderRegistry."""

    @pytest.mark.asyncio
    async def test_generate_response_via_registry(self):
        """Test generating a response through registry."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)

        result = await registry.generate_response("mock-model-1", "Test prompt")

        assert result == "Mock response for mock-model-1"

    @pytest.mark.asyncio
    async def test_generate_response_not_found(self):
        """Test generating response for non-existent model."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)

        result = await registry.generate_response("non-existent", "Test prompt")

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_response_disabled_provider(self):
        """Test generating response with disabled provider."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.disable_provider("mock")

        result = await registry.generate_response("mock-model-1", "Test prompt")

        assert result is None
