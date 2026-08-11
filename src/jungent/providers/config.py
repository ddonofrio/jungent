"""Configuration management for AI providers."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProviderConfig:
    """Configuration for AI providers."""

    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._config_path = config_path or self._get_default_config_path()
        self._load_config()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        home = Path.home()
        return str(home / ".jungent" / "config.json")

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            config_file = Path(self._config_path)
            if config_file.exists():
                with open(config_file) as f:
                    self._config = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._config = {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        config_dir = Path(self._config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w") as f:
            json.dump(self._config, f, indent=2)

    @property
    def disabled_providers(self) -> List[str]:
        """List of disabled provider IDs."""
        return self._config.get("disabled_providers", [])

    @property
    def enabled_providers(self) -> Optional[List[str]]:
        """List of enabled provider IDs, or None if all are enabled."""
        return self._config.get("enabled_providers")

    def is_provider_disabled(self, provider_id: str) -> bool:
        """Check if a provider is disabled."""
        if self.enabled_providers is not None:
            return provider_id not in self.enabled_providers
        return provider_id in self.disabled_providers

    def disable_provider(self, provider_id: str) -> None:
        """Disable a provider."""
        if "disabled_providers" not in self._config:
            self._config["disabled_providers"] = []

        if provider_id not in self._config["disabled_providers"]:
            self._config["disabled_providers"].append(provider_id)
            self._save_config()

    def enable_provider(self, provider_id: str) -> None:
        """Enable a provider."""
        if "disabled_providers" in self._config:
            self._config["disabled_providers"] = [
                p for p in self._config["disabled_providers"] if p != provider_id
            ]
            self._save_config()

    def set_api_key(self, provider_id: str, api_key: str) -> None:
        """Set API key for a provider."""
        if "providers" not in self._config:
            self._config["providers"] = {}

        self._config["providers"][provider_id] = {
            **self._config["providers"].get(provider_id, {}),
            "api_key": api_key,
        }
        self._save_config()

    def get_api_key(self, provider_id: str) -> Optional[str]:
        """Get API key for a provider."""
        return self._config.get("providers", {}).get(provider_id, {}).get("api_key")

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()
