"""OpenAI provider implementation."""

import os
from typing import Any, Dict, List, Optional

from .base import BaseProvider, ProviderModel


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI's GPT models."""

    provider_id = "openai"
    provider_name = "OpenAI"

    def _get_default_api_base_url(self) -> str:
        return "https://api.openai.com/v1"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.environ.get("OPENAI_API_KEY"), **kwargs)
        self.models = [
            ProviderModel(
                id="gpt-4o",
                name="GPT-4o",
                description="Flagship multimodal model",
                context_window=128000,
                supports_vision=True,
                supports_function_calling=True,
            ),
            ProviderModel(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                description="Previous flagship model with turbo speed",
                context_window=128000,
                supports_vision=True,
                supports_function_calling=True,
            ),
            ProviderModel(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                description="Fast and efficient model",
                context_window=16385,
                supports_vision=False,
                supports_function_calling=True,
            ),
            ProviderModel(
                id="o1",
                name="o1",
                description="Reasoning model for complex tasks",
                context_window=128000,
                supports_vision=False,
                supports_function_calling=False,
            ),
            ProviderModel(
                id="o1-mini",
                name="o1 Mini",
                description="Faster reasoning model",
                context_window=128000,
                supports_vision=False,
                supports_function_calling=False,
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
        """Generate a response using OpenAI's API."""
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_model(model)
        self._validate_temperature(temperature)
        self._validate_max_tokens(max_tokens)
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        # Build request payload
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if tools:
            payload["tools"] = tools

        # Make request with retry logic
        data = await self._make_request(
            url=f"{self.api_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            json_data=payload,
        )

        return self._parse_response_data(data)

    def _parse_response_data(self, data: Dict[str, Any]) -> str:
        """Parse OpenAI response data to extract text."""
        return data["choices"][0]["message"]["content"]

    def list_models(self) -> List[ProviderModel]:
        """List all available models from OpenAI."""
        return self.models
