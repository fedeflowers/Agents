"""Unit tests for tool implementations."""
import pytest

from src.tools.mock_cad import get_material_properties


class TestGetMaterialProperties:
    """Tests for the get_material_properties tool."""
    
    def test_known_part_123(self):
        """PART-123 should return correct properties."""
        result = get_material_properties.invoke("PART-123")
        
        assert result["density"] == 7.85
        assert result["thermal_conductivity"] == 50
        assert result["inventory"] == 140
    
    def test_known_part_999(self):
        """PART-999 should return correct properties."""
        result = get_material_properties.invoke("PART-999")
        
        assert result["density"] == 2.70
        assert result["thermal_conductivity"] == 205
        assert result["inventory"] == 20
    
    def test_unknown_part_returns_error(self):
        """Unknown part should return error dict with helpful message."""
        result = get_material_properties.invoke("PART-UNKNOWN")
        
        assert "error" in result
        assert "PART-UNKNOWN" in result["error"]
        assert result["found"] is False
    
    def test_empty_part_id(self):
        """Empty part ID should return error."""
        result = get_material_properties.invoke("")
        
        assert "error" in result
    
    def test_tool_has_description(self):
        """Tool should have a description for LLM."""
        assert get_material_properties.description
        assert "material properties" in get_material_properties.description.lower()
    
    def test_tool_name(self):
        """Tool should have correct name."""
        assert get_material_properties.name == "get_material_properties"


class TestToolRegistry:
    """Tests for the tool registry."""
    
    def test_tools_list_not_empty(self):
        """TOOLS list should contain at least one tool."""
        from src.tools import TOOLS
        assert len(TOOLS) >= 1
    
    def test_get_material_properties_in_registry(self):
        """get_material_properties should be in TOOLS registry."""
        from src.tools import TOOLS
        tool_names = [t.name for t in TOOLS]
        assert "get_material_properties" in tool_names
    
    def test_all_tools_have_descriptions(self):
        """All registered tools should have descriptions."""
        from src.tools import TOOLS
        for tool in TOOLS:
            assert tool.description, f"Tool {tool.name} missing description"
