"""Tool registry for the extraction pipeline.

Centralizes all available tools for easy management and extension.
"""
from src.tools.mock_cad import get_material_properties

# Registry of all available tools
# To add a new tool: 1) Create the tool function, 2) Import here, 3) Add to TOOLS list
TOOLS = [get_material_properties]

__all__ = ["TOOLS", "get_material_properties"]
