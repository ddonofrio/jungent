"""In-memory implementation of active memory storage."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .base import ActiveMemoryStore, MemoryEntry

logger = logging.getLogger(__name__)


class InMemoryActiveMemoryStore(ActiveMemoryStore):
    """In-memory implementation with bounded size and deterministic eviction.

    Memory is isolated by conversation ID and cleared on session expiry.
    No persistence across process restarts (MVP).
    """

    def __init__(self, max_entries_per_conversation: int = 100):
        """Initialize in-memory store.

        Args:
            max_entries_per_conversation: Maximum entries per conversation before eviction.
        """
        self.max_entries_per_conversation = max_entries_per_conversation
        # Store organized by conversation_id
        self._memory: Dict[str, List[MemoryEntry]] = {}
        self._lock = asyncio.Lock()

    async def put(
        self,
        conversation_id: str,
        entry: MemoryEntry,
    ) -> None:
        """Store a memory entry for a conversation.

        Args:
            conversation_id: The conversation to store in.
            entry: The memory entry to store.

        Raises:
            ValueError: If max_entries_per_conversation exceeded (eviction triggered).
        """
        async with self._lock:
            if conversation_id not in self._memory:
                self._memory[conversation_id] = []

            entries = self._memory[conversation_id]

            # Evict oldest entries if at capacity
            while len(entries) >= self.max_entries_per_conversation:
                oldest = entries.pop(0)
                logger.debug(
                    f"Evicted entry {oldest.key} from conversation {conversation_id}"
                )

            entries.append(entry)
            logger.debug(f"Stored entry {entry.key} in conversation {conversation_id}")

    async def get(
        self,
        conversation_id: str,
        key: str,
    ) -> Optional[MemoryEntry]:
        """Get a memory entry by key.

        Args:
            conversation_id: The conversation to search in.
            key: The entry key to look up.

        Returns:
            MemoryEntry if found, None otherwise.
        """
        async with self._lock:
            if conversation_id not in self._memory:
                return None

            for entry in self._memory[conversation_id]:
                if entry.key == key:
                    entry.last_used_at = datetime.utcnow()  # Update last used time
                    return entry
            return None

    async def list(
        self,
        conversation_id: str,
        type: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """List memory entries for a conversation.

        Args:
            conversation_id: The conversation to list.
            type: Filter by entry type (optional).

        Returns:
            List of MemoryEntry objects.
        """
        async with self._lock:
            if conversation_id not in self._memory:
                return []

            entries = self._memory[conversation_id]

            # Filter by type if specified
            if type:
                return [e for e in entries if e.type == type]

            return list(entries)

    async def delete(
        self,
        conversation_id: str,
        key: str,
    ) -> bool:
        """Delete a memory entry.

        Args:
            conversation_id: The conversation to delete from.
            key: The entry key to delete.

        Returns:
            True if deleted, False if not found.
        """
        async with self._lock:
            if conversation_id not in self._memory:
                return False

            entries = self._memory[conversation_id]

            # Find and remove the entry
            for i, entry in enumerate(entries):
                if entry.key == key:
                    del entries[i]
                    logger.debug(
                        f"Deleted entry {key} from conversation {conversation_id}"
                    )
                    return True

            return False

    async def clear(self, conversation_id: str) -> None:
        """Clear all memory for a conversation.

        Args:
            conversation_id: The conversation to clear.
        """
        async with self._lock:
            if conversation_id in self._memory:
                del self._memory[conversation_id]
                logger.info(f"Cleared all entries for conversation {conversation_id}")


class BoundedInMemoryActiveMemoryStore(InMemoryActiveMemoryStore):
    """Bounded store with deterministic eviction policy.

    Implements LRU-style eviction based on (last_used_at, created_at) when
        max_entries_per_conversation is exceeded.
    """

    def __init__(self, max_entries_per_conversation: int = 100):
        """Initialize bounded store."""
        super().__init__(max_entries_per_conversation=max_entries_per_conversation)
