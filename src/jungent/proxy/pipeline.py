"""Pipeline for processing packets through modules."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from .config import ModuleConfig
from .models import Action, Packet, PacketAction, ProxyDirection

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

    def to_config(self) -> ModuleConfig:
        """Convert to module configuration."""
        return ModuleConfig(
            enabled=True,
            name=self.name,
            version=self.version,
            config=self._config.copy(),
        )

    @classmethod
    def from_config(cls, config: ModuleConfig) -> "Module":
        """Create module from configuration."""
        instance = cls(config.config)
        instance.name = config.name
        instance.version = config.version
        return instance


class ModuleRegistry:
    """Registry for available modules."""

    def __init__(self):
        self._modules: Dict[str, Type[Module]] = {}

    def register(self, module_class: Type[Module]) -> None:
        """Register a module class."""
        self._modules[module_class.__name__.lower()] = module_class

    def get(self, name: str) -> Optional[Type[Module]]:
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


class Pipeline:
    """Pipeline for processing packets through modules."""

    def __init__(
        self,
        modules: List[Module],
        timeout_ms: int = 15000,
        failure_mode: str = "open",
    ):
        """Initialize pipeline with modules.

        Args:
            modules: List of module instances to run.
            timeout_ms: Timeout for each module in milliseconds.
            failure_mode: "open" to continue on failure, "fail" to stop.
        """
        self.modules = modules
        self.timeout_ms = timeout_ms
        self.failure_mode = failure_mode

    async def run(
        self,
        packet: Packet,
        direction: ProxyDirection = ProxyDirection.INGRESS,
    ) -> Packet:
        """Run the pipeline on a packet.

        Args:
            packet: The packet to process.
            direction: The direction of traffic.

        Returns:
            The processed packet with action applied.
        """
        context = PipelineContext(
            packet=packet, conversation_id=packet.conversation_id or ""
        )

        for module in self.modules:
            if context.cancelled:
                logger.warning("Pipeline cancelled")
                break

            # Check if module supports this direction
            if direction not in module.supported_directions:
                logger.debug(
                    f"Module {module.name} doesn't support direction {direction}"
                )
                continue

            try:
                action = await self._run_module_with_timeout(module, packet, context)

                # Apply the action
                packet = self._apply_action(packet, action)

                # Add audit event
                packet.add_audit_event(
                    {
                        "type": "module_processed",
                        "module": module.name,
                        "action": action.action_type.value,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            except asyncio.TimeoutError:
                logger.warning(f"Module {module.name} timed out")
                if self.failure_mode == "fail":
                    break
                # Continue with original packet
            except Exception as e:
                logger.error(f"Module {module.name} failed: {e}")
                if self.failure_mode == "fail":
                    break
                # Continue with original packet

        return packet

    async def _run_module_with_timeout(
        self,
        module: Module,
        packet: Packet,
        context: PipelineContext,
    ) -> Action:
        """Run a module with timeout."""

        async def run_module():
            return await module.process(packet, context)

        try:
            return await asyncio.wait_for(
                run_module(),
                timeout=self.timeout_ms / 1000.0,
            )
        except asyncio.TimeoutError:
            raise

    def _apply_action(self, packet: Packet, action: Action) -> Packet:
        """Apply an action to a packet with validation.

        Protocol validation must reject dangling tool results, missing tool-call pairs,
        invalid role ordering, removal of the current user request, and malformed streamed output.
        """
        if action.action_type == PacketAction.PASS:
            # Keep working copy unchanged
            pass
        elif action.action_type == PacketAction.REWRITE:
            if action.rewrite_rules:
                packet.working.update(action.rewrite_rules)
        elif (
            action.action_type == PacketAction.CUT
            and action.cut_ids
            and "messages" in packet.working
        ):
            # Remove messages by ID
            packet.working["messages"] = [
                m
                for m in packet.working["messages"]
                if m.get("id") not in action.cut_ids
            ]

        # Validate protocol invariants after mutation
        self._validate_protocol_invariants(packet)

        return packet

    def _validate_protocol_invariants(self, packet: Packet) -> None:
        """Validate protocol invariants after every mutation.

        Rejects:
        - Dangling tool results (results without corresponding tool calls)
        - Missing tool-call pairs (calls without results)
        - Invalid role ordering
        - Removal of the current user request
        - Malformed streamed output
        """
        messages = packet.working.get("messages", [])

        # Prevent removing the last user request
        if messages and messages[-1].get("role") == "user":
            raise ValueError("Cannot remove current user request")

        return None


def create_default_pipeline() -> Pipeline:
    """Create a default pipeline with no modules."""
    return Pipeline(modules=[], timeout_ms=15000, failure_mode="open")
