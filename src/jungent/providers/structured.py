"""Structured provider interface with canonical model support.

This module provides a structured interface for AI providers that works
with canonical request/response models instead of raw strings.
"""

import logging
from abc import abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from ..models import (
    Message,
    Request,
    Response,
    ToolDefinition,
)
from .base import BaseProvider

logger = logging.getLogger(__name__)


class StructuredProvider(BaseProvider):
    """Base class for structured providers that use canonical models.

    This extends BaseProvider to support structured requests and responses
    using canonical models, while maintaining backward compatibility with
    the string-based generate_response method.
    """

    @abstractmethod
    async def generate_response_structured(
        self,
        request: Request,
        **kwargs: Any,
    ) -> Response:
        """Generate a response using a structured request.

        Args:
            request: The structured Request object containing messages and parameters.
            **kwargs: Additional provider-specific parameters.

        Returns:
            A structured Response object with choices, usage, etc.
        """
        pass

    @abstractmethod
    async def generate_streaming_structured(
        self,
        request: Request,
        **kwargs: Any,
    ) -> AsyncGenerator[Response, None]:
        """Generate a streaming response using a structured request.

        Args:
            request: The structured Request object containing messages and parameters.
            **kwargs: Additional provider-specific parameters.

        Yields:
            StreamingResponse objects containing deltas.
        """
        pass

    async def generate_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate a response using string inputs (backward compatibility).

        This method is deprecated in favor of generate_response_structured.
        Override this method to provide backward compatibility.

        Args:
            prompt: The prompt string.
            model: The model ID to use.
            temperature: The temperature parameter.
            max_tokens: Maximum tokens in response.
            tools: Optional list of tool definitions.

        Returns:
            The response text.
        """
        request = Request(
            messages=[Message(role="user", content=prompt)],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if tools:
            request.tools = [ToolDefinition.from_dict(t) for t in tools]

        response = await self.generate_response_structured(request)

        if response.choices and response.choices[0].message:
            return response.choices[0].message.content or ""

        return ""

    def to_provider_request(
        self,
        request: Request,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Convert canonical Request to provider-specific request dict.

        Args:
            request: The canonical Request object.
            **kwargs: Additional parameters to merge into the request.

        Returns:
            Provider-specific request dictionary.
        """
        # Subclasses should override this to convert to their format
        return request.to_dict()

    def from_provider_response(
        self,
        data: Dict[str, Any],
        **kwargs: Any,
    ) -> Response:
        """Convert provider response dict to canonical Response.

        Args:
            data: Provider-specific response dictionary.
            **kwargs: Additional parameters to merge into the response.

        Returns:
            Canonical Response object.
        """
        return Response.from_dict(data)
