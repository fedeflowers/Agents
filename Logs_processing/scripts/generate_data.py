import os
import sys
import asyncio
from litellm import acompletion

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import settings

async def generate_data(n_batches: int = 5):
    filepath = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_descriptions.txt')
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    print(f"Generating data using model: {settings.MODEL_NAME}...")
    
    prompt = """
    Generate 20 diverse engineering sentences describing a part's stress analysis.
    Vary the phrasing, units (but mostly MPa), and formats.
    Include some edge cases:
    - Missing unit
    - "No significant stress"
    - Ambiguous material "It looks like steel"
    - Mentioning a Part ID like "PART-XYZ"

    Return ONLY the raw sentences, one per line. Do not include numbering.
    """

    sentences = []
    
    for i in range(n_batches):
        print(f"Batch {i+1}/{n_batches}...")
        try:
            response = await acompletion(
                model=settings.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content
            # Clean up content
            batch_sentences = [line.strip().lstrip('- ').lstrip('1234567890. ') for line in content.split('\n') if line.strip()]
            sentences.extend(batch_sentences)
        except Exception as e:
            print(f"Error in batch {i+1}: {e}")

    with open(filepath, 'w', encoding='utf-8') as f:
        for s in sentences:
            f.write(s + "\n")
            
    print(f"Generated {len(sentences)} lines to {filepath}")

if __name__ == "__main__":
    asyncio.run(generate_data(n_batches=5))
