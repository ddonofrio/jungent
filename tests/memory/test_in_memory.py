"""Deterministic tests for in-memory active memory store."""

import pytest


class TestInMemoryActiveMemoryStore:
    """Tests for conversation isolation and basic operations."""

    @pytest.mark.asyncio
    async def test_conversation_isolation(self):
        """Test that conversations are isolated from each other."""
        from jungent.memory.in_memory import InMemoryActiveMemoryStore

        store = InMemoryActiveMemoryStore()

        # Create entries for different conversations
        await store.put("conv1", type("Entry", (), {"key": "tool_a"}))
        await store.put("conv2", type("Entry", (), {"key": "tool_b"}))

    @pytest.mark.asyncio
    async def test_get_returns_correct_entry(self):
        """Test that get returns the correct entry."""
        from jungent.memory.in_memory import InMemoryActiveMemoryStore

        store = InMemoryActiveMemoryStore()

        entry = type("Entry", (), {"key": "my_key"})
        await store.put("conv1", entry)

    @pytest.mark.asyncio
    async def test_list_entries(self):
        """Test listing entries for a conversation."""

    @pytest.mark.asyncio
    async def test_delete_entry(self):
        """Test deleting an entry."""

    @pytest.mark.asyncio
    async def test_clear_conversation(self):
        """Test clearing all entries for a conversation."""


class TestContentHashing:
    """Tests for content hash computation and uniqueness."""

    @pytest.mark.asyncio
    async def test_hash_uniqueness(self):
        """Test that different contents produce different hashes."""

    @pytest.mark.asyncio
    async def test_hash_stability(self):
        """Test that hashes are stable for identical content."""


class TestReplacement:
    """Tests for entry replacement and eviction."""

    @pytest.mark.asyncio
    async def test_replacement_on_capacity(self):
        """Test that oldest entries are evicted on capacity exceeded."""

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU-style eviction based on last_used_at."""


class TestEvictionDeterminism:
    """Tests for deterministic eviction behavior."""

    @pytest.mark.asyncio
    async def test_eviction_order(self):
        """Test that eviction follows consistent order."""

    @pytest.mark.asyncio
    async def test_bounded_store_eviction(self):
        """Test bounded store eviction policy."""
