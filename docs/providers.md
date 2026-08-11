# AI Providers

The AI Providers module provides a unified interface for interacting with multiple AI providers. It supports over 30 providers across different categories including cloud providers, local models, and AI gateways.

## Architecture

The providers module is built around two main components:

- **BaseProvider**: An abstract base class that defines the interface for all providers
- **ProviderRegistry**: A registry that manages multiple provider instances

## Provider Categories

### Cloud Providers
- Anthropic (Claude models)
- OpenAI (GPT-4, GPT-3.5, o1)
- Google Gemini

### Local & Self-Hosted
- Ollama
- LM Studio
- Atomic Chat

### AI Gateways
- OpenRouter
- Requesty
- DaoXE

## Getting Started

### Basic Usage

```python
from jungent.providers import ProviderRegistry, AnthropicProvider, OpenAIProvider

# Create a registry
registry = ProviderRegistry()

# Register providers
registry.register("anthropic", AnthropicProvider)
registry.register("openai", OpenAIProvider)

# Get a provider and generate a response
anthropic = registry.get("anthropic")
response = await anthropic.generate_response("Hello, world!", "claude-3-5-sonnet")
```

### Using ProviderConfig

The `ProviderConfig` class manages provider configuration including enabled/disabled providers and API keys.

```python
from jungent.providers.config import ProviderConfig

# Load configuration from file
config = ProviderConfig()

# Check if a provider is disabled
if config.is_provider_disabled("kilo"):
    print("Kilo provider is disabled")

# Disable a provider
config.disable_provider("openai")

# Enable a provider
config.enable_provider("openai")

# Set API key for a provider
config.set_api_key("anthropic", "sk-ant-...")
```

### Configuration File

Configuration is stored in a JSON file (default: `~/.jungent/config.json`):

```json
{
  "disabled_providers": ["kilo", "openai"],
  "providers": {
    "anthropic": {
      "api_key": "sk-ant-..."
    },
    "openai": {
      "api_key": "sk-..."
    }
  }
}
```

You can also use `enabled_providers` to allow only specific providers:

```json
{
  "enabled_providers": ["anthropic"]
}
```

## Provider Methods

### BaseProvider

All providers implement the following interface:

```python
class BaseProvider:
    async def generate_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> str:
        """Generate a response from the model."""

    async def list_models(self) -> List[ProviderModel]:
        """List all available models."""

    def get_model(self, model_id: str) -> Optional[ProviderModel]:
        """Get a specific model by ID."""

    def supports_model(self, model_id: str) -> bool:
        """Check if a model is supported."""
```

### ProviderRegistry

The registry manages multiple providers:

```python
class ProviderRegistry:
    def register(self, provider_id: str, provider_class: Type[BaseProvider]) -> None:
        """Register a provider class."""

    def get(self, provider_id: str) -> Optional[BaseProvider]:
        """Get a provider instance."""

    def find_model(self, model_id: str) -> Optional[tuple[BaseProvider, ProviderModel]]:
        """Find a model across all providers."""

    async def generate_response(
        self,
        model_id: str,
        prompt: str,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """Generate a response using the specified model."""
```

## Adding a New Provider

To add a new provider:

1. Create a new class that inherits from `BaseProvider`
2. Implement the required abstract methods
3. Register the provider in the registry

```python
from jungent.providers import BaseProvider

class MyProvider(BaseProvider):
    provider_id = "my-provider"
    provider_name = "My Provider"

    async def generate_response(self, prompt, model, temperature=0.7, max_tokens=None, tools=None):
        # Implementation
        pass

    async def list_models(self):
        # Implementation
        pass

# Register the provider
registry = ProviderRegistry()
registry.register("my-provider", MyProvider)
```

## Running Tests

```bash
pytest tests/providers/
```

## Environment Variables

Providers can read API keys from environment variables:

| Provider | Environment Variable |
|----------|---------------------|
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Google | `GOOGLE_API_KEY` |