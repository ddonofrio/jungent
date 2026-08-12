"""Configuration for the proxy server."""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProxyConfig:
    """Configuration for the Jungent proxy server."""

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8787
    protocol: str = "openai-chat-completions"

    # Upstream provider settings
    upstream_provider: str = "openai"
    default_model: Optional[str] = None
    upstream_model_mapping: Dict[str, str] = field(default_factory=dict)

    # Timeout and limits
    module_timeout_ms: int = 15000
    max_request_bytes: int = 4194304  # 4MB
    session_ttl_seconds: int = 3600

    # Module settings
    module_failure_mode: str = "open"  # open or fail
    modules_enabled: List[str] = field(default_factory=lambda: ["hammer_scissors"])

    # Security
    auth_token: Optional[str] = None

    # Debug
    debug: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyConfig":
        """Create config from dictionary."""
        return cls(
            host=data.get("host", "127.0.0.1"),
            port=data.get("port", 8787),
            protocol=data.get("protocol", "openai-chat-completions"),
            upstream_provider=data.get("upstream_provider", "openai"),
            default_model=data.get("default_model"),
            upstream_model_mapping=data.get("upstream_model_mapping", {}),
            module_timeout_ms=data.get("module_timeout_ms", 15000),
            max_request_bytes=data.get("max_request_bytes", 4194304),
            session_ttl_seconds=data.get("session_ttl_seconds", 3600),
            module_failure_mode=data.get("module_failure_mode", "open"),
            modules_enabled=data.get("modules_enabled", ["hammer_scissors"]),
            auth_token=data.get("auth_token"),
            debug=data.get("debug", False),
        )

    @classmethod
    def from_env(cls) -> "ProxyConfig":
        """Create config from environment variables."""
        return cls(
            host=os.environ.get("JUNGENT_PROXY_HOST", "127.0.0.1"),
            port=int(os.environ.get("JUNGENT_PROXY_PORT", "8787")),
            upstream_provider=os.environ.get("JUNGENT_UPSTREAM_PROVIDER", "openai"),
            default_model=os.environ.get("JUNGENT_DEFAULT_MODEL"),
            module_timeout_ms=int(os.environ.get("JUNGENT_MODULE_TIMEOUT_MS", "15000")),
            max_request_bytes=int(
                os.environ.get("JUNGENT_MAX_REQUEST_BYTES", "4194304")
            ),
            session_ttl_seconds=int(
                os.environ.get("JUNGENT_SESSION_TTL_SECONDS", "3600")
            ),
            module_failure_mode=os.environ.get("JUNGENT_MODULE_FAILURE_MODE", "open"),
            auth_token=os.environ.get("JUNGENT_AUTH_TOKEN"),
            debug=os.environ.get("JUNGENT_DEBUG", "false").lower() == "true",
        )


@dataclass
class ModuleConfig:
    """Configuration for a specific module."""

    enabled: bool = True
    name: str = ""
    version: str = "1.0.0"
    config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "ModuleConfig":
        """Create module config from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            name=name,
            version=data.get("version", "1.0.0"),
            config=data.get("config", {}),
        )
