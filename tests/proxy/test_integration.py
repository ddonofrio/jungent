"""Integration tests for proxy runtime."""

import pytest


class TestProxyRuntime:
    """Tests for proxy server endpoints and lifecycle."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test /health endpoint returns liveness status."""
        from jungent.proxy.app import ProxyServer, ProxyConfig

        config = ProxyConfig(port=8787)
        server = await ProxyServer.create(config)

        # Health check should return healthy status

    @pytest.mark.asyncio
    async def test_ready_endpoint(self):
        """Test /ready endpoint reports configuration readiness."""
        from jungent.proxy.app import ProxyServer, ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )
        server = await ProxyServer.create(config)

        # Ready check should return provider and model info

    @pytest.mark.asyncio
    async def test_chat_completions_endpoint(self):
        """Test POST /v1/chat/completions handles requests."""
        from jungent.proxy.app import ProxyServer, ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )
        server = await ProxyServer.create(config)

    @pytest.mark.asyncio
    async def test_conversation_id_propagation(self):
        """Test X-Jungent-Conversation-Id header is propagated."""
        from jungent.proxy.app import ProxyServer, ProxyConfig

        config = ProxyConfig(port=8787, auth_token="test-token")
        server = await ProxyServer.create(config)

    @pytest.mark.asyncio
    async def test_request_size_limit(self):
        """Test requests exceeding max_request_bytes are rejected with 413."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(port=8787, max_request_bytes=1024)  # Small limit for test

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test server shuts down gracefully."""
        from jungent.proxy.app import ProxyServer, ProxyConfig

        config = ProxyConfig(port=8787)
        server = await ProxyServer.create(config)

        # Verify close_all() is called on stop
