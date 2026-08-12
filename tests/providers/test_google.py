"""Tests for Google Gemini provider."""

import pytest
from unittest.mock import MagicMock, patch

from jungent.providers import GoogleProvider


class AsyncMock(MagicMock):
    """Async mock helper for async methods."""

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class TestGoogleProvider:
    """Tests for GoogleProvider class."""

    def test_init_with_api_key(self):
        """Test initializing with API key."""
        provider = GoogleProvider(api_key="test-key")

        assert provider.api_key == "test-key"

    def test_init_with_env_var(self):
        """Test initializing with environment variable."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "env-key"}):
            provider = GoogleProvider()

            assert provider.api_key == "env-key"

    def test_provider_properties(self):
        """Test provider ID and name properties."""
        provider = GoogleProvider(_skip_api_key_validation=True)

        assert provider.provider_id == "google"
        assert provider.provider_name == "Google Gemini"

    def test_list_models(self):
        """Test listing models."""
        provider = GoogleProvider(_skip_api_key_validation=True)
        models = provider.list_models()

        assert len(models) > 0
        model_ids = [model.id for model in models]
        assert "gemini-1.5-pro" in model_ids
        assert "gemini-1.5-flash" in model_ids

    def test_get_model(self):
        """Test getting a specific model."""
        provider = GoogleProvider(_skip_api_key_validation=True)
        model = provider.get_model("gemini-1.0-pro")

        assert model is not None
        assert model.id == "gemini-1.0-pro"
        assert model.name == "Gemini 1.0 Pro"
        assert model.context_window == 30720

    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test generating a successful response."""
        provider = GoogleProvider(api_key="test-key")

        with patch.object(provider, "_make_request") as mock_make_request:
            mock_make_request.return_value = {
                "candidates": [{"content": {"parts": [{"text": "Test response"}]}}],
            }

            result = await provider.generate_response("Test prompt", "gemini-1.5-pro")

            assert result == "Test response"
            mock_make_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_no_api_key(self):
        """Test generating response without API key."""
        provider = GoogleProvider(_skip_api_key_validation=True)

        with pytest.raises(ValueError, match="Google API key not provided"):
            await provider.generate_response("Test prompt", "gemini-1.5-pro")

    @pytest.mark.asyncio
    async def test_generate_response_with_tools(self):
        """Test generating response with tools."""
        provider = GoogleProvider(api_key="test-key")
        tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {"type": "object", "properties": {}},
            }
        ]

        with patch.object(provider, "_make_request") as mock_make_request:
            mock_make_request.return_value = {
                "candidates": [
                    {"content": {"parts": [{"text": "Response with tool"}]}}
                ],
            }

            result = await provider.generate_response(
                "Test prompt", "gemini-1.5-pro", tools=tools
            )

            assert result == "Response with tool"
            # Verify tools were passed in the request
            call_args = mock_make_request.call_args
            json_data = call_args.kwargs.get("json_data")
            assert json_data is not None
            assert "tools" in json_data
            # Verify tools were converted to Google format
            converted_tools = json_data["tools"]
            assert len(converted_tools) == 1
            assert "function_declarations" in converted_tools[0]

    @pytest.mark.asyncio
    async def test_generate_response_invalid_model(self):
        """Test generating response with invalid model."""
        provider = GoogleProvider(api_key="test-key")

        with pytest.raises(ValueError, match="not found"):
            await provider.generate_response("Test prompt", "invalid-model")
