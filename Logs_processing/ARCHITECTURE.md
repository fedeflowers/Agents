# Architecture Documentation

## Overview
This solution implements an **Agentic Extraction Pipeline** designed to parse unstructured engineering text into strict `Pydantic` models. It leverages `litellm` for model agility and `langgraph` for stateful orchestration, ensuring robustness and modularity.

## Core Components

### 1. Agent Graph (`src/agent_graph.py`)
- **Structure**: A cyclic graph with Conditional Edges.
- **Components**:
  - `extract_node`: Async node calling the LLM with tool definitions.
  - `tool_node`: Executes `get_material_properties` when requested by the agent.
  - `router`: Determines if the flow should loop back (after tool use) or terminate.
- **State Management**: Uses `TypedDict` state to persist messages and intermediate outputs across graph steps.

### 2. Tooling (`src/tools/`)
- **Modular Design**: Tools are defined as standalone functions decorated with `@tool` (LangChain Core), allowing easy introspection and conversion to OpenAI schemas via `convert_to_openai_tool`.
- **Mock Implementation**: `MockCADTool` simulates low-latency lookups to a PLM system.

### 3. Data Pipeline (`src/main.py`)
- **Async Batching**: Processes text in chunks using `asyncio.gather`.
- **Error Handling**: Captures individual row failures without halting the batch, flagging them as `requires_review`.

---

## Production Readiness

### Scalability (1M+ Rows)
- **Current Bottleneck**: Sequential processing within batches is efficient, but single-machine memory/CPU limits exist.
- **Proposed Solution**:
  - **Queue System**: Push raw text to **RabbitMQ** or **Kafka**.
  - **Workers**: Deploy `src/main.py` consumers as Kubernetes Pods (scaled via KEDA based on queue depth).
  - **Caching**: Implement **Redis** semantic caching at the `litellm` layer to avoid re-processing identical phrases.

### Security & Privacy
- **Egress Control**: Run within a VPC. If using external LLMs (OpenAI), ensure Enterprise agreements for zero-data retention.
- **PII Scrubbing**: Pre-processing step to detect and redact names/emails before sending to LLM.
- **Secret Management**: API Keys injected via K8s Secrets or HashiCorp Vault (loaded via `pydantic-settings`).

### Latency Optimization
- **Streaming**: For real-time UIs, `langgraph` supports streaming tokens.
- **Model Distillation**: Use GPT-4 for "Gold Data" generation, then fine-tune a smaller model (e.g., Mistral-7B) for the specific extraction task to run locally or cheaper/faster.

## Eval Methodology
- **Reliability**: Validated via `scripts/run_evals.py` checking strict field equality against a Golden Dataset.
- **Strictness**: `Pydantic` validators ensure numerical sanity (e.g., `Max Stress > 0`).
