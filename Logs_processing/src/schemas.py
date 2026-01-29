from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class MaterialType(str, Enum):
    STEEL = "STEEL"
    ALUMINUM = "ALUMINUM"
    TITANIUM = "TITANIUM"
    COMPOSITE = "COMPOSITE"
    PLASTIC = "PLASTIC"
    UNKNOWN = "UNKNOWN"

class ExtractionResult(BaseModel):
    """
    Structured extraction from engineering text descriptions.
    """
    part_name: str = Field(..., description="The name of the mechanical part or component.")
    max_stress_mpa: Optional[float] = Field(None, description="The maximum stress value mentioned, in MPa.")
    material_type: MaterialType = Field(default=MaterialType.UNKNOWN, description="The material type inferred from the text.")
    part_id: Optional[str] = Field(None, description="Alphanumeric ID of the part if mentioned (e.g., PART-123).")
    requires_review: bool = Field(False, description="Set to True if the text is ambiguous, contradictory, or missing critical data.")
    confidence_score: float = Field(..., description="A score between 0.0 and 1.0 indicating confidence in the extraction.")

    @field_validator('max_stress_mpa')
    @classmethod
    def validate_stress(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Max stress cannot be negative.")
        return v
