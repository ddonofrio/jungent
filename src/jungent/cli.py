"""Command-line interface for Jungent."""

import argparse
import asyncio
import logging

from .proxy.app import ProxyServer
from .proxy.config import ProxyConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="jungent",
        description="Jungent - AI proxy for coding agents",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Proxy command
    proxy_parser = subparsers.add_parser(
        "proxy",
        help="Start the proxy server",
    )
    proxy_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    proxy_parser.add_argument(
        "--port",
        type=int,
        default=8787,
        help="Port to bind to (default: 8787)",
    )
    proxy_parser.add_argument(
        "--provider",
        type=str,
        default="openai",
        help="Upstream provider (default: openai)",
    )
    proxy_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Default model to use",
    )
    proxy_parser.add_argument(
        "--timeout",
        type=int,
        default=15000,
        help="Module timeout in ms (default: 15000)",
    )
    proxy_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.command == "proxy":
        return await run_proxy(args)
    else:
        parser.print_help()
        return 0


async def run_proxy(args) -> int:
    """Run the proxy server."""
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting Jungent proxy server")

    # Create config
    config = ProxyConfig(
        host=args.host,
        port=args.port,
        upstream_provider=args.provider,
        default_model=args.model,
        module_timeout_ms=args.timeout,
    )

    # Create and start server
    try:
        server = await ProxyServer.create(config)
        await server.start()

        # Keep running until cancelled
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass

        await server.stop()
        logger.info("Proxy server stopped")
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted")
        return 130
    except Exception as e:
        logger.error(f"Error starting proxy: {e}")
        return 1
