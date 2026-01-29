"""Agent graph definition for the extraction pipeline.

This module implements a LangGraph-based agentic workflow for extracting
structured engineering data from unstructured text.
"""
import json
from pathlib import Path
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_litellm import ChatLiteLLM
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.schemas import ExtractionResult
from src.config import settings
from src.tools import TOOLS, get_material_properties
from src.logging_config import get_logger

# --- Logger ---
logger = get_logger(__name__)

# --- Load System Prompt ---
PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "extraction_prompt.txt"


def load_system_prompt() -> str:
    """Load the system prompt from external file."""
    try:
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.warning("system_prompt_not_found", path=str(SYSTEM_PROMPT_PATH))
        return "You are an expert engineering data extractor. Extract structured data from the text."


SYSTEM_PROMPT = load_system_prompt()

# --- Setup Model ---
llm = ChatLiteLLM(model=settings.MODEL_NAME, temperature=0)

# --- Bind Tools ---
# We use the Pydantic model as a structured output tool alongside the registry tools
tools = TOOLS + [ExtractionResult]
llm_with_tools = llm.bind_tools(tools)


# --- Graph State ---
class AgentState(TypedDict):
    """State container for the agent graph."""
    input_text: str
    messages: Annotated[List[BaseMessage], add_messages]
    final_output: Optional[Dict[str, Any]]


# --- Nodes ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=lambda retry_state: logger.warning(
        "llm_retry",
        attempt=retry_state.attempt_number,
        wait=retry_state.next_action.sleep
    )
)
async def _invoke_llm(messages: List[BaseMessage]) -> Any:
    """Invoke the LLM with retry logic for transient failures."""
    return await llm_with_tools.ainvoke(messages)


async def agent_node(state: AgentState) -> Dict[str, Any]:
    """Main agent node that invokes the LLM."""
    messages = state["messages"]
    
    # Add system prompt if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        sys_msg = SystemMessage(content=SYSTEM_PROMPT)
        messages = [sys_msg] + messages

    # Add input text if this is the start
    if len(messages) == 1 and isinstance(messages[0], SystemMessage):
        messages.append(HumanMessage(content=f"Analyze this text: {state['input_text']}"))
        logger.debug("agent_processing", input_text=state['input_text'][:100])

    response = await _invoke_llm(messages)
    
    logger.debug(
        "agent_response",
        has_tool_calls=bool(getattr(response, 'tool_calls', None))
    )
    
    return {"messages": [response]}


def router(state: AgentState) -> Literal["tools", "process_output", "end"]:
    """Route to next node based on LLM response."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        logger.debug("router_decision", next_node="end", reason="no_tool_calls")
        return "end"
    
    # Check if it called the extraction tool
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "ExtractionResult":
            logger.debug("router_decision", next_node="process_output")
            return "process_output"
    
    logger.debug("router_decision", next_node="tools")
    return "tools"


async def process_output_node(state: AgentState) -> Dict[str, Any]:
    """Extract and validate the structured data from the tool call."""
    messages = state["messages"]
    last_message = messages[-1]
    
    final_data = {}
    
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "ExtractionResult":
            try:
                data = tool_call["args"]
                validated = ExtractionResult(**data)
                final_data = validated.model_dump(mode='json')
                logger.info(
                    "extraction_success",
                    part_name=final_data.get("part_name"),
                    confidence=final_data.get("confidence_score")
                )
            except Exception as e:
                final_data = tool_call["args"]
                final_data["requires_review"] = True
                final_data["error"] = str(e)
                logger.warning("extraction_validation_failed", error=str(e))
            break
    
    return {"final_output": final_data}


# --- Tool Node ---
tool_node = ToolNode([get_material_properties])

# --- Build Workflow ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_node("process_output", process_output_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    router,
    {
        "tools": "tools",
        "process_output": "process_output",
        "end": END
    }
)

workflow.add_edge("tools", "agent")
workflow.add_edge("process_output", END)

app = workflow.compile()
