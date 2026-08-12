"""OpenAI provider implementation with structured model support."""

import json
import os
from typing import Any, Dict, List, Optional, AsyncIterable

import httpx

from ..models import (
    Message,
    Request,
    Response,
    ToolDefinition,
)
from .base import BaseProvider, ProviderModel


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI's GPT models with structured model support."""

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

    def to_provider_request(
        self,
        request: Request,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Convert canonical Request to OpenAI request dict."""
        payload: Dict[str, Any] = {
            "model": request.model or self.models[0].id,
            "messages": [self._message_to_openai(m) for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "n": request.n,
            "stop": request.stop,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
            "parallel_tool_calls": request.parallel_tool_calls,
        }

        if request.tools:
            payload["tools"] = [self._tool_to_openai(t) for t in request.tools]

        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice.to_dict()

        if request.response_format:
            payload["response_format"] = request.response_format

        if request.user:
            payload["user"] = request.user

        return {**payload, **kwargs}

    def _message_to_openai(self, message: Message) -> Dict[str, Any]:
        """Convert canonical Message to OpenAI message format."""
        result: Dict[str, Any] = {
            "role": message.role.value,
            "content": message.content,
        }

        if message.name:
            result["name"] = message.name

        if message.tool_call_id:
            result["tool_call_id"] = message.tool_call_id

        if message.refusal:
            result["refusal"] = message.refusal

        if message.tool_calls:
            result["tool_calls"] = [
                {"id": tc.id, "type": tc.type, "function": tc.function.to_dict()}
                for tc in message.tool_calls
                if tc.function
            ]

        return result

    def _tool_to_openai(self, tool: ToolDefinition) -> Dict[str, Any]:
        """Convert canonical ToolDefinition to OpenAI tool format."""
        if tool.function:
            return {
                "type": tool.type,
                "function": tool.function.to_dict(),
            }
        return {"type": tool.type}

    def from_provider_response(
        self,
        data: Dict[str, Any],
        **kwargs: Any,
    ) -> Response:
        """Convert OpenAI response to canonical Response."""
        response = Response.from_dict(data)
        return response

    async def generate_response_structured(
        self,
        request: Request,
        **kwargs: Any,
    ) -> Response:
        """Generate a response using structured request (canonical API)."""
        if not request.messages:
            raise ValueError("Request must contain at least one message")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        # Validate model exists before making request
        self._validate_model(request.model or self.models[0].id)

        payload = self.to_provider_request(request, **kwargs)

        data = await self._make_request(
            url=f"{self.api_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            json_data=payload,
        )

        # Convert to canonical Response using from_dict (which uses canonical models)
        return Response.from_dict(data)

    async def generate_streaming(
        self,
        request: Request,
        **kwargs: Any,
    ) -> AsyncIterable[Response]:
        """Generate a streaming response using a structured request."""
        if not request.messages:
            raise ValueError("Request must contain at least one message")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        payload = self.to_provider_request(request, stream=True, **kwargs)

        client = await self._get_http_client()
        async with client.stream(
            "POST",
            f"{self.api_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            json=payload,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        yield self._parse_stream_chunk(data)
                    except Exception:
                        continue

    def _parse_stream_chunk(self, data: str) -> Response:
        """Parse a single SSE stream chunk."""
        try:
            chunk = json.loads(data)
            return Response.from_dict(chunk)
        except json.JSONDecodeError:
            return Response()

    async def _get_http_client(self):
        """Get the HTTP client for streaming."""
        if not hasattr(self, "_client"):
            self._client = httpx.AsyncClient()
        return self._client

    def _parse_response_data(self, data: Dict[str, Any]) -> str:
        """Parse OpenAI response data to extract text."""
        return data["choices"][0]["message"]["content"]

    async def generate_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate a response using OpenAI's API (deprecated string-based interface).

        .. deprecated::
            This method is preserved for backward compatibility but uses the structured
            provider contract internally. New code should use generate_response_structured()
            with canonical Request/Response types.
        """
        from ..models import MessageRole

        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_model(model)
        self._validate_temperature(temperature)
        self._validate_max_tokens(max_tokens)

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        request = Request(
            messages=[Message(role=MessageRole.USER, content=prompt)],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            request.tools = [ToolDefinition.from_dict(t) for t in tools]

        response = await self.generate_response_structured(request)
        return response.choices[0].message.content or ""

    def list_models(self) -> List[ProviderModel]:
        """List all available models from OpenAI."""
        return self.models
