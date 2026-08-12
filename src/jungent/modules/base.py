"""Base classes for Hammer & Scissors modules."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..proxy.models import Action, Packet, ProxyDirection

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """Context passed to modules during pipeline execution."""

    packet: Packet
    conversation_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cancelled: bool = False

    async def cancel(self) -> None:
        """Mark the pipeline as cancelled."""
        self.cancelled = True


class Module:
    """Base class for pipeline modules."""

    name: str = "base_module"
    version: str = "1.0.0"
    supported_directions: List[ProxyDirection] = field(
        default_factory=lambda: [ProxyDirection.INGRESS, ProxyDirection.EGRESS]
    )
    streaming_safe: bool = False
    _config: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize module with configuration."""
        if config:
            self._config = config

    async def make_internal_call(
        self,
        provider_id: str,
        model_id: str,
        prompt_or_request: Any,
    ) -> Any:
        """Make an internal call to a provider without going through proxy pipeline.

        This bypasses Hammer & Scissors to prevent infinite recursion loops when
        modules need to make direct calls to providers for their own decisions.

        Args:
            provider_id: The upstream provider ID (e.g., "openai")
            model_id: The model identifier
            prompt_or_request: Either a plain string prompt or canonical Request object

        Returns:
            Response from the provider call (text, structured response, etc.)
        """
        # Implementation depends on available provider registry access
        # For MVP, this method is not used; modules should use configured internal channels
        raise NotImplementedError(
            "Internal calls require a registered provider. Configure internal channel."
        )

    @property
    def config(self) -> Dict[str, Any]:
        """Get module configuration."""
        return self._config

    async def process(
        self,
        packet: Packet,
        context: PipelineContext,
    ) -> Action:
        """Process a packet and return an action.

        Args:
            packet: The packet to process.
            context: The pipeline context.

        Returns:
            An action to apply to the packet.
        """
        raise NotImplementedError

    def to_config(self) -> "ModuleConfig":
        """Convert to module configuration."""
        return ModuleConfig(
            enabled=True,
            name=self.name,
            version=self.version,
            config=self._config.copy(),
        )

    @classmethod
    def from_config(cls, config: "ModuleConfig") -> "Module":
        """Create module from configuration."""
        instance = cls(config.config)
        instance.name = config.name
        instance.version = config.version
        return instance


@dataclass
class ModuleConfig:
    """Configuration for a specific module."""

    enabled: bool = True
    name: str = ""
    version: str = "1.0.0"
    config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "ModuleConfig":
        """Create module config from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            name=name,
            version=data.get("version", "1.0.0"),
            config=data.get("config", {}),
        )


class ModuleRegistry:
    """Registry for available modules."""

    def __init__(self):
        self._modules: Dict[str, type] = {}

    def register(self, module_class: type) -> None:
        """Register a module class."""
        self._modules[module_class.__name__.lower()] = module_class

    def get(self, name: str) -> Optional[type]:
        """Get a module class by name."""
        return self._modules.get(name.lower())

    def list_available(self) -> List[str]:
        """List all available module names."""
        return list(self._modules.keys())

    def create(
        self, name: str, config: Optional[Dict[str, Any]] = None
    ) -> Optional[Module]:
        """Create a module instance."""
        module_class = self.get(name)
        if module_class:
            return module_class(config)
        return None
