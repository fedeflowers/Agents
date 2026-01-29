# Engineering Intelligence Assignment - Implementation Plan

## Overview
This document outlines the plan to build an Agentic Workflow for structured extraction of engineering data from raw text. The goal is to achieve high reliability, strict schema validation, and production readiness using modern agentic patterns.

## Technologies
- **Language**: Python 3.11
- **Validation**: `pydantic` v2
- **Config**: `pydantic-settings`
- **LLM Abstraction**: `litellm` (Unified interface for OpenAI, Anthropic, etc.)
- **Agent Orchestration**: `langgraph` (Stateful, multi-step agent workflows)
- **Testing/Evals**: `pytest` for unit tests, custom script for standard evals.
- **Mocking**: Custom mock classes for external tools.

---

## Phase 1: The Skeleton & Schema (45 mins)
**Goal**: Set up the rigid structure that ensures type safety and project configurability.

### 1. Project Initialization
- Initialize a Python project with `poetry` or `pip`.
- Set up a clean directory structure:
  ```
  .
  ├── data/
  ├── scripts/
  ├── src/
  │   ├── tools/
  │   ├── __init__.py
  │   ├── config.py
  │   └── schemas.py
  ├── tests/
  ├── .env
  └── requirements.txt
  ```

### 2. Schema Definition (`src/schemas.py`)
- Define `MaterialType` Enum (e.g., STEEL, ALUMINUM).
- Define `ExtractionResult` Pydantic model with fields:
  - `max_stress` (float, with Field description)
  - `material_type` (MaterialType)
  - `part_name` (str)
  - `requires_review` (bool) - Flag if confidence is low or data missing.
- Implement validators for "Max Stress" (e.g., must be positive).

### 3. Configuration (`src/config.py`)
- Use `BaseSettings` to load `OPENAI_API_KEY` and other model parameters from `.env`.
- Configure `litellm` settings (model aliases, fallbacks).

### 4. Mock Tool Interface (`src/tools/mock_cad.py`)
- Define `MockCADTool` class compatible with LangChain/LangGraph tool interface.
- Method `get_material_properties(part_id: str) -> dict`.
- Returns simulated JSON data to enrich the extraction.

### 5. Data Generation
- Write a script `scripts/generate_data.py` to prompt an LLM (via `litellm`) to generate 1000 rows of synthetic "raw engineering text". Save to `data/raw_descriptions.txt`.

---

## Phase 2: The Agentic Core (90 mins)
**Goal**: Build the extraction pipeline using Graph-based orchestration.

### 1. Agent Graph Design (`src/agent_graph.py`)
- **State**: Define `AgentState` (TypedDict) holding the input text, messages, and partial extraction results.
- **Nodes**:
  - `extract_fields`: LLM call using strict structured output (via `litellm` + `response_format`).
  - `validate_output`: Check Pydantic constraints.
  - `query_tool`: Call `MockCADTool` if `part_id` is found but metadata is missing.
- **Edges**:
  - Conditional edge: If `part_id` detected -> `query_tool`.
  - Conditional edge: If validation fails -> retry `extract_fields`.
- **Compile**: Build and compile the `langgraph` application.

### 2. Pipeline Script (`main.py`)
- Read from `data/raw_descriptions.txt`.
- Invoke the compiled `langgraph` app for each row.
- Process in batches.
- Output to `data/extracted_results.csv`.

---

## Phase 3: Evals & Polish (45 mins)
**Goal**: Prove reliability and document the architecture.

### 1. Evals (`scripts/run_evals.py`)
- Define a "Gold Standard" dataset.
- Metrics:
  - **Field Accuracy**: % of separate fields matching ground truth.
  - **Parsing Success Rate**: % of valid Pydantic objects created.
- Output: Print a report to console.

### 2. Documentation (`ARCHITECTURE.md`)
- **Scaling**: Discuss Redis for caching `litellm` calls, Celery/RabbitMQ for async graph execution.
- **Security**: Data sanitization, API key management.
- **Latency**: Batching vs Streaming with LangGraph.

### 3. README & Final Polish
- Instructions to install, run pipeline, and run evals.
