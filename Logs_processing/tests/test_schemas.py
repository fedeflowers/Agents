"""Unit tests for Pydantic schemas."""
import pytest
from pydantic import ValidationError

from src.schemas import ExtractionResult, MaterialType


class TestMaterialType:
    """Tests for MaterialType enum."""
    
    def test_all_materials_defined(self):
        """Ensure all expected materials are defined."""
        expected = {"STEEL", "ALUMINUM", "TITANIUM", "COMPOSITE", "PLASTIC", "UNKNOWN"}
        actual = {m.value for m in MaterialType}
        assert actual == expected
    
    def test_string_value_matches(self):
        """Material types should equal their string values."""
        assert MaterialType.STEEL == "STEEL"
        assert MaterialType.ALUMINUM == "ALUMINUM"


class TestExtractionResult:
    """Tests for ExtractionResult model."""
    
    def test_valid_full_data(self, extraction_result_valid_data):
        """Valid complete data should pass validation."""
        result = ExtractionResult(**extraction_result_valid_data)
        assert result.part_name == "Bracket Assembly"
        assert result.max_stress_mpa == 350.0
        assert result.material_type == MaterialType.STEEL
        assert result.confidence_score == 0.95
    
    def test_valid_minimal_data(self, extraction_result_minimal_data):
        """Minimal data with only required fields should pass."""
        result = ExtractionResult(**extraction_result_minimal_data)
        assert result.part_name == "Unknown Part"
        assert result.max_stress_mpa is None
        assert result.material_type == MaterialType.UNKNOWN
        assert result.requires_review is False
    
    def test_missing_required_fields(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExtractionResult()
        
        errors = exc_info.value.errors()
        error_fields = {e["loc"][0] for e in errors}
        assert "part_name" in error_fields
        assert "confidence_score" in error_fields
    
    def test_negative_stress_raises_error(self):
        """Negative stress values should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ExtractionResult(
                part_name="Test Part",
                max_stress_mpa=-100.0,
                confidence_score=0.8,
            )
        
        assert "Max stress cannot be negative" in str(exc_info.value)
    
    def test_zero_stress_is_valid(self):
        """Zero stress should be valid (for 'no stress' cases)."""
        result = ExtractionResult(
            part_name="Cover Plate",
            max_stress_mpa=0.0,
            confidence_score=0.9,
        )
        assert result.max_stress_mpa == 0.0
    
    def test_none_stress_is_valid(self):
        """None stress should be valid (when not mentioned)."""
        result = ExtractionResult(
            part_name="Unknown Component",
            max_stress_mpa=None,
            confidence_score=0.6,
        )
        assert result.max_stress_mpa is None
    
    def test_material_type_default(self):
        """Material type should default to UNKNOWN."""
        result = ExtractionResult(
            part_name="Mystery Part",
            confidence_score=0.5,
        )
        assert result.material_type == MaterialType.UNKNOWN
    
    def test_requires_review_default_false(self):
        """requires_review should default to False."""
        result = ExtractionResult(
            part_name="Normal Part",
            confidence_score=0.9,
        )
        assert result.requires_review is False
    
    def test_confidence_score_bounds(self):
        """Confidence scores at boundaries should be valid."""
        # Lower bound
        result_low = ExtractionResult(
            part_name="Low Confidence",
            confidence_score=0.0,
        )
        assert result_low.confidence_score == 0.0
        
        # Upper bound
        result_high = ExtractionResult(
            part_name="High Confidence",
            confidence_score=1.0,
        )
        assert result_high.confidence_score == 1.0
    
    def test_model_dump_json_mode(self, extraction_result_valid_data):
        """model_dump with json mode should produce serializable output."""
        result = ExtractionResult(**extraction_result_valid_data)
        dumped = result.model_dump(mode="json")
        
        assert isinstance(dumped, dict)
        assert dumped["material_type"] == "STEEL"
        assert isinstance(dumped["max_stress_mpa"], float)
    
    def test_all_material_types_accepted(self):
        """All MaterialType values should be accepted."""
        for material in MaterialType:
            result = ExtractionResult(
                part_name=f"{material.value} Part",
                material_type=material,
                confidence_score=0.8,
            )
            assert result.material_type == material
