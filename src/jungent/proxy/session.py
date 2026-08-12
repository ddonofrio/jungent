"""Session management for proxy conversations."""

import asyncio
import contextlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .config import ProxyConfig

logger = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    """A session for a conversation."""

    conversation_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "messages": self.messages,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        """Create from dictionary."""
        return cls(
            conversation_id=data.get("conversation_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.utcnow().isoformat())
            ),
            last_activity=datetime.fromisoformat(
                data.get("last_activity", datetime.utcnow().isoformat())
            ),
            messages=data.get("messages", []),
            metadata=data.get("metadata", {}),
        )

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.last_activity + timedelta(seconds=ttl_seconds)


class SessionManager:
    """Manager for conversation sessions."""

    def __init__(self, config: ProxyConfig):
        """Initialize session manager."""
        self.config = config
        self._sessions: Dict[str, ConversationSession] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the session manager."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop the session manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

    async def get_or_create_session(
        self, conversation_id: Optional[str] = None
    ) -> ConversationSession:
        """Get or create a session for a conversation ID."""
        async with self._lock:
            if conversation_id and conversation_id in self._sessions:
                session = self._sessions[conversation_id]
                session.update_activity()
                return session

            # Create new session
            session_id = conversation_id or str(uuid.uuid4())
            session = ConversationSession(conversation_id=session_id)
            self._sessions[session_id] = session
            return session

    async def get_session(self, conversation_id: str) -> Optional[ConversationSession]:
        """Get a session by ID."""
        async with self._lock:
            if conversation_id in self._sessions:
                session = self._sessions[conversation_id]
                if session.is_expired(self.config.session_ttl_seconds):
                    del self._sessions[conversation_id]
                    return None
                session.update_activity()
                return session
            return None

    async def delete_session(self, conversation_id: str) -> bool:
        """Delete a session by ID."""
        async with self._lock:
            if conversation_id in self._sessions:
                del self._sessions[conversation_id]
                return True
            return False

    async def list_sessions(self) -> List[ConversationSession]:
        """List all active sessions."""
        async with self._lock:
            return list(self._sessions.values())

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove expired sessions."""
        async with self._lock:
            expired = [
                cid
                for cid, session in self._sessions.items()
                if session.is_expired(self.config.session_ttl_seconds)
            ]
            for cid in expired:
                del self._sessions[cid]
                logger.debug(f"Cleaned up expired session: {cid}")
