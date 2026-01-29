import os
import sys
import asyncio
import pandas as pd
import json
from typing import List, Dict, Any

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent_graph import app
from src.schemas import ExtractionResult

async def process_text(text: str) -> Dict[str, Any]:
    """
    Runs the agent graph for a single text input.
    """
    if not text.strip():
        return {}

    try:
        # Invoke the graph
        # config={"recursion_limit": 5} ensures we don't loop infinitely
        result = await app.ainvoke({"input_text": text, "messages": []}, config={"recursion_limit": 5})
        
        final_output = result.get("final_output", {})
        
        # Flatten for CSV
        row = {
            "raw_text": text,
            "part_name": final_output.get("part_name"),
            "max_stress_mpa": final_output.get("max_stress_mpa"),
            "material_type": final_output.get("material_type"),
            "part_id": final_output.get("part_id"),
            "requires_review": final_output.get("requires_review", False),
            "confidence_score": final_output.get("confidence_score", 0.0),
            "error": final_output.get("error")
        }
        return row
    except Exception as e:
        return {
            "raw_text": text,
            "error": str(e),
            "requires_review": True
        }

async def main():
    input_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_descriptions.txt')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'extracted_results.csv')
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(lines)} lines. Starting processing...")
    
    # Process in chunks to avoid rate limits
    chunk_size = 5 # Small batch to be safe with rate limits
    results = []
    
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i+chunk_size]
        print(f"Processing chunk {i}-{i+len(chunk)}...")
        
        batch_tasks = [process_text(text) for text in chunk]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)
        
        # Simple checkpointing
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"Saved {len(results)} rows to {output_file}")
        
    print("Processing complete.")

if __name__ == "__main__":
    asyncio.run(main())
