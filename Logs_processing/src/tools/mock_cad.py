from typing import Dict, Optional, Any
from langchain_core.tools import tool
import random

# Internal database (could be moved to a separate store if needed)
_DATABASE = {
    "PART-123": {"density": 7.85, "thermal_conductivity": 50, "inventory": 140},
    "PART-999": {"density": 2.70, "thermal_conductivity": 205, "inventory": 20},
}

@tool
def get_material_properties(part_id: str) -> Dict[str, Any]:
    """
    Retrieves material properties (density, thermal conductivity) for a given mechanical Part ID.
    Useful for enriching extraction data when a Part ID is mentioned.
    """
    if part_id in _DATABASE:
        return _DATABASE[part_id]
    
    return {"error": f"Part '{part_id}' not found in database", "found": False}
