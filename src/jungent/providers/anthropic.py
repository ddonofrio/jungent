"""Anthropic (Claude) provider implementation."""

import os
from typing import Any, Dict, List, Optional

from .base import BaseProvider, ProviderModel


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic's Claude models."""

    provider_id = "anthropic"
    provider_name = "Anthropic"

    def _get_default_api_base_url(self) -> str:
        return "https://api.anthropic.com/v1"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.environ.get("ANTHROPIC_API_KEY"), **kwargs)
        self.models = [
            ProviderModel(
                id="claude-3-7-sonnet-20250219",
                name="Claude 3.7 Sonnet",
                description="Most intelligent model, superior reasoning capabilities",
                context_window=200000,
                supports_vision=True,
                supports_function_calling=True,
            ),
            ProviderModel(
                id="claude-3-5-sonnet-20240620",
                name="Claude 3.5 Sonnet",
                description="Balanced model with excellent coding capabilities",
                context_window=200000,
                supports_vision=True,
                supports_function_calling=True,
            ),
            ProviderModel(
                id="claude-3-opus-20240229",
                name="Claude 3 Opus",
                description="Most capable model for complex tasks",
                context_window=200000,
                supports_vision=True,
                supports_function_calling=True,
            ),
            ProviderModel(
                id="claude-3-haiku-20240307",
                name="Claude 3 Haiku",
                description="Fastest and most compact model",
                context_window=200000,
                supports_vision=True,
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
        """Generate a response using Anthropic's API."""
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_model(model)
        self._validate_temperature(temperature)
        self._validate_max_tokens(max_tokens)
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        # Build request payload with tools support
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }

        if tools:
            # Anthropic uses tools in a different format than OpenAI
            payload["tools"] = self._convert_tools_to_anthropic_format(tools)

        # Make request with retry logic
        data = await self._make_request(
            url=f"{self.api_base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json_data=payload,
        )

        return self._parse_response_data(data)

    def _convert_tools_to_anthropic_format(
        self, tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert tools to Anthropic's format.

        Supports both OpenAI-style tools (with 'type' and 'function' keys)
        and Anthropic-style tools (with 'name', 'description', 'input_schema' keys).
        """
        anthropic_tools = []
        for tool in tools:
            # Handle OpenAI-style tools: {"type": "function", "function": {...}}
            if "function" in tool:
                func = tool.get("function", {})
                anthropic_tool: Dict[str, Any] = {
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                }
            # Handle Anthropic-style tools: {"name": "...", "description": "...", "input_schema": {...}}
            elif "name" in tool:
                anthropic_tool = {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("input_schema", {}),
                }
            else:
                # Skip invalid tool
                continue
            anthropic_tools.append(anthropic_tool)
        return anthropic_tools

    def _parse_response_data(self, data: Dict[str, Any]) -> str:
        """Parse Anthropic response data to extract text."""
        return data["content"][0]["text"]

    def list_models(self) -> List[ProviderModel]:
        """List all available models from Anthropic."""
        return self.models
