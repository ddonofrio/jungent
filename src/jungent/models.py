"""Canonical models for AI provider protocol.

These models provide a provider-neutral representation of request/response
structures that can be translated to/from provider-specific formats.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class MessageRole(str, Enum):
    """Message roles for conversation messages."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class FinishReason(str, Enum):
    """Reasons why a model request finished."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ABORTED = "aborted"
    MODEL_LIMIT = "model_limit"


@dataclass
class Message:
    """A single message in a conversation."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole = MessageRole.USER
    content: Union[str, List[Dict[str, Any]]] = ""
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: List["ToolCall"] = field(default_factory=list)
    refusal: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }
        if self.name:
            result["name"] = self.name
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.refusal:
            result["refusal"] = self.refusal
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dict."""
        role = MessageRole(data.get("role", "user"))
        content = data.get("content", "")

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            role=role,
            content=content,
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
            tool_calls=[ToolCall.from_dict(tc) for tc in data.get("tool_calls", [])],
            refusal=data.get("refusal"),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
        )


@dataclass
class ToolCall:
    """A tool call made by the model."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "function"
    function: Optional["FunctionCall"] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "created_at": self.created_at.isoformat(),
        }
        if self.function:
            result["function"] = self.function.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Create from dict."""
        function_data = data.get("function")
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=data.get("type", "function"),
            function=FunctionCall.from_dict(function_data) if function_data else None,
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
        )


@dataclass
class FunctionCall:
    """A function call within a tool call."""

    name: str
    arguments: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        return {
            "name": self.name,
            "arguments": self.arguments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FunctionCall":
        """Create from dict."""
        return cls(
            name=data.get("name", ""),
            arguments=data.get("arguments", ""),
        )


@dataclass
class ToolDefinition:
    """Definition of a tool that can be used."""

    type: str = "function"
    function: Optional["FunctionDefinition"] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {
            "type": self.type,
        }
        if self.function:
            result["function"] = self.function.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolDefinition":
        """Create from dict."""
        function_data = data.get("function")
        return cls(
            type=data.get("type", "function"),
            function=(
                FunctionDefinition.from_dict(function_data) if function_data else None
            ),
        )


@dataclass
class FunctionDefinition:
    """Definition of a function tool."""

    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    strict: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {
            "name": self.name,
        }
        if self.description:
            result["description"] = self.description
        if self.parameters:
            result["parameters"] = self.parameters
        if self.strict is not None:
            result["strict"] = self.strict
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FunctionDefinition":
        """Create from dict."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description"),
            parameters=data.get("parameters"),
            strict=data.get("strict"),
        )


@dataclass
class ToolChoice:
    """Specification for tool choice behavior."""

    type: str = "auto"  # auto, required, none
    function: Optional[str] = None  # For specific function selection

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {"type": self.type}
        if self.function:
            result["function"] = self.function
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolChoice":
        """Create from dict."""
        return cls(
            type=data.get("type", "auto"),
            function=data.get("function"),
        )


