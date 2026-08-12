"""Base classes for AI Providers."""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ProviderModel:
    """Represents a model offered by an AI provider."""

    def __init__(
        self,
        id: str,
        name: str,
        description: Optional[str] = None,
        context_window: Optional[int] = None,
        supports_vision: bool = False,
        supports_function_calling: bool = False,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.context_window = context_window
        self.supports_vision = supports_vision
        self.supports_function_calling = supports_function_calling


class HttpClientPool:
    """Shared HTTP client pool for efficient connection management."""

    _clients: Dict[int, httpx.AsyncClient] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """Get or create an HTTP client for this event loop."""
        loop_id = id(asyncio.get_event_loop())

        async with cls._lock:
            if loop_id not in cls._clients:
                cls._clients[loop_id] = httpx.AsyncClient()
                logger.info(f"Created HTTP client for event loop {loop_id}")
            return cls._clients[loop_id]

    @classmethod
    async def close_all(cls) -> None:
        """Close all HTTP clients."""
        async with cls._lock:
            for client in cls._clients.values():
                await client.aclose()
            cls._clients.clear()
            logger.info("Closed all HTTP clients")

    @classmethod
    @asynccontextmanager
    async def client_context(cls):
        """Context manager for getting and automatically closing an HTTP client."""
        client = await cls.get_client()
        try:
            yield client
        finally:
            # Note: we don't close the client here since it's shared
            # The client is closed by close_all() which should be called at shutdown
            pass


class BaseProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key or kwargs.get("api_key")
        self.config = kwargs
        self.models: List[ProviderModel] = []
        self.api_base_url = kwargs.get(
            "api_base_url", self._get_default_api_base_url()
        )
        self.timeout = kwargs.get("timeout", 30.0)
        self.max_retries = kwargs.get("max_retries", 3)
        self.retry_delay = kwargs.get("retry_delay", 1.0)

        # Validate API key is set only if not in test mode
        # Allow None for testing purposes, but warn users
        if not self.api_key and not kwargs.get("_skip_api_key_validation", False):
            logger.warning(
                f"API key not provided for {self.provider_name}. "
                f"Set the API key or {self._get_env_var_name()} environment variable. "
                f"Requests will fail without a valid API key."
            )

    def _get_env_var_name(self) -> str:
        """Get the environment variable name for this provider's API key."""
        return f"{self.provider_id.upper()}_API_KEY"

    def _get_default_api_base_url(self) -> str:
        """Get the default API base URL for this provider."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _get_default_api_base_url()"
        )

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name for this provider."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate a response from the provider's model."""
        pass

    @abstractmethod
    def list_models(self) -> List[ProviderModel]:
        """List all available models from this provider."""
        pass

    def get_model(self, model_id: str) -> Optional[ProviderModel]:
        """Get a specific model by ID."""
        for model in self.models:
            if model.id == model_id:
                return model
        return None

    def supports_model(self, model_id: str) -> bool:
        """Check if this provider supports a given model."""
        return self.get_model(model_id) is not None

    async def check_health(self) -> Dict[str, Any]:
        """Check if the provider is healthy and API key is valid.
        
        Returns a dict with 'healthy' boolean and optional 'error' message.
        """
        try:
            # Try a minimal request - just list models to verify connectivity
            models = self.list_models()
            if not models:
                return {"healthy": True, "error": None}
            return {"healthy": True, "error": None}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def is_api_key_valid(self) -> bool:
        """Check if the API key is valid by making a test request."""
        try:
            # For providers with a models endpoint, we can use that
            # Otherwise, rely on validation
            self.list_models()
            return True
        except Exception:
            return False

    async def _make_request(
        self,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        client = await HttpClientPool.get_client()

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Making {method} request to {url} (attempt {attempt + 1}/{self.max_retries})"
                )
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < self.max_retries - 1:
                    # Rate limit - wait and retry
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise
            except httpx.RequestError as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Request failed, retrying in {delay}s: {e} (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                raise

        raise RuntimeError("Unexpected retry loop exit")

    def _validate_model(self, model_id: str) -> ProviderModel:
        """Validate that a model ID exists for this provider."""
        model = self.get_model(model_id)
        if not model:
            raise ValueError(
                f"Model '{model_id}' not found for provider '{self.provider_id}'. "
                f"Available models: {[m.id for m in self.models]}"
            )
        return model

    def _validate_temperature(self, temperature: float) -> None:
        """Validate temperature parameter is in valid range."""
        if not 0 <= temperature <= 2:
            raise ValueError(
                f"Temperature must be between 0 and 2, got {temperature}"
            )

    def _validate_max_tokens(self, max_tokens: Optional[int]) -> None:
        """Validate max_tokens parameter if provided."""
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {max_tokens}")

    def _validate_prompt(self, prompt: str) -> None:
        """Validate prompt parameter."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

    async def _safe_parse_response(self, data: Dict[str, Any]) -> str:
        """Safely parse response data with validation."""
        try:
            return self._parse_response_data(data)
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(
                f"Unexpected response format from provider '{self.provider_id}': {data}"
            ) from e

    def _parse_response_data(self, data: Dict[str, Any]) -> str:
        """Parse the response data to extract text. Must be implemented by subclasses."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _parse_response_data()"
        )


# Deterministic fake providers for testing (Work Order 320 requirement)
class MockProvider1(BaseProvider):
    """Simple mock provider for enable/disable edge case tests."""

    @property
    def provider_id(self) -> str:
        return "mock-1"

    @property
    def provider_name(self) -> str:
        return "Mock Provider 1"

    def _get_default_api_base_url(self) -> str:
        return "https://api.mock.com"

    async def generate_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        return "Mock response"

    def list_models(self) -> List[ProviderModel]:
        return [ProviderModel(id="mock-model-1", name="Mock Model 1")]

    def _parse_response_data(self, data: Dict[str, Any]) -> str:
        return data.get("content", "")[0].get("text", "") if isinstance(data.get("content"), list) else ""


class MockProvider2(MockProvider1):
    """Second variant of mock provider for different test scenarios."""

    @property
    def provider_id(self) -> str:
        return "mock-2"

    @property
    def provider_name(self) -> str:
        return "Mock Provider 2"

