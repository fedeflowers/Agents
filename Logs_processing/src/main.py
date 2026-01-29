"""Main entry point for the extraction pipeline.

Provides CLI interface for batch processing of engineering text.
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import typer

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent_graph import app
from src.schemas import ExtractionResult
from src.logging_config import get_logger
from src.config import settings

logger = get_logger(__name__)

# CLI App
cli = typer.Typer(
    name="extraction-pipeline",
    help="Agentic Extraction Pipeline for engineering data.",
    add_completion=False,
)


async def process_text(text: str) -> Dict[str, Any]:
    """Run the agent graph for a single text input."""
    if not text.strip():
        return {}

    try:
        result = await app.ainvoke(
            {"input_text": text, "messages": []},
            config={"recursion_limit": 5}
        )
        
        final_output = result.get("final_output", {})
        
        return {
            "raw_text": text,
            "part_name": final_output.get("part_name"),
            "max_stress_mpa": final_output.get("max_stress_mpa"),
            "material_type": final_output.get("material_type"),
            "part_id": final_output.get("part_id"),
            "requires_review": final_output.get("requires_review", False),
            "confidence_score": final_output.get("confidence_score", 0.0),
            "error": final_output.get("error"),
        }
    except Exception as e:
        logger.error("processing_failed", text=text[:50], error=str(e))
        return {
            "raw_text": text,
            "error": str(e),
            "requires_review": True,
        }


async def run_batch(lines: List[str], chunk_size: int = 5) -> List[Dict[str, Any]]:
    """Process lines in batches with checkpointing."""
    results = []
    total = len(lines)
    
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i + chunk_size]
        logger.info("processing_chunk", start=i, end=i + len(chunk), total=total)
        
        batch_tasks = [process_text(text) for text in chunk]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)
        
    return results


@cli.command()
def process(
    input_file: Path = typer.Option(
        None,
        "--input", "-i",
        help="Input file with raw text descriptions (one per line).",
    ),
    output_file: Path = typer.Option(
        None,
        "--output", "-o",
        help="Output CSV file for extracted results.",
    ),
    chunk_size: int = typer.Option(
        5,
        "--chunk-size", "-c",
        help="Number of texts to process in parallel.",
    ),
) -> None:
    """Process raw text descriptions and extract structured data."""
    # Default paths
    base_dir = Path(__file__).parent.parent
    if input_file is None:
        input_file = base_dir / "data" / "raw_descriptions.txt"
    if output_file is None:
        output_file = base_dir / "data" / "extracted_results.csv"
    
    if not input_file.exists():
        logger.error("input_file_not_found", path=str(input_file))
        raise typer.Exit(code=1)
    
    # Read input
    lines = [
        line.strip()
        for line in input_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    logger.info("loaded_input", count=len(lines), source=str(input_file))
    
    # Process
    results = asyncio.run(run_batch(lines, chunk_size))
    
    # Save output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    logger.info("saved_output", count=len(results), destination=str(output_file))
    
    # Summary
    review_count = sum(1 for r in results if r.get("requires_review"))
    typer.echo(f"\n✅ Processed {len(results)} rows. {review_count} require review.")
    typer.echo(f"📄 Output saved to: {output_file}")


@cli.command()
def version() -> None:
    """Show version information."""
    typer.echo("Extraction Pipeline v1.0.0")
    typer.echo(f"Model: {settings.MODEL_NAME}")


if __name__ == "__main__":
    cli()
