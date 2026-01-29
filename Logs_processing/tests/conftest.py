"""Pytest configuration and shared fixtures."""
import sys
from pathlib import Path

import pytest

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_steel_text() -> str:
    """Sample text describing a steel part."""
    return "Part PART-123 is made of STEEL and handled 400 MPa stress."


@pytest.fixture
def sample_aluminum_text() -> str:
    """Sample text describing an aluminum part."""
    return "The aluminum housing (PART-999) failed at 250 MPa."


@pytest.fixture
def sample_no_stress_text() -> str:
    """Sample text with no stress mentioned."""
    return "No stress detected on the plastic cover."


@pytest.fixture
def sample_negative_stress_text() -> str:
    """Sample text with negative stress (edge case)."""
    return "Critical error in component X. Stress level negative -50 MPa."


@pytest.fixture
def sample_ambiguous_text() -> str:
    """Sample ambiguous text requiring review."""
    return "The component might be steel or possibly aluminum. No clear stress data."


@pytest.fixture
def sample_unknown_part_text() -> str:
    """Sample text with unknown part ID."""
    return "Part PART-UNKNOWN made of titanium withstood 500 MPa."


@pytest.fixture
def extraction_result_valid_data() -> dict:
    """Valid data for ExtractionResult."""
    return {
        "part_name": "Bracket Assembly",
        "max_stress_mpa": 350.0,
        "material_type": "STEEL",
        "part_id": "PART-123",
        "requires_review": False,
        "confidence_score": 0.95,
    }


@pytest.fixture
def extraction_result_minimal_data() -> dict:
    """Minimal valid data for ExtractionResult."""
    return {
        "part_name": "Unknown Part",
        "confidence_score": 0.5,
    }
