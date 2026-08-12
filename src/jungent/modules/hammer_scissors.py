"""Hammer & Scissors interception engine module."""

import logging
from typing import Any, Dict, List, Optional

from ..proxy.models import Action, Packet, PacketAction, ProxyDirection
from .base import Module

logger = logging.getLogger(__name__)


class HammerAndScissorsModule(Module):
    """Hammer & Scissors module - deterministic interception engine.

    Hammer & Scissors is a deterministic interception engine, not an evaluator.
    It moves packets between the agent and provider, invokes installed modules
    in order, validates their requested actions, applies those actions, and
    records an audit trace.
    """

    name: str = "hammer_scissors"
    version: str = "1.0.0"
    supported_directions: List[ProxyDirection] = [
        ProxyDirection.INGRESS,
        ProxyDirection.EGRESS,
    ]
    streaming_safe: bool = False

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Hammer & Scissors module."""
        super().__init__(config)
        self.pipeline = config.get("pipeline", []) if config else []
        self.failure_mode = config.get("failure_mode", "open") if config else "open"
        self.module_timeout_ms = (
            config.get("module_timeout_ms", 15000) if config else 15000
        )

    async def process(
        self,
        packet: Packet,
        context: Any,
    ) -> Action:
        """Process a packet and return an action.

        For Hammer & Scissors, this is a pass-through that applies any
        actions from submodules.

        Args:
            packet: The packet to process.
            context: The pipeline context.

        Returns:
            An action to apply to the packet (typically pass).
        """
        # Hammer & Scissors doesn't make decisions itself
        # It just forwards packets and applies actions from modules
        return Action(action_type=PacketAction.PASS)

    def apply_action(self, packet: Packet, action: Action) -> Packet:
        """Apply an action to a packet."""
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

        return packet
