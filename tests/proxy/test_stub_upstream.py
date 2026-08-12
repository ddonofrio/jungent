"""Stub upstream integration tests for proxy."""

import pytest


class TestStubUpstreamIntegration:
    """Integration tests with stub upstream providers (no live credentials)."""

    @pytest.fixture
    def stub_openai_provider(self):
        """Create a stub OpenAI provider that returns synthetic responses."""

        class StubOpenAIProvider:
            def __init__(self):
                self.provider_id = "stub-openai"

            async def generate_response_structured(self, request):
                """Stub implementation returning synthetic response."""
                from jungent.models import Response, MessageRole

                # Synthetic usage stats
                usage = {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                }

                return Response(
                    id="stub-" + request.id,
                    model=request.model or "gpt-4o",
                    choices=[
                        {
                            "index": 0,
                            "message": {
                                "role": MessageRole.ASSISTANT.value,
                                "content": f"Response for: {request.messages[-1].content if request.messages else ''}",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    usage=usage,
                )

        return StubOpenAIProvider()

    @pytest.mark.asyncio
    async def test_normal_text_response(self, stub_openai_provider):
        """Test normal text response through proxy."""
        from jungent.models import Request

        request_data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        stub_provider = stub_openai_provider
        response = await stub_provider.generate_response_structured(
            Request.from_dict(request_data)
        )

    @pytest.mark.asyncio
    async def test_multiturn_tool_calls(self, stub_openai_provider):
        """Test multi-turn conversation with tool calls."""

        # First turn: user request
        messages = [
            {"role": "user", "content": "What can you do?"},
        ]

        response_data_1 = {
            "model": "gpt-4o",
            "messages": messages,
        }

        # Second turn: tool call
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "filesystem_read",
                            "arguments": '["/path/to/file"]',
                        },
                    }
                ],
            }
        )

        response_data_2 = {
            "model": "gpt-4o",
            "messages": messages,
        }

    @pytest.mark.asyncio
    async def test_tool_result_response(self, stub_openai_provider):
        """Test response after tool result arrives."""

        messages = [
            {"role": "user", "content": "Read file"},
            {
                "role": "assistant",
                "tool_calls": [{"id": "call_123", "type": "function"}],
            },
            {"role": "tool", "tool_call_id": "call_123", "content": "File contents..."},
        ]

    @pytest.mark.asyncio
    async def test_empty_content_response(self, stub_openai_provider):
        """Test handling of empty content in response."""

        request_data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": ""}],
        }

    @pytest.mark.asyncio
    async def test_structured_content_response(self, stub_openai_provider):
        """Test structured content (JSON) in response."""

        request_data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Return JSON"}],
            "response_format": {"type": "json_object"},
        }

    @pytest.mark.asyncio
    async def test_finish_reason_handling(self, stub_openai_provider):
        """Test different finish reasons."""

        request_data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Short answer"}],
            "max_tokens": 10,
        }

    @pytest.mark.asyncio
    async def test_unknown_protocol_fields(self, stub_openai_provider):
        """Test that unknown fields survive pass-through."""

        request_data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
            # Add some provider-specific extra fields
            "custom_field": "value",
            "another_custom": 123,
        }

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """Test full multi-turn conversation through proxy."""

        # Turn 1: User greeting
        messages_1 = [{"role": "user", "content": "Hello"}]

        # Turn 2: Assistant response
        messages_2 = [
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Turn 3: User follow-up
        messages_3 = messages_1 + messages_2 + [{"role": "user", "content": "Thanks"}]
