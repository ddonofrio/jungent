# AI Providers

The AI Providers module provides a unified interface for interacting with multiple AI providers. It currently supports three providers: OpenAI, Anthropic (Claude), and Google Gemini. Additional providers can be added by inheriting from `BaseProvider`.

## Architecture

The providers module is built around two main components:

- **BaseProvider**: An abstract base class that defines the interface for all providers
- **ProviderRegistry**: A registry that manages multiple provider instances

## Supported Providers

### Implemented Adapters

1. **OpenAI** - GPT models (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, o1, o1-mini)
2. **Anthropic** - Claude models (claude-3-7-sonnet, claude-3-5-sonnet, claude-3-opus, claude-3-haiku)
3. **Google Gemini** - gemini models (gemini-1.5-pro, gemini-1.5-flash, gemini-1.0-pro)

### Provider Categories

#### Cloud Providers
- Anthropic (Claude models)
- OpenAI (GPT models)
- Google Gemini

#### AI Gateways
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
    # Synchronous method - list models from hardcoded catalog or API call
    def list_models(self) -> List[ProviderModel]:
        """List all available models."""

    # Synchronous method - get a specific model by ID
    def get_model(self, model_id: str) -> Optional[ProviderModel]:
        """Get a specific model by ID."""

    # Synchronous method - check if a model is supported
    def supports_model(self, model_id: str) -> bool:
        """Check if a model is supported."""

    # Asynchronous method - generate response using structured API
    async def generate_response_structured(
        self,
        request: Request,
        **kwargs: Any,
    ) -> Response:
        """Generate a response using the structured provider contract."""

    # Legacy synchronous string-based interface (deprecated but preserved)
    async def generate_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> str:
        """Generate a response from the model (legacy string API)."""
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

## Interface Notes

- `list_models()` is **synchronous** - models are loaded from a catalog or cached API response
- `generate_response_structured()` uses the canonical `Request/Response` types for all providers
- `generate_response()` (string-based) is deprecated but preserved for backward compatibility
- All provider-specific translation happens inside adapter implementations
