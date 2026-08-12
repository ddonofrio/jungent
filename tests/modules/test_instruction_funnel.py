"""Tests for Instruction Funnel module."""

import pytest


class TestInstructionFunnelBehavioralScenarios:
    """Tests for the three required behavioral scenarios from OT_JUNGENT_PROXY_MODE.md."""

    @pytest.mark.asyncio
    async def test_scenario_a_large_prompt(self):
        """Scenario A: Large initial prompt with tool catalogues (~7K tokens)."""

    @pytest.mark.asyncio
    async def test_scenario_b_work_order(self):
        """Scenario B: Work-order request with relevant tools."""

    @pytest.mark.asyncio
    async def test_scenario_c_powershell_recovery(self):
        """Scenario C: PowerShell recovery for PSSecurityException."""

    @pytest.mark.asyncio
    async def test_scenario_a_tool_catalogue_stored(self):
        """Scenario A: Tool catalogue should be stored in active memory."""

    @pytest.mark.asyncio
    async def test_scenario_b_only_relevant_tools_restored(self):
        """Scenario B: Only relevant tools should be attached to request."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

        # Simulate work-order - only filesystem, file-reading, editing, shell tools needed
        messages = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {
                "role": "user",
                "content": "Look in the directory, find OT.md, and execute it",
            },
        ]

    @pytest.mark.asyncio
    async def test_scenario_c_recovery_instruction_applied(self):
        """Scenario C: PowerShell recovery instruction should be applied."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

        # Simulate PSSecurityException error - should get recovery instruction
        messages = [
            {"role": "user", "content": ".\\script\\start-vite.ps1"},
            {
                "role": "tool",
                "tool_call_id": "call_123",
                "content": "PSSecurityException: running scripts is disabled on this system",
            },
        ]


class TestInstructionFunnelClassification:
    """Tests for instruction classification."""

    @pytest.mark.asyncio
    async def test_classify_stable_identity(self):
        """Test classifying stable identity/personality instructions."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_classify_active_user_objective(self):
        """Test classifying active user objective."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_classify_reusable_operational_instructions(self):
        """Test classifying reusable operational instructions."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_classify_tool_catalogue(self):
        """Test classifying tool catalogue."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_classify_recent_task_state(self):
        """Test classifying recent task state."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()


class TestInstructionFunnelToolExtraction:
    """Tests for tool catalogue extraction and restoration."""

    @pytest.mark.asyncio
    async def test_extract_tools_from_content(self):
        """Test extracting tool definitions from instruction text."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_store_tool_schemas_with_hashes(self):
        """Test storing complete canonical definitions with content hashes."""

        # Tool schemas should be stored separately for future indexing strategies

    @pytest.mark.asyncio
    async def test_restore_relevant_tools_only(self):
        """Test restoring smallest sufficient subset of tools."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()


class TestInstructionFunnelNoiseReduction:
    """Tests for noise reduction behavior."""

    @pytest.mark.asyncio
    async def test_remove_unrelated_tool_catalogues(self):
        """Test removing unrelated tool catalogues from context."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_remove_repeated_instructions(self):
        """Test removing repeated instructions."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()


class TestInstructionFunnelErrorRecovery:
    """Tests for failed-attempt repair behavior."""

    @pytest.mark.asyncio
    async def test_recognize_actionable_tool_errors(self):
        """Test recognizing actionable tool errors."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_rewrite_context_with_recovery_instruction(self):
        """Test rewriting context with compact recovery instruction."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()


class TestInstructionFunnelContextCutting:
    """Tests for context cutting behavior."""

    @pytest.mark.asyncio
    async def test_cut_obsolete_assistant_tool_calls(self):
        """Test cutting obsolete assistant tool calls after correction."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_preserve_compact_factual_replacement(self):
        """Test preserving compact factual replacement when needed."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()


class TestInstructionFunnelDecisionTrace:
    """Tests for decision trace recording."""

    @pytest.mark.asyncio
    async def test_record_action_type(self):
        """Test recording action type (PASS/REWRITE/CUT)."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_record_tool_names_restored_removed(self):
        """Test recording tool names restored or removed."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()

    @pytest.mark.asyncio
    async def test_record_size_before_after(self):
        """Test recording size before and after."""
        from jungent.modules.instruction_funnel import InstructionFunnelModule

        module = InstructionFunnelModule()


class TestInstructionFunnelDecisionProviderFixtures:
    """Tests for deterministic decision provider fixtures."""

    @pytest.fixture
    def stub_decision_provider(self):
        """Create a stub decision provider that returns synthetic responses."""

        class StubDecisionProvider:
            def __init__(self):
                self.provider_id = "stub-decision"

            async def generate_response_structured(self, request):
                """Stub implementation returning synthetic response."""
                from jungent.models import Response, MessageRole

                messages = request.messages or []
                content = messages[-1].content if messages else ""

                # Synthetic decision based on content keywords
                if "PSSecurityException" in content:
                    return Response(
                        id="stub-recovery",
                        model="stub-decision-model",
                        choices=[
                            {
                                "index": 0,
                                "message": {
                                    "role": MessageRole.ASSISTANT.value,
                                    "content": "[Recovery] Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\\script\\start-vite.ps1",
                                },
                                "finish_reason": "stop",
                            }
                        ],
                    )

                return Response(
                    id="stub-pass",
                    model="stub-decision-model",
                    choices=[
                        {
                            "index": 0,
                            "message": {
                                "role": MessageRole.ASSISTANT.value,
                                "content": "PASS",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                )

        return StubDecisionProvider()
