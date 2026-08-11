"""Google Gemini provider implementation."""

import os
from typing import Any, Dict, List, Optional

from .base import BaseProvider, ProviderModel


class GoogleProvider(BaseProvider):
    """Provider for Google Gemini models."""

    provider_id = "google"
    provider_name = "Google Gemini"

    def _get_default_api_base_url(self) -> str:
        return "https://generativelanguage.googleapis.com/v1"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.environ.get("GOOGLE_API_KEY"), **kwargs)
        self.models = [
            ProviderModel(
                id="gemini-1.5-pro",
                name="Gemini 1.5 Pro",
                description="Multimodal model with large context window",
                context_window=1000000,
                supports_vision=True,
                supports_function_calling=True,
            ),
            ProviderModel(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash",
                description="Fast and efficient multimodal model",
                context_window=1000000,
                supports_vision=True,
                supports_function_calling=True,
            ),
            ProviderModel(
                id="gemini-1.0-pro",
                name="Gemini 1.0 Pro",
                description="Original Gemini model",
                context_window=30720,
                supports_vision=False,
                supports_function_calling=True,
            ),
        ]

    async def generate_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate a response using Google's API."""
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_model(model)
        self._validate_temperature(temperature)
        self._validate_max_tokens(max_tokens)
        if not self.api_key:
            raise ValueError("Google API key not provided")

        # Build request payload
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if tools:
            payload["tools"] = [
                {"function_declarations": [t.get("function", {}) for t in tools]}
            ]

        # Make request with retry logic
        data = await self._make_request(
            url=f"{self.api_base_url}/models/{model}:generateContent",
            headers={"content-type": "application/json"},
            params={"key": self.api_key},
            json_data=payload,
        )

        return self._parse_response_data(data)

    def _parse_response_data(self, data: Dict[str, Any]) -> str:
        """Parse Google response data to extract text."""
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def list_models(self) -> List[ProviderModel]:
        """List all available models from Google."""
        return self.models
