"""Core models for the proxy server."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProxyDirection(str, Enum):
    """Direction of traffic through the proxy."""

    INGRESS = "ingress"  # Client -> Proxy
    EGRESS = "egress"  # Proxy -> Upstream Provider


class PacketAction(str, Enum):
    """Action to take on a packet."""

    PASS = "pass"  # Forward unchanged
    REWRITE = "rewrite"  # Modify specific fields
    CUT = "cut"  # Remove context elements


class PacketType(str, Enum):
    """Type of packet being processed."""

    CHAT_COMPLETIONS = "chat_completions"
    EMBEDDINGS = "embeddings"
    MODELS = "models"
    UNKNOWN = "unknown"


@dataclass
class Packet:
    """A packet traversing the proxy pipeline.

    This is the central data structure for Hammer & Scissors,
    representing a request or response at any stage of processing.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    direction: ProxyDirection = ProxyDirection.INGRESS
    packet_type: PacketType = PacketType.UNKNOWN
    endpoint: str = "/v1/chat/completions"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Conversation context
    conversation_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Original and working versions
    original: Optional[Dict[str, Any]] = None
    working: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize working copy from original."""
        if self.original is None:
            self.original = self.working.copy()
        if not self.working:
            self.working = self.original.copy()

    def add_audit_event(self, event: Dict[str, Any]) -> None:
        """Add an event to the audit trail."""
        self.audit_trail.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                **event,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to dictionary."""
        return {
            "id": self.id,
            "direction": self.direction.value,
            "packet_type": self.packet_type.value,
            "endpoint": self.endpoint,
            "timestamp": self.timestamp.isoformat(),
            "conversation_id": self.conversation_id,
            "request_id": self.request_id,
            "original": self.original,
            "working": self.working,
            "metadata": self.metadata,
            "audit_trail": self.audit_trail,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Packet":
        """Create packet from dictionary."""
        direction = ProxyDirection(data.get("direction", "ingress"))
        packet_type = PacketType(data.get("packet_type", "unknown"))

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            direction=direction,
            packet_type=packet_type,
            endpoint=data.get("endpoint", "/v1/chat/completions"),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.utcnow().isoformat())
            ),
            conversation_id=data.get("conversation_id"),
            request_id=data.get("request_id", str(uuid.uuid4())),
            original=data.get("original"),
            working=data.get("working", {}),
            metadata=data.get("metadata", {}),
            audit_trail=data.get("audit_trail", []),
        )


@dataclass
class Action:
    """An action to apply to a packet."""

    action_type: PacketAction
    # For REWRITE action
    rewrite_rules: Optional[Dict[str, Any]] = None
    # For CUT action
    cut_ids: List[str] = field(default_factory=list)
    cut_replacement: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary."""
        result = {"type": self.action_type.value}
        if self.rewrite_rules:
            result["rewrite_rules"] = self.rewrite_rules
        if self.cut_ids:
            result["cut_ids"] = self.cut_ids
        if self.cut_replacement:
            result["cut_replacement"] = self.cut_replacement
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        """Create action from dictionary."""
        action_type = PacketAction(data.get("type", "pass"))

        if action_type == PacketAction.PASS:
            return cls(action_type=action_type)
        elif action_type == PacketAction.REWRITE:
            return cls(
                action_type=action_type,
                rewrite_rules=data.get("rewrite_rules"),
            )
        elif action_type == PacketAction.CUT:
            return cls(
                action_type=action_type,
                cut_ids=data.get("cut_ids", []),
                cut_replacement=data.get("cut_replacement"),
            )
        return cls(action_type=action_type)


@dataclass
class ProxyRequest:
    """A request received by the proxy."""

    method: str = "POST"
    path: str = "/v1/chat/completions"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def conversation_id(self) -> Optional[str]:
        """Get or generate conversation ID."""
        cid = self.headers.get("X-Jungent-Conversation-Id")
        if not cid and self.body and self.body.get("messages"):
            cid = self.body["messages"][-1].get("id", str(uuid.uuid4()))
        return cid

    def to_packet(self) -> Packet:
        """Convert to packet for pipeline processing."""
        return Packet(
            direction=ProxyDirection.INGRESS,
            packet_type=PacketType.CHAT_COMPLETIONS,
            endpoint=self.path,
            working=self.body.copy(),
            metadata={
                "method": self.method,
                "headers": self.headers.copy(),
            },
        )


@dataclass
class ProxyResponse:
    """A response returned from the proxy."""

    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_packet(cls, packet: Packet) -> "ProxyResponse":
        """Create response from packet."""
        return cls(
            status_code=200,
            body=packet.working.copy(),
            headers={
                "X-Jungent-Conversation-Id": packet.conversation_id or "",
                "X-Jungent-Request-Id": packet.request_id,
            },
        )


@dataclass
class ProxyError(Exception):
    """Error from the proxy server."""

    message: str
    status_code: int = 500
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        result = {"error": self.message}
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class ValidationError(ProxyError):
    """Validation error for proxy requests."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)
