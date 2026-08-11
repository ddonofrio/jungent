"""AI Providers module for Jungent."""

from typing import Optional

from .base import BaseProvider, ProviderModel
from .registry import ProviderRegistry
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from .google import GoogleProvider
from .config import ProviderConfig

__all__ = [
    "BaseProvider",
    "ProviderModel",
    "ProviderRegistry",
    "AnthropicProvider",
    "OpenAIProvider",
    "GoogleProvider",
    "ProviderConfig",
]


def load_default_providers(config: Optional[ProviderConfig] = None) -> ProviderRegistry:
    """Load the default set of providers with optional configuration.
    
    Args:
        config: Optional ProviderConfig instance. If provided, will configure
                disabled/enabled providers and API keys from the config.
    
    Returns:
        A ProviderRegistry with default providers registered and optionally configured.
    """
    registry = ProviderRegistry()
    
    # Register default providers
    registry.register("anthropic", AnthropicProvider)
    registry.register("openai", OpenAIProvider)
    registry.register("google", GoogleProvider)
    
    # Apply config if provided
    if config is not None:
        registry.load_from_config(config.to_dict())
    
    return registry
