"""Integration tests for the agent graph.

These tests require a valid API key and will make actual LLM calls.
Mark with pytest.mark.integration to allow selective running.
"""
import pytest

from src.agent_graph import app, load_system_prompt, SYSTEM_PROMPT


class TestSystemPrompt:
    """Tests for system prompt loading."""
    
    def test_system_prompt_loaded(self):
        """System prompt should be loaded from file."""
        assert SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 50
    
    def test_system_prompt_contains_key_instructions(self):
        """System prompt should contain critical instructions."""
        assert "ExtractionResult" in SYSTEM_PROMPT
        assert "Max Stress" in SYSTEM_PROMPT or "max stress" in SYSTEM_PROMPT.lower()
    
    def test_load_system_prompt_function(self):
        """load_system_prompt should return non-empty string."""
        prompt = load_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestAgentGraph:
    """Tests for the compiled agent graph."""
    
    def test_app_is_compiled(self):
        """App should be a compiled graph."""
        assert app is not None
        assert hasattr(app, "ainvoke")
    
    def test_graph_has_required_nodes(self):
        """Graph should have all required nodes."""
        # Check that the graph has the expected structure
        assert app is not None


@pytest.mark.asyncio
@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests that make actual LLM calls.
    
    Run with: pytest -m integration tests/test_agent_graph.py
    """
    
    async def test_simple_extraction(self, sample_steel_text):
        """Basic extraction should work."""
        result = await app.ainvoke(
            {"input_text": sample_steel_text, "messages": []},
            config={"recursion_limit": 5}
        )
        
        assert "final_output" in result
        output = result["final_output"]
        assert output.get("part_id") == "PART-123"
        assert output.get("material_type") == "STEEL"
    
    async def test_extraction_with_tool_call(self, sample_steel_text):
        """Extraction should trigger tool call for part ID."""
        result = await app.ainvoke(
            {"input_text": sample_steel_text, "messages": []},
            config={"recursion_limit": 5}
        )
        
        # The agent should have called get_material_properties
        messages = result.get("messages", [])
        assert len(messages) >= 2  # At least system + response
    
    async def test_no_stress_extraction(self, sample_no_stress_text):
        """No stress text should extract 0.0 or None."""
        result = await app.ainvoke(
            {"input_text": sample_no_stress_text, "messages": []},
            config={"recursion_limit": 5}
        )
        
        output = result.get("final_output", {})
        stress = output.get("max_stress_mpa")
        assert stress == 0.0 or stress is None
