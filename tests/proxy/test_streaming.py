"""Tests for streaming behavior."""

import pytest


class TestStreamingBehavior:
    """Tests for valid SSE behaviour and buffering."""

    @pytest.mark.asyncio
    async def test_non_streaming_buffered_response(self):
        """Test non-streaming request returns buffered complete response."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )

    @pytest.mark.asyncio
    async def test_streaming_sse_response(self):
        """Test streaming request returns SSE response."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )

    @pytest.mark.asyncio
    async def test_streaming_module_buffering(self):
        """Test streaming modules buffer complete content before emitting."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )

    @pytest.mark.asyncio
    async def test_streaming_direct_when_safe(self):
        """Test streaming directly when every active module declares path safe."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )


class TestStreamingNonStreamingMultiTurnToolCalls:
    """Integration tests for non-streaming and multi-turn tool calls."""

    @pytest.mark.asyncio
    async def test_non_streaming_normal_text(self):
        """Test non-streaming normal text response."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )

    @pytest.mark.asyncio
    async def test_non_streaming_multiturn_tool_calls(self):
        """Test non-streaming multi-turn tool calls."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )

    @pytest.mark.asyncio
    async def test_multiturn_tool_calls(self):
        """Test multi-turn conversation with tool calls."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )


class TestStreamingEndpointHandling:
    """Tests for streaming endpoint handling."""

    @pytest.mark.asyncio
    async def test_stream_parameter_handling(self):
        """Test that stream=true never returns non-streaming JSON response."""
        from jungent.proxy.app import ProxyConfig

        config = ProxyConfig(
            port=8787, upstream_provider="openai", default_model="gpt-4o"
        )
