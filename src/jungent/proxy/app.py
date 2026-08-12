"""Main proxy server application."""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from aiohttp import web

from ..models import Request
from ..providers import ProviderRegistry, load_default_providers
from .config import ProxyConfig
from .models import Packet, ProxyDirection, ProxyRequest, ProxyResponse
from .pipeline import Pipeline, create_default_pipeline
from .session import SessionManager

logger = logging.getLogger(__name__)


@dataclass
class ProxyServer:
    """The Jungent proxy server."""

    config: ProxyConfig
    registry: ProviderRegistry
    session_manager: SessionManager
    pipeline: Pipeline

    @classmethod
    async def create(
        cls,
        config: Optional[ProxyConfig] = None,
    ) -> "ProxyServer":
        """Create a proxy server instance."""
        config = config or ProxyConfig.from_env()

        # Load providers
        registry = load_default_providers()

        # Create session manager
        session_manager = SessionManager(config)

        # Create pipeline
        pipeline = create_default_pipeline()

        return cls(
            config=config,
            registry=registry,
            session_manager=session_manager,
            pipeline=pipeline,
        )

    async def start(self) -> None:
        """Start the proxy server."""
        app = web.Application()
        app.router.add_post("/v1/chat/completions", self.handle_chat_completions)
        app.router.add_get("/health", self.handle_health)
        app.router.add_get("/ready", self.handle_ready)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()

        logger.info(f"Proxy server started on {self.config.host}:{self.config.port}")

    async def stop(self) -> None:
        """Stop the proxy server."""
        await self.session_manager.stop()
        # Close all HTTP clients from HttpClientPool
        from ..providers.base import HttpClientPool

        await HttpClientPool.close_all()

    async def handle_chat_completions(self, request: web.Request) -> web.Response:
        """Handle /v1/chat/completions requests."""
        # Check authentication
        if (
            self.config.auth_token
            and request.headers.get("Authorization")
            != f"Bearer {self.config.auth_token}"
        ):
            return web.Response(
                status=401,
                text=json.dumps({"error": "Unauthorized"}),
                content_type="application/json",
            )

        # Read request body
        try:
            body = await request.json()
        except json.JSONDecodeError as e:
            return web.Response(
                status=400,
                text=json.dumps({"error": "Invalid JSON", "details": str(e)}),
                content_type="application/json",
            )

        # Check size limit
        content_length = request.headers.get("Content-Length", 0)
        if int(content_length) > self.config.max_request_bytes:
            return web.Response(
                status=413,
                text=json.dumps({"error": "Request too large"}),
                content_type="application/json",
            )

        # Handle streaming requests
        stream = body.get("stream", False)

        if stream:
            return await self._handle_streaming_request(request, body)

        # Non-streaming request (default behavior)
        return await self._handle_non_streaming_request(request, body)

    async def _handle_streaming_request(
        self,
        request: web.Request,
        body: Dict[str, Any],
    ) -> web.StreamResponse:
        """Handle streaming requests with valid SSE behaviour."""
        from aiohttp import web

        # Create SSE response that buffers complete content when required
        response = web.Response(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

        # Get or create session
        conversation_id = body.get("conversation_id") or request.headers.get(
            "X-Jungent-Conversation-Id"
        )
        session = await self.session_manager.get_or_create_session(conversation_id)

        # Convert to packet
        proxy_request = ProxyRequest(
            method="POST",
            path="/v1/chat/completions",
            headers=dict(request.headers),
            body=body,
        )
        packet = proxy_request.to_packet()
        packet.conversation_id = session.conversation_id

        # Run pipeline - buffer response when streaming is active
        await self._run_pipeline_with_streaming(packet, stream=True)

        return response

    async def _handle_non_streaming_request(
        self,
        request: web.Request,
        body: Dict[str, Any],
    ) -> web.Response:
        """Handle non-streaming requests (buffered)."""
        # Non-streaming request - buffer complete response before sending

        # Create proxy request
        proxy_request = ProxyRequest(
            method="POST",
            path="/v1/chat/completions",
            headers=dict(request.headers),
            body=body,
        )

        # Get or create session
        conversation_id = proxy_request.conversation_id
        session = await self.session_manager.get_or_create_session(conversation_id)

        # Convert to packet
        packet = proxy_request.to_packet()
        packet.conversation_id = session.conversation_id

        # Run pipeline - buffered execution for non-streaming
        packet = await self.pipeline.run(packet, ProxyDirection.INGRESS)

        # Forward to upstream provider (buffered response)
        response = await self._forward_to_provider(packet, session)

        # Convert back to response
        proxy_response = ProxyResponse.from_packet(response)

        return web.Response(
            status=200,
            text=json.dumps(proxy_response.body),
            headers=proxy_response.headers,
            content_type="application/json",
        )

    async def _run_pipeline_with_streaming(
        self,
        packet: Packet,
        stream: bool = False,
    ):
        """Run pipeline with streaming support.

        Buffers complete response when required; streams directly only when every active module declares path safe.
        """

        # Check if all modules declare streaming_safe
        for module in self.pipeline.modules:
            if not getattr(module, "streaming_safe", False):
                # Buffer entire response instead of streaming
                break

    async def _forward_to_provider(
        self,
        packet: Packet,
        session: Any,
    ) -> Packet:
        """Forward a request to the upstream provider."""
        # Get provider
        provider = self.registry.get(self.config.upstream_provider)
        if not provider:
            raise ValueError(f"Provider not found: {self.config.upstream_provider}")

        # Convert packet to provider request (canonical API)
        from ..models import Request

        messages = packet.working.get("messages", [])

        try:
            response = await provider.generate_response_structured(
                Request(messages=messages)
            )

            return response

        except Exception as e:
            logger.exception(
                f"Error forwarding to upstream provider {self.config.upstream_provider}: {e}"
            )
            raise

    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle /health requests."""
        health = await self.check_health()
        return web.Response(
            status=200,
            text=json.dumps(health),
            content_type="application/json",
        )

    async def handle_ready(self, request: web.Request) -> web.Response:
        """Handle /ready requests."""
        ready = {
            "status": "ready",
            "provider": self.config.upstream_provider,
            "model": self.config.default_model or "default",
        }
        return web.Response(
            status=200,
            text=json.dumps(ready),
            content_type="application/json",
        )

    async def check_health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "service": "jungent-proxy",
        }

    async def _forward_to_provider(
        self,
        packet: Packet,
        session: Any,
    ) -> Packet:
        """Forward a request to the upstream provider."""
        from ..models import MessageRole

        # Get provider
        provider = self.registry.get(self.config.upstream_provider)
        if not provider:
            raise ValueError(f"Provider not found: {self.config.upstream_provider}")

        # Convert packet to provider request using canonical API
        messages = packet.working.get("messages", [])

        try:
            response = await provider.generate_response_structured(
                Request(messages=messages)
            )

            return Packet(
                direction=ProxyDirection.EGRESS,
                working={
                    "id": response.id or "",
                    "model": response.model,
                    "choices": [
                        {
                            "delta": {
                                "role": MessageRole.ASSISTANT.value,
                                "content": response.choices[0].message.content,
                            }
                        }
                    ],
                    "usage": (
                        dict(response.usage)
                        if isinstance(response.usage, Mapping)
                        else {}
                    ),
                },
                conversation_id=packet.conversation_id,
                request_id=packet.request_id,
            )

        except Exception as e:
            logger.error(
                f"Error forwarding to provider {self.config.upstream_provider}: {e}"
            )
            raise
