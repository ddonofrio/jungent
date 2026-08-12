"""Active memory storage interface."""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry."""

    type: str
    key: str
    content_hash: str
    payload: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)
    relevance: float = 1.0
    conversation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "key": self.key,
            "content_hash": self.content_hash,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat(),
            "relevance": self.relevance,
            "conversation_id": self.conversation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            type=data.get("type", ""),
            key=data.get("key", ""),
            content_hash=data.get("content_hash", ""),
            payload=data.get("payload", {}),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.utcnow().isoformat())
            ),
            last_used_at=datetime.fromisoformat(
                data.get("last_used_at", datetime.utcnow().isoformat())
            ),
            relevance=data.get("relevance", 1.0),
            conversation_id=data.get("conversation_id"),
        )


class ActiveMemoryStore:
    """Interface for active memory storage."""

    async def put(
        self,
        conversation_id: str,
        entry: MemoryEntry,
    ) -> None:
        """Store a memory entry for a conversation."""
        raise NotImplementedError

    async def get(
        self,
        conversation_id: str,
        key: str,
    ) -> Optional[MemoryEntry]:
        """Get a memory entry by key."""
        raise NotImplementedError

    async def list(
        self,
        conversation_id: str,
        type: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """List memory entries for a conversation."""
        raise NotImplementedError

    async def delete(
        self,
        conversation_id: str,
        key: str,
    ) -> bool:
        """Delete a memory entry."""
        raise NotImplementedError

    async def clear(self, conversation_id: str) -> None:
        """Clear all memory for a conversation."""
        raise NotImplementedError

    @staticmethod
    def compute_hash(payload: Dict[str, Any]) -> str:
        """Compute content hash for a payload."""
        content = str(payload)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
