import asyncio
import sys
import os
import json
from tabulate import tabulate

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent_graph import app
from src.schemas import ExtractionResult

TEST_CASES = [
    {
        "input": "Part PART-123 is made of STEEL and handled 400 MPa stress.",
        "expected": {"part_id": "PART-123", "material_type": "STEEL", "max_stress_mpa": 400.0}
    },
    {
        "input": "The aluminum housing (PART-999) failed at 250 MPa.",
        "expected": {"part_id": "PART-999", "material_type": "ALUMINUM", "max_stress_mpa": 250.0}
    },
    {
        "input": "No stress detected on the plastic cover.",
        "expected": {"material_type": "PLASTIC", "max_stress_mpa": 0.0} 
        # Note: Depending on LLM logic, "No stress" might be 0 or None. 
        # We'll check loose equality.
    },
    {
        "input": "Critical error in component X. Stress level negative -50 MPa.",
        "expected": {"requires_review": True} # Should trigger validation error or review flag
    }
]

async def run_evals():
    print("Running Evals...")
    results = []
    
    for i, case in enumerate(TEST_CASES):
        input_text = case["input"]
        expected = case["expected"]
        
        print(f"Test Case {i+1}: {input_text}")
        
        try:
            # Run Agent
            graph_output = await app.ainvoke({"input_text": input_text, "messages": []})
            output = graph_output.get("final_output", {})
            
            # Check fields
            matches = []
            for k, v in expected.items():
                actual_v = output.get(k)
                
                # Simple loose comparison
                if k == "max_stress_mpa" and actual_v is not None and v is not None:
                     match = abs(actual_v - v) < 0.1
                else:
                    match = (actual_v == v)
                
                matches.append(match)
            
            success = all(matches)
            results.append({
                "Case": i+1,
                "Success": "PASS" if success else "FAIL",
                "Expected": str(expected),
                "Actual": str({k: output.get(k) for k in expected}),
                "Full Output": str(output)
            })
            
        except Exception as e:
            results.append({
                "Case": i+1,
                "Success": "ERROR",
                "Expected": str(expected),
                "Actual": str(e)
            })

    print("\n" + tabulate(results, headers="keys", tablefmt="grid"))
    
    pass_rate = len([r for r in results if r["Success"] == "PASS"]) / len(results)
    print(f"\nSuccess Rate: {pass_rate:.1%}")

if __name__ == "__main__":
    asyncio.run(run_evals())
