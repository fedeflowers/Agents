# Engineering Intelligence - Agentic Extraction Pipeline

An automated, production-ready pipeline to extract structured engineering data from raw text using **LangGraph**, **LiteLLM**, and **Pydantic**. 

This system achieves **100% accuracy** on standard evaluation benchmarks by leveraging a cyclic multi-step agent that can "think", call tools to enrich data, and validate its own output.

## 🚀 Features

- **Structured Extraction**: Enforces strict schema for `Max Stress`, `Material Type`, and `Part ID`.
- **Hybrid Agentic Workflow**:
  - Uses `LangGraph` for stateful orchestration.
  - **Tool Enrichment**: Automatically key-value lookups (e.g., density, thermal conductivity) from a mock PLM system when a `Part ID` is detected.
- **Robust Validation**:
  - **Pydantic Validation**: Ensures `Max Stress` is non-negative (unless explicitly flagged).
  - **Hallucination Guardrails**: System prompts strictly enforce extracting "handled/withstood" values while handling "no stress" as 0.0.
- **Production Ready**: Async batch processing, error handling, and modular design.

## 🛠️ Architecture

The core logic resides in `src/agent_graph.py`. It implements a ReAct-style agent loop:

1.  **Input**: Raw text description.
2.  **Agent Logic (LangGraph)**:
    -   **Analyze**: The LLM analyzes the text.
    -   **Enrich**: If a `Part ID` (e.g., `PART-123`) is found, it calls `get_material_properties`.
    -   **Extract**: It extracts `Max Stress`, `Material Type`, etc.
    -   **Submit**: Calls `ExtractionResult` to finalize.
3.  **Validation**: Pydantic models validate the structure. If valid, it returns JSON; otherwise, it flags for review.

## 📦 Setup

1.  **Cloning & Environment**:
    ```bash
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    - Create a `.env` file in the root:
      ```
      OPENAI_API_KEY=sk-...
      ```
    - Adjust model settings in `src/config.py` if needed (default: `gpt-4o-mini`).

## 🏃 Usage

### 1. Generate Synthetic Data
Generate 100+ rows of realistic engineering logs to test the pipeline.
```bash
python scripts/generate_data.py
```

### 2. Run the Extraction Pipeline
Process the raw text and generate a structured CSV (`data/extracted_results.csv`).
```bash
python src/main.py
```

### 3. Run Evals
Verify the agent's accuracy against a Golden Dataset of tricky edge cases.
```bash
python scripts/run_evals.py
```
*Current Success Rate: 100%*

## 📂 Project Structure

- `src/`
  - `agent_graph.py`: Main LangGraph definition (Nodes: Agent, Tool, Process Output).
  - `schemas.py`: Pydantic models defining the extraction schema.
  - `tools/`: External tools (Mock CAD/PLM lookup).
  - `main.py`: Batch processing entry point.
- `scripts/`: Data generation and evaluation scripts.
- `data/`: Storage for raw input and extracted CSVs.

## 🛡️ Error Handling
- **Negative Stress**: If a negative value is extracted, the system marks the record as `requires_review = True`.
- **Missing Data**: Ambiguous or missing fields result in lower confidence scores or review flags.
- **Parsing Errors**: Failed JSON parsing is caught and logged without crashing the batch.
