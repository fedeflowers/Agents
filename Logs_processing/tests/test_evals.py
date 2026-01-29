"""Parametrized eval test cases for extraction accuracy.

This file contains 15+ edge cases to validate the extraction pipeline.
Run with: pytest tests/test_evals.py -v
"""
import pytest

from src.agent_graph import app


# Test case definitions: (input_text, expected_fields)
EVAL_CASES = [
    # Standard cases
    pytest.param(
        "Part PART-123 is made of STEEL and handled 400 MPa stress.",
        {"part_id": "PART-123", "material_type": "STEEL", "max_stress_mpa": 400.0},
        id="standard_steel_part",
    ),
    pytest.param(
        "The aluminum housing (PART-999) failed at 250 MPa.",
        {"part_id": "PART-999", "material_type": "ALUMINUM", "max_stress_mpa": 250.0},
        id="aluminum_failure",
    ),
    pytest.param(
        "Titanium bracket withstood 800 MPa during testing.",
        {"material_type": "TITANIUM", "max_stress_mpa": 800.0},
        id="titanium_high_stress",
    ),
    
    # Zero/No stress cases
    pytest.param(
        "No stress detected on the plastic cover.",
        {"material_type": "PLASTIC", "max_stress_mpa": 0.0},
        id="no_stress_plastic",
    ),
    pytest.param(
        "The component experienced zero load during operation.",
        {"max_stress_mpa": 0.0},
        id="zero_load",
    ),
    
    # Edge cases requiring review
    pytest.param(
        "Critical error in component X. Stress level negative -50 MPa.",
        {"requires_review": True},
        id="negative_stress_review",
    ),
    pytest.param(
        "Data unclear. Possibly steel? Stress might be 100 or 200 MPa.",
        {"requires_review": True},
        id="ambiguous_data",
    ),
    
    # Composite materials
    pytest.param(
        "Carbon fiber composite panel handled peak stress of 600 MPa.",
        {"material_type": "COMPOSITE", "max_stress_mpa": 600.0},
        id="composite_material",
    ),
    
    # Missing data handling
    pytest.param(
        "Steel mounting plate for assembly line.",
        {"material_type": "STEEL"},
        id="no_stress_mentioned",
    ),
    pytest.param(
        "Component tested at 350 MPa.",
        {"max_stress_mpa": 350.0},
        id="no_material_mentioned",
    ),
    
    # Unit variations
    pytest.param(
        "Bracket experienced 0.5 GPa stress during impact testing.",
        {"max_stress_mpa": 500.0},  # 0.5 GPa = 500 MPa
        id="gpa_units",
    ),
    
    # Multiple values - should extract max
    pytest.param(
        "Stress varied from 100 MPa to 450 MPa during cycle testing.",
        {"max_stress_mpa": 450.0},
        id="stress_range_max",
    ),
    
    # Part ID variations
    pytest.param(
        "Part ID: PART-123 made of steel alloy.",
        {"part_id": "PART-123", "material_type": "STEEL"},
        id="part_id_with_colon",
    ),
    
    # Wording variations
    pytest.param(
        "Steel beam sustained 320 MPa under load.",
        {"material_type": "STEEL", "max_stress_mpa": 320.0},
        id="sustained_wording",
    ),
    pytest.param(
        "Maximum recorded stress: 275 MPa on aluminum frame.",
        {"material_type": "ALUMINUM", "max_stress_mpa": 275.0},
        id="maximum_recorded",
    ),
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestEvalCases:
    """Parametrized eval tests for extraction accuracy."""
    
    @pytest.mark.parametrize("input_text,expected", EVAL_CASES)
    async def test_extraction_case(self, input_text: str, expected: dict):
        """Test individual extraction case."""
        result = await app.ainvoke(
            {"input_text": input_text, "messages": []},
            config={"recursion_limit": 5}
        )
        
        output = result.get("final_output", {})
        
        for key, expected_value in expected.items():
            actual_value = output.get(key)
            
            # Loose comparison for stress values
            if key == "max_stress_mpa" and actual_value is not None and expected_value is not None:
                assert abs(actual_value - expected_value) < 1.0, (
                    f"Stress mismatch: expected {expected_value}, got {actual_value}"
                )
            else:
                assert actual_value == expected_value, (
                    f"Field '{key}' mismatch: expected {expected_value}, got {actual_value}"
                )


@pytest.mark.asyncio
@pytest.mark.integration  
class TestEvalSummary:
    """Summary test to run all cases and report pass rate."""
    
    async def test_overall_accuracy(self):
        """Calculate and report overall accuracy across all cases."""
        passed = 0
        failed = 0
        results = []
        
        for param in EVAL_CASES:
            input_text = param.values[0]
            expected = param.values[1]
            case_id = param.id
            
            try:
                result = await app.ainvoke(
                    {"input_text": input_text, "messages": []},
                    config={"recursion_limit": 5}
                )
                output = result.get("final_output", {})
                
                case_passed = True
                for key, exp_val in expected.items():
                    actual = output.get(key)
                    if key == "max_stress_mpa" and actual is not None and exp_val is not None:
                        if abs(actual - exp_val) >= 1.0:
                            case_passed = False
                    elif actual != exp_val:
                        case_passed = False
                
                if case_passed:
                    passed += 1
                else:
                    failed += 1
                    results.append(f"FAIL: {case_id}")
                    
            except Exception as e:
                failed += 1
                results.append(f"ERROR: {case_id} - {e}")
        
        total = passed + failed
        accuracy = passed / total if total > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"Eval Results: {passed}/{total} passed ({accuracy:.1%})")
        print(f"{'='*50}")
        
        for r in results:
            print(r)
        
        # We want at least 80% accuracy
        assert accuracy >= 0.80, f"Accuracy {accuracy:.1%} below 80% threshold"
