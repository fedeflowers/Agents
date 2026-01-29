import json
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.tools import tool

from src.schemas import ExtractionResult
from src.config import settings
from src.tools.mock_cad import get_material_properties
from src.tools.submit import submit_extraction

# --- Setup Model ---
# We use ChatLiteLLM which leverages the litellm library
llm = ChatLiteLLM(model=settings.MODEL_NAME, temperature=0)

# --- Define Tools ---
# We treat the final extraction as a "tool" the agent must call to submit its work.

# Update the Pydantic model description to be very clear it's for this tool
# We can just bind the Pydantic model directly as a structured output tool helper,
# but wrapping it in a function ensures it looks like a tool to the LLM.
# CTUALLY, passing the Pydantic class to bind_tools works great in LangChain.
# It creates a tool named "ExtractionResult".

tools = [get_material_properties, ExtractionResult]
llm_with_tools = llm.bind_tools(tools)

# --- Graph State ---
class AgentState(TypedDict):
    input_text: str
    messages: Annotated[List[BaseMessage], add_messages]
    final_output: Optional[Dict[str, Any]]

# --- Nodes ---

async def agent_node(state: AgentState):
    messages = state["messages"]
    
    # System prompt to guide behavior
    if not messages or not isinstance(messages[0], SystemMessage):
        sys_msg = SystemMessage(content="""You are an expert engineering data extractor. 
Extract strict structured data from the text.
If a Part ID is present (e.g., PART-123), you MUST use the 'get_material_properties' tool to enrich the data (density, thermal conductivity, etc.) BEFORE finalizing.
IMPORTANT: The tool does NOT provide stress data. You MUST extract 'Max Stress' directly from the input text.
- If the text says a part "handled" or "withstood" a stress (e.g., "handled 400 MPa"), that IS the Max Stress.
- If the text says "no stress" or similar, set Max Stress to 0.0.
- If the text explicitly mentions a negative value, extract it exactly as written including the negative sign.
- Do not hallucinate numbers. Only use values present in the text.
Once you have all information, call the 'ExtractionResult' tool to submit the final answer.
""")
        messages = [sys_msg] + messages

    # Add input text if this is the start and we haven't added it yet
    # We check if the last message is a HumanMessage with the input, or just checking state
    if len(messages) == 1 and isinstance(messages[0], SystemMessage):
         messages.append(HumanMessage(content=f"Analyze this text: {state['input_text']}"))

    # Debug print
    # print(f"--- Sending to LLM ---\n{messages}\n----------------")
        
    response = await llm_with_tools.ainvoke(messages)
    
    # Debug print
    # print(f"--- LLM Response ---\n{response}\n----------------")
    
    return {"messages": [response]}

def router(state: AgentState) -> Literal["tools", "process_output", "end"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        # If no tool called, force end (or error?)
        # Ideally the model ALWAYS calls a tool because we told it to.
        # But if it chats, we just end.
        return "end"
    
    # Check if it called the extraction tool
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "ExtractionResult":
            return "process_output"
            
    return "tools"

async def process_output_node(state: AgentState):
    """
    Extracts the structured data from the tool call and validates it.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    final_data = {}
    
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "ExtractionResult":
            # The args are already a dict, validation will happen via Pydantic model instantiation
            try:
                # Validate using the actual model
                data = tool_call["args"]
                # We can instantiate to validate, but we just return the dict for the main pipeline
                # Optionally run ExtractionResult(**data) to catch errors here
                validated = ExtractionResult(**data)
                final_data = validated.model_dump(mode='json')
            except Exception as e:
                # Validation failed. Return raw args but set requires_review=True
                final_data = tool_call["args"]
                final_data["requires_review"] = True
                final_data["error"] = str(e)
            break
            
    return {"final_output": final_data}

# Define Tool Node (using prebuilt for standard tools)
# Note: We only want to run 'get_material_properties' here. 
# 'ExtractionResult' is handled by process_output_node.
tool_node = ToolNode([get_material_properties])

# --- Workflow ---
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
