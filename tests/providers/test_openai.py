"""Tests for OpenAI provider."""

import pytest
from unittest.mock import MagicMock, patch


class AsyncMock(MagicMock):
    """Async mock helper for async methods."""

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


from jungent.providers import OpenAIProvider


class TestOpenAIProvider:
    """Tests for OpenAIProvider class."""

    def test_init_with_api_key(self):
        """Test initializing with API key."""
        provider = OpenAIProvider(api_key="test-key")

        assert provider.api_key == "test-key"

    def test_init_with_env_var(self):
        """Test initializing with environment variable."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            provider = OpenAIProvider()

            assert provider.api_key == "env-key"

    def test_provider_properties(self):
        """Test provider ID and name properties."""
        provider = OpenAIProvider(_skip_api_key_validation=True)

        assert provider.provider_id == "openai"
        assert provider.provider_name == "OpenAI"

    def test_list_models(self):
        """Test listing models."""
        provider = OpenAIProvider(_skip_api_key_validation=True)
        models = provider.list_models()

        assert len(models) > 0
        model_ids = [model.id for model in models]
        assert "gpt-4o" in model_ids
        assert "gpt-3.5-turbo" in model_ids

    def test_get_model(self):
        """Test getting a specific model."""
        provider = OpenAIProvider(_skip_api_key_validation=True)
        model = provider.get_model("gpt-4-turbo")

        assert model is not None
        assert model.id == "gpt-4-turbo"
        assert model.name == "GPT-4 Turbo"
        assert model.context_window == 128000
        assert model.supports_vision is True

    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test generating a successful response."""
        provider = OpenAIProvider(api_key="test-key")

        with patch.object(provider, "_make_request") as mock_make_request:
            mock_make_request.return_value = {
                "choices": [{"message": {"content": "Test response"}}],
            }

            result = await provider.generate_response("Test prompt", "gpt-4o")

            assert result == "Test response"
            mock_make_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_no_api_key(self):
        """Test generating response without API key."""
        provider = OpenAIProvider(_skip_api_key_validation=True)

        with pytest.raises(ValueError, match="OpenAI API key not provided"):
            await provider.generate_response("Test prompt", "gpt-4o")

    @pytest.mark.asyncio
    async def test_generate_response_with_tools(self):
        """Test generating response with tools."""
        provider = OpenAIProvider(api_key="test-key")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                },
            }
        ]

        with patch.object(provider, "_make_request") as mock_make_request:
            mock_make_request.return_value = {
                "choices": [{"message": {"content": "Response with tool"}}],
            }

            result = await provider.generate_response(
                "Test prompt", "gpt-4o", tools=tools
            )

            assert result == "Response with tool"
            # Verify tools were passed in the request
            call_args = mock_make_request.call_args
            json_data = call_args.kwargs.get("json_data")
            assert json_data is not None
            assert "tools" in json_data
            assert json_data["tools"] == tools

    @pytest.mark.asyncio
    async def test_generate_response_invalid_model(self):
        """Test generating response with invalid model."""
        provider = OpenAIProvider(api_key="test-key")

        with pytest.raises(ValueError, match="not found"):
            await provider.generate_response("Test prompt", "invalid-model")

    @pytest.mark.asyncio
    async def test_generate_response_invalid_temperature(self):
        """Test generating response with invalid temperature."""
        provider = OpenAIProvider(api_key="test-key")

        with pytest.raises(ValueError, match="Temperature must be between"):
            await provider.generate_response("Test prompt", "gpt-4o", temperature=3.0)

    @pytest.mark.asyncio
    async def test_generate_response_empty_prompt(self):
        """Test generating response with empty prompt."""
        provider = OpenAIProvider(api_key="test-key")

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await provider.generate_response("", "gpt-4o")
