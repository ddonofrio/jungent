"""Google Gemini provider implementation with structured contract."""

import os
from typing import Any, Dict, List, Optional

from ..models import Request, Response
from .base import BaseProvider, ProviderModel


class GoogleProvider(BaseProvider):
    """Provider for Google Gemini models with structured request/response."""

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
        """Generate a response using Google's API (deprecated string-based interface).

        .. deprecated::
            This method is preserved for backward compatibility but uses the structured
            provider contract internally. New code should use generate_response_structured()
            with canonical Request/Response types.
        """
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_model(model)
        self._validate_temperature(temperature)
        self._validate_max_tokens(max_tokens)
        if not self.api_key:
            raise ValueError("Google API key not provided")

        # Build request payload (same as structured version)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if tools:
            payload["tools"] = [
                {"function_declarations": [t.function.to_dict() for t in tools]}
            ]

        # Make request with retry logic
        data = await self._make_request(
            url=f"{self.api_base_url}/models/{model or 'gemini-1.5-pro'}:generateContent",
            headers={"content-type": "application/json"},
            params={"key": self.api_key},
            json_data=payload,
        )

        # Return text from parsed response (still uses _parse_response_data for backward compat)
        return self._parse_response_data(data)

    async def generate_response_structured(
        self,
        request: Request,
        **kwargs: Any,
    ) -> Response:
        """Generate a response using structured request (canonical API)."""
        if not request.messages:
            raise ValueError("Request must contain at least one message")

        if not self.api_key:
            raise ValueError("Google API key not provided")

        # Convert canonical Request to Google payload
        payload = {
            "contents": [
                {"parts": [{"text": msg.content} for msg in request.messages]}
                for _ in range(len(request.messages))
            ],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        if request.tools:
            payload["tools"] = [
                {"function_declarations": [t.function.to_dict() for t in request.tools]}
            ]

        # Make request with retry logic
        data = await self._make_request(
            url=f"{self.api_base_url}/models/{request.model or 'gemini-1.5-pro'}:generateContent",
            headers={"content-type": "application/json"},
            params={"key": self.api_key},
            json_data=payload,
        )

        # Convert to canonical Response
        return Response.from_dict(data)

    def _parse_response_data(self, data: Dict[str, Any]) -> str:
        """Parse Google response data to extract text."""
        if not isinstance(data["candidates"], list):
            raise ValueError(
                f"Unexpected response format from provider 'google': {data}"
            )

        candidate = data["candidates"][0]
        if not candidate or "content" not in candidate:
            raise ValueError(f"Missing content in candidate: {candidate}")

        parts = candidate["content"].get("parts", [])
        if not parts:
            raise ValueError(f"Missing parts in content: {parts}")

        return parts[0].get("text", "")

    def list_models(self) -> List[ProviderModel]:
        """List all available models from Google."""
        return self.models
