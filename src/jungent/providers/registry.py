"""Registry for managing AI providers."""

from typing import Any, Dict, List, Optional, Type

from .base import BaseProvider, ProviderModel


class ProviderRegistry:
    """Registry for managing AI providers."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        self._provider_classes: Dict[str, Type[BaseProvider]] = {}
        self._config: Dict[str, Any] = {}

    def register(self, provider_id: str, provider_class: Type[BaseProvider]) -> None:
        """Register a provider class by its ID."""
        self._provider_classes[provider_id] = provider_class

    def register_instance(self, provider: BaseProvider) -> None:
        """Register a provider instance."""
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str, api_key: Optional[str] = None) -> Optional[BaseProvider]:
        """Get a provider instance by ID."""
        # Check if provider is disabled
        if provider_id in self._config.get("disabled_providers", []):
            # Remove instance if it exists
            if provider_id in self._providers:
                del self._providers[provider_id]
            return None
        
        # Check enabled_providers allowlist
        enabled = self._config.get("enabled_providers")
        if enabled is not None and provider_id not in enabled:
            # Remove instance if it exists
            if provider_id in self._providers:
                del self._providers[provider_id]
            return None

        if provider_id not in self._providers:
            if provider_id not in self._provider_classes:
                return None
            
            # Get API key from params, then from config
            provider_api_key = api_key or self._get_provider_api_key(provider_id)
            self._providers[provider_id] = self._provider_classes[provider_id](
                api_key=provider_api_key
            )
        return self._providers[provider_id]

    def get_all(self) -> List[BaseProvider]:
        """Get all registered provider instances."""
        # Return instances that have been created
        return list(self._providers.values())

    def list_available_providers(self) -> List[str]:
        """List all available provider IDs."""
        return list(self._provider_classes.keys())

    def disable_provider(self, provider_id: str) -> None:
        """Disable a provider by ID."""
        # Remove instance if it exists
        if provider_id in self._providers:
            del self._providers[provider_id]
        # Mark provider as disabled by adding to disabled list in config
        if "disabled_providers" not in self._config:
            self._config["disabled_providers"] = []
        if provider_id not in self._config["disabled_providers"]:
            self._config["disabled_providers"].append(provider_id)

    def enable_provider(self, provider_id: str, api_key: Optional[str] = None) -> Optional[BaseProvider]:
        """Enable a provider by ID."""
        if provider_id not in self._provider_classes:
            return None
        if provider_id not in self._providers:
            # Get API key from params or config
            provider_api_key = api_key or self._get_provider_api_key(provider_id)
            self._providers[provider_id] = self._provider_classes[provider_id](
                api_key=provider_api_key
            )
        return self._providers[provider_id]

    def get_enabled_providers(self) -> List[BaseProvider]:
        """Get all enabled provider instances."""
        disabled = self._config.get("disabled_providers", [])
        enabled = self._config.get("enabled_providers")
        
        return [
            provider for provider in self._providers.values()
            if provider.provider_id not in disabled
            and (enabled is None or provider.provider_id in enabled)
        ]

    def load_from_config(self, config: Dict[str, Any]) -> None:
        """Load provider configuration."""
        self._config = config

        disabled = config.get("disabled_providers", [])
        enabled = config.get("enabled_providers")

        for provider_id in disabled:
            self.disable_provider(provider_id)

        if enabled is not None:
            for provider_id in self._provider_classes:
                if provider_id not in enabled:
                    self.disable_provider(provider_id)

    def find_model(self, model_id: str) -> Optional[tuple[BaseProvider, ProviderModel]]:
        """Find a model across all enabled providers."""
        # First check already created instances
        for provider in self.get_enabled_providers():
            model = provider.get_model(model_id)
            if model:
                return (provider, model)
        
        # If not found, try to create instances for each provider class and check
        # This handles lazy loading case
        for provider_id in self._provider_classes:
            # Check if provider is disabled
            if provider_id in self._config.get("disabled_providers", []):
                continue
            # Check enabled_providers allowlist
            enabled = self._config.get("enabled_providers")
            if enabled is not None and provider_id not in enabled:
                continue
            
            # Create a temporary instance to check for the model
            provider_api_key = self._get_provider_api_key(provider_id)
            provider = self._provider_classes[provider_id](api_key=provider_api_key)
            model = provider.get_model(model_id)
            if model:
                return (provider, model)
        
        return None

    async def generate_response(
        self,
        model_id: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """Generate a response using the specified model from any provider."""
        result = self.find_model(model_id)
        if not result:
            return None

        provider, model = result
        return await provider.generate_response(
            prompt=prompt,
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _get_provider_api_key(self, provider_id: str) -> Optional[str]:
        """Get API key for a provider from config."""
        return self._config.get("providers", {}).get(provider_id, {}).get("api_key")
