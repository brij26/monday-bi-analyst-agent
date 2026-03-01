import os
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from src.monday_client import fetch_board_data, get_column_titles

# Load environment variables
load_dotenv()

# Validate OpenAI key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set.")


# ---------------------------
# Tools
# ---------------------------

@tool
def get_board_columns(board_type: str) -> str:
    """Lists all available column titles for a specific board ('deals' or 'work_orders')."""
    if board_type.lower() == "deals":
        board_id = os.getenv("MONDAY_DEALS_BOARD_ID")
    else:
        board_id = os.getenv("MONDAY_WORK_ORDERS_BOARD_ID")

    if not board_id:
        return f"Error: {board_type} board ID not set."

    cols = get_column_titles(board_id)
    return ", ".join(cols)


@tool
def get_deals_board_data(columns_to_fetch: list[str] | None = None) -> str:
    """Fetches live data from Deals board."""
    board_id = os.getenv("MONDAY_DEALS_BOARD_ID")
    if not board_id:
        return "Error: MONDAY_DEALS_BOARD_ID not set."

    data = fetch_board_data(board_id, columns_to_keep=columns_to_fetch)
    return json.dumps(data, separators=(",", ":"))


@tool
def get_work_orders_board_data(columns_to_fetch: list[str] | None = None) -> str:
    """Fetches live data from Work Orders board."""
    board_id = os.getenv("MONDAY_WORK_ORDERS_BOARD_ID")
    if not board_id:
        return "Error: MONDAY_WORK_ORDERS_BOARD_ID not set."

    data = fetch_board_data(board_id, columns_to_keep=columns_to_fetch)
    return json.dumps(data, separators=(",", ":"))


# ---------------------------
# System Prompt
# ---------------------------

BI_SYSTEM_PROMPT = """You are an expert Business Intelligence AI Agent assisting founders and executives.
Your primary role is to answer complex business questions by querying live data from monday.com boards.

CRITICAL:
- If unsure about column names, call `get_board_columns`.
- Fetch only necessary columns.
- Clean and normalize messy values.
- Explicitly mention missing or inconsistent data.

Always reason carefully and compute aggregates only from provided data.
"""


# ---------------------------
# Initialize Agent
# ---------------------------

def initialize_agent():
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
    )

    tools = [
        get_board_columns,
        get_deals_board_data,
        get_work_orders_board_data,
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", BI_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # ✅ NEW 0.2+ AGENT
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
    )

    return agent_executor


if __name__ == "__main__":
    agent_exec = initialize_agent()
    print("Agent initialized successfully.")