@dataclass
class Usage:
    """Token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_tokens_details: Optional[Dict[str, int]] = None
    completion_tokens_details: Optional[Dict[str, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }
        if self.prompt_tokens_details:
            result["prompt_tokens_details"] = self.prompt_tokens_details
        if self.completion_tokens_details:
            result["completion_tokens_details"] = self.completion_tokens_details
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Usage":
        """Create from dict."""
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            prompt_tokens_details=data.get("prompt_tokens_details"),
            completion_tokens_details=data.get("completion_tokens_details"),
        )


@dataclass
class Request:
    """A request to the AI provider."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    tools: List[ToolDefinition] = field(default_factory=list)
    tool_choice: Optional[ToolChoice] = None
    parallel_tool_calls: bool = True
    user: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None
    stream: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    # Provider-specific extra fields (preserve unknown fields)
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
        }
        if self.model:
            result["model"] = self.model
        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.max_tokens is not None:
            result["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            result["top_p"] = self.top_p
        if self.n is not None:
            result["n"] = self.n
        if self.stop is not None:
            result["stop"] = self.stop
        if self.presence_penalty is not None:
            result["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty is not None:
            result["frequency_penalty"] = self.frequency_penalty
        if self.tools:
            result["tools"] = [t.to_dict() for t in self.tools]
        if self.tool_choice:
            result["tool_choice"] = self.tool_choice.to_dict()
        if not self.parallel_tool_calls:
            result["parallel_tool_calls"] = self.parallel_tool_calls
        if self.user:
            result["user"] = self.user
        if self.response_format:
            result["response_format"] = self.response_format
        if self.stream:
            result["stream"] = self.stream
        if self.metadata:
            result["metadata"] = self.metadata
        # Add extra fields (provider-specific)
        result.update(self.extra_fields)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Request":
        """Create from dict."""
        # Extract known fields and extra fields
        known_fields = {
            "id",
            "messages",
            "model",
            "temperature",
            "max_tokens",
            "top_p",
            "n",
            "stop",
            "presence_penalty",
            "frequency_penalty",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
            "user",
            "response_format",
            "stream",
            "created_at",
            "metadata",
        }
        extra_fields = {k: v for k, v in data.items() if k not in known_fields}

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            model=data.get("model"),
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            top_p=data.get("top_p"),
            n=data.get("n"),
            stop=data.get("stop"),
            presence_penalty=data.get("presence_penalty"),
            frequency_penalty=data.get("frequency_penalty"),
            tools=[ToolDefinition.from_dict(t) for t in data.get("tools", [])],
            tool_choice=(
                ToolChoice.from_dict(data.get("tool_choice"))
                if data.get("tool_choice")
                else None
            ),
            parallel_tool_calls=data.get("parallel_tool_calls", True),
            user=data.get("user"),
            response_format=data.get("response_format"),
            stream=data.get("stream", False),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
            metadata=data.get("metadata"),
            extra_fields=extra_fields,
        )

    @property
    def conversation_id(self) -> Optional[str]:
        """Get conversation ID from metadata or last message."""
        if self.metadata and "conversation_id" in self.metadata:
            return self.metadata["conversation_id"]
        # Try to get from last message
        if self.messages:
            return self.messages[-1].id
        return None


@dataclass
class Response:
    """A response from the AI provider."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created: int = 0
    model: Optional[str] = None
    choices: List["Choice"] = field(default_factory=list)
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None
    # Provider-specific extra fields (preserve unknown fields)
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {
            "id": self.id,
            "created": self.created,
            "choices": [c.to_dict() for c in self.choices],
        }
        if self.model:
            result["model"] = self.model
        if self.usage:
            result["usage"] = self.usage.to_dict()
        if self.system_fingerprint:
            result["system_fingerprint"] = self.system_fingerprint
        # Add extra fields (provider-specific)
        result.update(self.extra_fields)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Response":
        """Create from dict."""
        # Extract known fields and extra fields
        known_fields = {
            "id",
            "created",
            "model",
            "choices",
            "usage",
            "system_fingerprint",
        }
        extra_fields = {k: v for k, v in data.items() if k not in known_fields}

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            created=data.get("created", 0),
            model=data.get("model"),
            choices=[Choice.from_dict(c) for c in data.get("choices", [])],
            usage=Usage.from_dict(data.get("usage")) if data.get("usage") else None,
            system_fingerprint=data.get("system_fingerprint"),
            extra_fields=extra_fields,
        )


@dataclass
class Choice:
    """A single choice in a response."""

    index: int = 0
    message: Optional[Message] = None
    finish_reason: Optional[FinishReason] = None
    logprobs: Optional[Dict[str, Any]] = None
    delta: Optional[Message] = None  # For streaming responses

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {
            "index": self.index,
        }
        if self.finish_reason:
            result["finish_reason"] = self.finish_reason.value
        if self.logprobs:
            result["logprobs"] = self.logprobs
        # Include either message or delta, not both
        if self.message and not self.delta:
            result["message"] = self.message.to_dict()
        elif self.delta and not self.message or self.delta:
            result["delta"] = self.delta.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Choice":
        """Create from dict."""
        message_data = data.get("message")
        delta_data = data.get("delta")
        finish_reason_str = data.get("finish_reason")

        return cls(
            index=data.get("index", 0),
            message=Message.from_dict(message_data) if message_data else None,
            finish_reason=(
                FinishReason(finish_reason_str) if finish_reason_str else None
            ),
            logprobs=data.get("logprobs"),
            delta=Message.from_dict(delta_data) if delta_data else None,
        )


@dataclass
class StreamingDelta:
    """A delta in a streaming response."""

    role: Optional[MessageRole] = None
    content: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    function: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API transmission."""
        result: Dict[str, Any] = {}
        if self.role:
            result["role"] = self.role.value
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.function:
            result["function"] = self.function
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamingDelta":
        """Create from dict."""
        return cls(
            role=MessageRole(data["role"]) if data.get("role") else None,
            content=data.get("content"),
            tool_calls=[ToolCall.from_dict(tc) for tc in data.get("tool_calls", [])],
            function=data.get("function"),
        )


@dataclass
class StreamingEvent:
    """A single event in a streaming response."""

    event: str = "message"
    data: Union[Response, StreamingDelta, Dict[str, Any]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for SSE transmission."""
        if isinstance(self.data, (Response, StreamingDelta)):
            return {"event": self.event, "data": self.data.to_dict()}
        else:
            return {"event": self.event, "data": self.data}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamingEvent":
        """Create from dict."""
        event_type = data.get("event", "message")
        data_obj = data.get("data", {})

        if isinstance(data_obj, dict):
            if "choices" in data_obj:
                return cls(event=event_type, data=Response.from_dict(data_obj))
            elif "role" in data_obj or "content" in data_obj:
                return cls(event=event_type, data=StreamingDelta.from_dict(data_obj))

        return cls(event=event_type, data=data_obj)
