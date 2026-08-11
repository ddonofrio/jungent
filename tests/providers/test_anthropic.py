"""Tests for Anthropic provider."""

import pytest
from unittest.mock import MagicMock, patch


class AsyncMock(MagicMock):
    """Async mock helper for async methods."""

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


from jungent.providers import AnthropicProvider


class TestAnthropicProvider:
    """Tests for AnthropicProvider class."""

    def test_init_with_api_key(self):
        """Test initializing with API key."""
        provider = AnthropicProvider(api_key="test-key")

        assert provider.api_key == "test-key"

    def test_init_with_env_var(self):
        """Test initializing with environment variable."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            provider = AnthropicProvider()

            assert provider.api_key == "env-key"

    def test_provider_properties(self):
        """Test provider ID and name properties."""
        provider = AnthropicProvider(_skip_api_key_validation=True)

        assert provider.provider_id == "anthropic"
        assert provider.provider_name == "Anthropic"

    def test_list_models(self):
        """Test listing models."""
        provider = AnthropicProvider(_skip_api_key_validation=True)
        models = provider.list_models()

        assert len(models) > 0
        assert all(model.id.startswith("claude-") for model in models)

    def test_get_model(self):
        """Test getting a specific model."""
        provider = AnthropicProvider(_skip_api_key_validation=True)
        model = provider.get_model("claude-3-5-sonnet-20240620")

        assert model is not None
        assert model.id == "claude-3-5-sonnet-20240620"
        assert model.name == "Claude 3.5 Sonnet"
        assert model.context_window == 200000
        assert model.supports_vision is True
        assert model.supports_function_calling is True

    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test generating a successful response."""
        provider = AnthropicProvider(api_key="test-key")

        with patch.object(provider, "_make_request") as mock_make_request:
            mock_make_request.return_value = {
                "content": [{"text": "Test response"}],
            }

            result = await provider.generate_response("Test prompt", "claude-3-7-sonnet-20250219")

            assert result == "Test response"
            mock_make_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_no_api_key(self):
        """Test generating response without API key."""
        provider = AnthropicProvider(_skip_api_key_validation=True)

        with pytest.raises(ValueError, match="Anthropic API key not provided"):
            await provider.generate_response("Test prompt", "claude-3-7-sonnet-20250219")

    @pytest.mark.asyncio
    async def test_generate_response_with_tools(self):
        """Test generating response with tools."""
        provider = AnthropicProvider(api_key="test-key")
        tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "input_schema": {"type": "object", "properties": {}},
            }
        ]

        with patch.object(provider, "_make_request") as mock_make_request:
            mock_make_request.return_value = {
                "content": [{"text": "Response with tool"}],
            }

            result = await provider.generate_response(
                "Test prompt", "claude-3-7-sonnet-20250219", tools=tools
            )

            assert result == "Response with tool"
            # Verify tools were passed in the request (converted to Anthropic format)
            call_args = mock_make_request.call_args
            json_data = call_args.kwargs.get("json_data")
            assert json_data is not None
            assert "tools" in json_data
            # Verify tools were converted to Anthropic format
            converted_tools = json_data["tools"]
            assert len(converted_tools) == 1
            assert converted_tools[0]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_generate_response_invalid_model(self):
        """Test generating response with invalid model."""
        provider = AnthropicProvider(api_key="test-key")

        with pytest.raises(ValueError, match="not found"):
            await provider.generate_response("Test prompt", "invalid-model")

    @pytest.mark.asyncio
    async def test_convert_tools_to_anthropic_format_openai_style(self):
        """Test converting tools to Anthropic format (OpenAI style)."""
        provider = AnthropicProvider(api_key="test-key")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {"type": "object"},
                },
            }
        ]

        result = provider._convert_tools_to_anthropic_format(tools)

        assert len(result) == 1
        assert result[0]["name"] == "test_tool"
        assert result[0]["description"] == "A test tool"
        assert result[0]["input_schema"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_convert_tools_to_anthropic_format_anthropic_style(self):
        """Test converting tools to Anthropic format (Anthropic style)."""
        provider = AnthropicProvider(api_key="test-key")
        tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "input_schema": {"type": "object"},
            }
        ]

        result = provider._convert_tools_to_anthropic_format(tools)

        assert len(result) == 1
        assert result[0]["name"] == "test_tool"
        assert result[0]["description"] == "A test tool"
        assert result[0]["input_schema"]["type"] == "object"
