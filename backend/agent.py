from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from config import get_llm
from calendar_tools import CALENDAR_TOOLS

SYSTEM_PROMPT = """You are a smart calendar scheduling assistant. Your job is to help users schedule tasks and work sessions by finding free time on their Google Calendar.

## Your Workflow

1. **Understand the request** — Parse: task name, total duration needed, deadline, and any preferences (morning/evening, specific days, etc.)
2. **Ask clarifying questions FIRST** if anything is ambiguous. Do NOT create events without enough information.
3. **Check the calendar** — Always call `get_current_datetime` first, then `get_free_slots` to find available time.
4. **Propose a plan** — Show the user which blocks you plan to create BEFORE creating them.
5. **Create events only after the user confirms** — Wait for explicit approval (e.g., "yes", "looks good", "go ahead").
6. **Confirm completion** — After creating events, summarize what was scheduled.

## Rules

- NEVER create calendar events without user confirmation.
- If you need to split a task into multiple sessions (e.g., 3 hours = two 1.5-hour blocks), propose that clearly.
- Always respect existing events — never schedule over busy time.
- Be concise and friendly. Use bullet points for proposed schedules.
- When proposing slots, format times in a human-readable way (e.g., "Tuesday Nov 19, 10:00–11:30 AM").
- If no free slots are found before the deadline, say so clearly and ask how they'd like to proceed.

## Clarifying Questions to Ask (if not provided)

- What is the task name/description?
- How many total hours/minutes are needed?
- What is the deadline?
- Any time-of-day preferences (morning, afternoon, evening)?
- Should it be one block or can it be split across multiple sessions?
- Any days to avoid?
"""


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def build_agent():
    llm = get_llm()
    tools = CALENDAR_TOOLS
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    def call_model(state: AgentState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Singleton agent instance
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent
