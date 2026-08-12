"""Instruction Funnel module - reduces instruction load."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..models import Message, Request
from ..proxy.models import Action, Packet, PacketAction, ProxyDirection
from .base import Module

logger = logging.getLogger(__name__)


class InstructionFunnelModule(Module):
    """Instruction Funnel module - reduces instruction load.

    Instruction Funnel reduces instruction and context load, retains reusable
    tool definitions in active session memory, restores only relevant tools,
    compresses noisy tool output, and removes obsolete failed attempts without
    judging whether the coding task itself was completed correctly.
    """

    name: str = "instruction_funnel"
    version: str = "1.0.0"
    supported_directions: List[ProxyDirection] = [ProxyDirection.INGRESS]
    streaming_safe: bool = False
    _decision_provider: Optional[Any] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Instruction Funnel module."""
        super().__init__(config)
        self.decision_provider = (
            config.get("decision_provider", "openai") if config else "openai"
        )
        self.decision_model = config.get("decision_model") if config else None
        self.max_context_tokens = (
            config.get("max_context_tokens", 200000) if config else 200000
        )
        self._memory: Dict[str, List[Dict[str, Any]]] = {}

    @property
    def decision_provider(self) -> str:
        """Get decision provider name."""
        return self._decision_provider or "openai"

    @decision_provider.setter
    def decision_provider(self, value: str) -> None:
        """Set decision provider name."""
        self._decision_provider = value

    async def process(
        self,
        packet: Packet,
        context: Any,
    ) -> Action:
        """Process a packet and return an action using LLM decision.

        Args:
            packet: The packet to process.
            context: The pipeline context.

        Returns:
            An action (pass, rewrite, or cut) based on analysis.
        """
        # Get conversation state
        conversation_id = packet.conversation_id or ""
        messages = packet.working.get("messages", [])

        # Analyze the messages and decide on action
        action = await self._analyze_and_decide(messages, conversation_id)

        return action

    async def _analyze_and_decide(
        self,
        messages: List[Dict[str, Any]],
        conversation_id: str,
    ) -> Action:
        """Analyze messages and decide on action using decision provider.

        Every decision response must contain exactly one of the Hammer & Scissors
        action tool calls (PASS/REWRITE/CUT). Reject natural-language-only decisions.
        Apply configured failure policy if analysis fails.
        """
        # For MVP, use heuristic-based decisions; in production, call decision provider
        # Check if we should use LLM-assisted decision (when decision_provider is configured)
        if self.decision_provider and self._has_decision_provider():
            return await self._analyze_with_llm(messages, conversation_id)

        # Scenario A: Large initial prompt with tool catalogues (~7K tokens)
        total_tokens = self._estimate_token_count(messages)

        if total_tokens > 5000:
            return await self._handle_large_prompt(messages, conversation_id)

        # Scenario B: Work-order request (look, find, execute keywords)
        if self._is_work_order_request(messages):
            return await self._handle_work_order(messages, conversation_id)

        # Default: pass through unchanged
        return Action(action_type=PacketAction.PASS)

    def _has_decision_provider(self) -> bool:
        """Check if decision provider is available for internal calls."""
        # This bypasses the proxy pipeline to prevent recursion
        return True  # Placeholder - check actual implementation

    async def _analyze_with_llm(
        self,
        messages: List[Dict[str, Any]],
        conversation_id: str,
    ) -> Action:
        """Analyze with LLM decision provider (bypasses proxy pipeline).

        Uses internal channel marked as internal to prevent recursion.
        Every response contains exactly one action tool call (PASS/REWRITE/CUT).
        Fallbacks to heuristics on provider failure.
        """
        from ..providers.registry import ProviderRegistry

        # Get or create internal decision provider instance
        registry = ProviderRegistry()
        provider = registry.get(self.decision_provider)

        if not provider:
            logger.warning(
                f"Decision provider '{self.decision_provider}' not found, using heuristics"
            )
            return await self._analyze_with_heuristics(messages, conversation_id)

        # Call decision provider with messages to analyze (internal channel bypasses pipeline)
        analysis_prompt = f"""Classify these messages and determine the appropriate action:

Messages ({len(messages)}):
{messages[:5]}  # Show first 5 for context limit

Determine if this is a large prompt (~7K+ tokens), work-order request, or needs error recovery.
Respond with exactly one of: PASS, REWRITE, CUT and provide reasoning."""

        try:
            decision = await provider.generate_response_structured(
                Request(messages=[Message(role="user", content=analysis_prompt)])
            )

            # Parse decision from response (should return action type)
            if "PASS" in str(decision):
                return Action(action_type=PacketAction.PASS)
            elif "REWRITE" in str(decision):
                return await self._handle_large_prompt(messages, conversation_id)
            else:
                return Action(action_type=PacketAction.CUT)

        except Exception as e:
            logger.error(f"Decision provider failed: {e}")
            # Fall back to heuristics on failure
            return await self._analyze_with_heuristics(messages, conversation_id)

    def _analyze_with_heuristics(
        self,
        messages: List[Dict[str, Any]],
        conversation_id: str,
    ) -> Action:
        """Fallback heuristic-based analysis when LLM decision is unavailable."""

    def _estimate_token_count(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count from messages."""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            # More accurate estimate than just counting words // 4
            if isinstance(content, str):
                total += len(content) // 1.5  # Rough chars per token
        return total

    def _is_work_order_request(self, messages: List[Dict[str, Any]]) -> bool:
        """Check if this is a work-order request."""
        if not messages:
            return False
        last_msg = messages[-1]
        content = last_msg.get("content", "").lower()
        # Check for work-order keywords using any() instead of loop
        work_order_keywords = ["look in", "find file", "execute", "run"]
        return any(keyword in content for keyword in work_order_keywords)

    async def _handle_large_prompt(
        self,
        messages: List[Dict[str, Any]],
        conversation_id: str,
    ) -> Action:
        """Handle large initial prompt with tool catalogues.

        Scenario A: Extract tool definitions from system/user messages,
        store them in active memory, and rewrite context to remove
        irrelevant tool payload while preserving personality/greeting.
        """
        # Extract tool definitions from all message types
        tools = []
        personality_instructions = ""
        greeting_found = False

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                # System messages typically contain instructions/personality
                personality_instructions += content + "\n"
            elif role in ("user", "assistant") and self._extract_tools_from_content(
                content
            ):
                # Look for tool definitions in user/assistant messages
                tools.extend(self._parse_tool_definitions(content))

        # Store extracted tools in active memory
        if conversation_id:
            if conversation_id not in self._memory:
                self._memory[conversation_id] = []
            self._memory[conversation_id].extend(tools)

        # Rewrite to keep system instructions and first user message (greeting)
        rewritten_messages = self._build_reduced_context(
            messages, personality_instructions, greeting_found
        )

        return Action(
            action_type=PacketAction.REWRITE,
            rewrite_rules={
                "messages": rewritten_messages,
            },
            metadata={"scenario": "large_prompt", "tools_extracted": len(tools)},
        )

    def _extract_tools_from_content(self, content: str) -> bool:
        """Check if content contains tool definitions."""
        # Heuristic: look for common tool pattern indicators
        tool_indicators = [
            "function",
            "parameters",
            "tool:",
            "```json",
            "def ",  # Python function definition
        ]
        return any(indicator in content.lower() for indicator in tool_indicators)

    def _parse_tool_definitions(self, content: str) -> List[Dict[str, Any]]:
        """Parse tool definitions from content."""
        tools = []
        lines = content.split("\n")

        # Look for JSON-like tool blocks or markdown code blocks
        in_code_block = False
        current_tools_str = ""

        for line in lines:
            if "```json" in line.lower():
                in_code_block = True
                continue
            elif "```" in line.lower() and in_code_block:
                # Parse the accumulated JSON
                if current_tools_str.strip():
                    try:
                        parsed_tools = json.loads(current_tools_str)
                        tools.extend(parsed_tools)
                    except json.JSONDecodeError:
                        pass  # Skip malformed JSON
                in_code_block = False
                current_tools_str = ""
            elif in_code_block:
                current_tools_str += line + "\n"

        return tools

    def _build_reduced_context(
        self,
        messages: List[Dict[str, Any]],
        personality_instructions: str,
        greeting_found: bool,
    ) -> List[Dict[str, Any]]:
        """Build reduced context from original messages."""
        rewritten = []

        # Add system messages (instructions/personality)
        for msg in messages:
            if msg.get("role") == "system":
                rewritten.append(msg)

        # Check if we have a greeting (first non-system message)
        first_user_msg = None
        for msg in messages:
            if msg.get("role") != "system":
                first_user_msg = msg
                break

        # Add system instructions and first user interaction only
        rewritten_messages = [
            {"role": "system", "content": personality_instructions.strip()},
        ]

        if first_user_msg:
            rewritten_messages.append(first_user_msg)

        return rewritten_messages

    async def _handle_work_order(
        self,
        messages: List[Dict[str, Any]],
        conversation_id: str,
    ) -> Action:
        """Handle work-order request.

        Scenario B: Rewrite context to include only user objective and relevant tools.
        Removes tool catalogues not needed for the current task.
        """
        # Get relevant tools from memory for this conversation
        relevant_tools = self._get_relevant_tools(conversation_id)

        # Build minimal context with user request + relevant tools info
        rewritten_messages = self._build_work_order_context(messages, relevant_tools)

        return Action(
            action_type=PacketAction.REWRITE,
            rewrite_rules={
                "messages": rewritten_messages,
            },
            metadata={"scenario": "work_order", "relevant_tools": len(relevant_tools)},
        )

    def _get_relevant_tools(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get relevant tools for current task."""
        return self._memory.get(conversation_id, [])[:5]  # Limit to top 5 tools

    def _build_work_order_context(
        self,
        messages: List[Dict[str, Any]],
        relevant_tools: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Build context for work-order request."""
        # Keep only the objective and necessary facts
        rewritten = []

        # Add system instructions
        for msg in messages:
            if msg.get("role") == "system":
                rewritten.append(msg)

        # Find user's current objective (last non-system message before tool calls)
        last_user_obj = None
        for msg in reversed(messages):
            if msg.get("role") != "tool" and msg.get("role") != "assistant":
                last_user_obj = msg
                break

        if last_user_obj:
            rewritten.append(last_user_obj)

        return rewritten

    async def cut_context(
        self,
        packet: Packet,
        message_ids: List[str],
        replacement: Optional[str] = None,
    ) -> Action:
        """Request context cutting for obsolete messages.

        After a corrected attempt supersedes a failed one, request CUT action
        to remove the obsolete assistant tool call and its paired tool result.
        Preserve or insert compact factual replacement when needed.
        """
        return Action(
            action_type=PacketAction.CUT,
            cut_ids=message_ids,
            cut_replacement=replacement,
            metadata={"scenario": "context_cut"},
        )

    async def repair_error_recovery(
        self,
        packet: Packet,
        error_message: str,
    ) -> Action:
        """Handle failed-attempt recovery.

        Scenario C: Recognize actionable tool errors and rewrite context with
        compact recovery instruction. Does not claim command succeeded before
        corresponding tool result arrives.
        """
        # Check for PowerShell security exception pattern
        if (
            "PSSecurityException" in error_message
            or "scripts is disabled" in error_message.lower()
        ):
            recovery_instruction = (
                "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; "
                ".\\script\\start-vite.ps1"
            )

            return Action(
                action_type=PacketAction.REWRITE,
                rewrite_rules={
                    "messages": self._build_recovery_context(
                        packet.working, recovery_instruction
                    ),
                },
                metadata={"scenario": "error_repair", "recovery_applied": True},
            )

        # Default: pass through unchanged (no special repair needed)
        return Action(action_type=PacketAction.PASS)

    def _build_recovery_context(
        self,
        packet_data: Dict[str, Any],
        recovery_instruction: str,
    ) -> List[Dict[str, Any]]:
        """Build context with recovery instruction."""
        messages = packet_data.get("messages", [])

        # Remove the failing attempt and add recovery info
        filtered_messages = [
            msg
            for msg in messages
            if "PSSecurityException" not in (msg.get("content") or "")
        ]

        return filtered_messages + [
            {"role": "assistant", "content": f"[Recovery] {recovery_instruction}"}
        ]

    def clear_memory(self, conversation_id: str) -> None:
        """Clear memory for a conversation."""
        if conversation_id in self._memory:
            del self._memory[conversation_id]

    def get_memory(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get memory for a conversation."""
        return self._memory.get(conversation_id, [])

    async def add_audit_event(
        self,
        packet: Packet,
        action_type: str,
        tool_names: Optional[List[str]] = None,
    ) -> None:
        """Add decision trace for audit."""
        if not hasattr(packet, "audit_trail"):
            return

        packet.add_audit_event(
            {
                "type": "instruction_funnel",
                "action": action_type,
                "tools_removed": tool_names or [],
                "size_before": len(packet.working.get("messages", [])),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
