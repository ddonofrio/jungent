"""Tests for base provider and registry."""

import pytest
from typing import List, Optional

from jungent.providers import BaseProvider, ProviderModel, ProviderRegistry


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    provider_id = "mock"
    provider_name = "Mock Provider"

    def _get_default_api_base_url(self) -> str:
        return "https://mock.api.example.com"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        # Use a fake key for testing if none provided
        super().__init__(api_key or "test-mock-key", **kwargs)
        self.models = [
            ProviderModel(
                id="mock-model-1",
                name="Mock Model 1",
                context_window=8000,
            ),
            ProviderModel(
                id="mock-model-2",
                name="Mock Model 2",
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

    def list_models(self) -> List[ProviderModel]:
        """Mock model listing."""
        return self.models


class TestProviderModel:
    """Tests for ProviderModel class."""

    def test_provider_model_creation(self):
        """Test creating a ProviderModel instance."""
        model = ProviderModel(
            id="test-model",
            name="Test Model",
            description="A test model",
            context_window=8000,
            supports_vision=True,
            supports_function_calling=False,
        )

        assert model.id == "test-model"
        assert model.name == "Test Model"
        assert model.description == "A test model"
        assert model.context_window == 8000
        assert model.supports_vision is True
        assert model.supports_function_calling is False

    def test_provider_model_defaults(self):
        """Test ProviderModel with default values."""
        model = ProviderModel(id="test", name="Test")

        assert model.id == "test"
        assert model.name == "Test"
        assert model.description is None
        assert model.context_window is None
        assert model.supports_vision is False
        assert model.supports_function_calling is False


class TestBaseProvider:
    """Tests for BaseProvider class."""

    def test_provider_properties(self):
        """Test provider ID and name properties."""
        provider = MockProvider(_skip_api_key_validation=True)

        assert provider.provider_id == "mock"
        assert provider.provider_name == "Mock Provider"

    def test_get_model_exists(self):
        """Test getting an existing model."""
        provider = MockProvider(_skip_api_key_validation=True)
        model = provider.get_model("mock-model-1")

        assert model is not None
        assert model.id == "mock-model-1"
        assert model.name == "Mock Model 1"

    def test_get_model_not_exists(self):
        """Test getting a non-existent model."""
        provider = MockProvider(_skip_api_key_validation=True)
        model = provider.get_model("non-existent")

        assert model is None

    def test_supports_model_exists(self):
        """Test checking if a model is supported."""
        provider = MockProvider(_skip_api_key_validation=True)

        assert provider.supports_model("mock-model-1") is True
        assert provider.supports_model("non-existent") is False

    def test_list_models(self):
        """Test listing all models."""
        provider = MockProvider(_skip_api_key_validation=True)
        models = provider.list_models()

        assert len(models) == 2
        assert models[0].id == "mock-model-1"
        assert models[1].id == "mock-model-2"

    def test_api_base_url(self):
        """Test default API base URL."""
        provider = MockProvider(api_key="test-key")

        assert provider.api_base_url == "https://mock.api.example.com"

    def test_validate_temperature(self):
        """Test temperature validation."""
        provider = MockProvider(api_key="test-key")

        # Valid temperatures should not raise
        provider._validate_temperature(0.0)
        provider._validate_temperature(1.0)
        provider._validate_temperature(2.0)

        # Invalid temperature should raise
        with pytest.raises(ValueError, match="Temperature must be between"):
            provider._validate_temperature(3.0)

    def test_validate_max_tokens(self):
        """Test max_tokens validation."""
        provider = MockProvider(api_key="test-key")

        # Valid max_tokens should not raise
        provider._validate_max_tokens(None)
        provider._validate_max_tokens(100)

        # Invalid max_tokens should raise
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            provider._validate_max_tokens(-1)


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
        registry.register("mock1", MockProvider)
        registry.register("mock2", MockProvider)
        # Get instances to create them
        registry.get("mock1")
        registry.get("mock2")

        providers = registry.get_all()
        assert len(providers) == 2

    def test_load_from_config_disabled(self):
        """Test loading config with disabled providers."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.register("other", MockProvider)

        config = {"disabled_providers": ["mock"]}
        registry.load_from_config(config)

        # After loading config, disabled providers should return None
        assert registry.get("mock") is None
        assert registry.get("other") is not None

    def test_load_from_config_enabled(self):
        """Test loading config with enabled providers."""
        registry = ProviderRegistry()
        registry.register("mock", MockProvider)
        registry.register("other", MockProvider)

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
