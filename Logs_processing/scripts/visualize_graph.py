import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent_graph import app

output_file = os.path.join(os.path.dirname(__file__), '..', 'graph.png')

print("Generating graph image...")
try:
    # This requires an internet connection to reach mermaid.ink api by default
    png_data = app.get_graph().draw_mermaid_png()
    with open(output_file, 'wb') as f:
        f.write(png_data)
    print(f"Graph saved to {output_file}")
except Exception as e:
    print(f"Error drawing graph (you might need internet access or extra deps): {e}")
    # Fallback to text
    print("\nMermaid Syntax:")
    print(app.get_graph().draw_mermaid())
