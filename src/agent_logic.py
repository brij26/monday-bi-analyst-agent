import os
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents.openai_functions_agent.base import create_openai_functions_agent
from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from src.monday_client import fetch_board_data, get_column_titles

# Load environment variables
load_dotenv()

# We need the OpenAI key to initialize the LLM
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please add it to your .env file.")

# Define Tools
@tool
def get_board_columns(board_type: str) -> str:
    """
    Lists all available column titles for a specific board.
    Use this if you are unsure which columns contain revenue, sectors, or status.
    board_type should be either 'deals' or 'work_orders'.
    """
    if board_type.lower() == 'deals':
        board_id = os.getenv("MONDAY_DEALS_BOARD_ID")
    else:
        board_id = os.getenv("MONDAY_WORK_ORDERS_BOARD_ID")
        
    if not board_id:
        return f"Error: {board_type} board ID not set."
    
    cols = get_column_titles(board_id)
    return ", ".join(cols)

@tool
def get_deals_board_data(columns_to_fetch: list[str] = None) -> str:
    """
    Fetches live data from the Monday.com Deals board. 
    Use this to answer questions about deal pipelines, revenue, sales, and client sectors.
    You can optionally provide a list of column names to fetch to save context space (e.g. ['Client Code', 'Masked Deal value', 'Sector/service']).
    Returns a JSON string representation of the rows.
    """
    board_id = os.getenv("MONDAY_DEALS_BOARD_ID")
    if not board_id:
        return "Error: MONDAY_DEALS_BOARD_ID is not set in the environment."
    data = fetch_board_data(board_id, columns_to_keep=columns_to_fetch)
    return json.dumps(data, separators=(',', ':'))


@tool
def get_work_orders_board_data(columns_to_fetch: list[str] = None) -> str:
    """
    Fetches live data from the Monday.com Work Orders board.
    Use this to answer questions about tickets, workloads, operation status, and issue resolution.
    You can optionally provide a list of column names to fetch to save context space (e.g. ['Company', 'Issue', 'Assignee']).
    Returns a JSON string representation of the rows.
    """
    board_id = os.getenv("MONDAY_WORK_ORDERS_BOARD_ID")
    if not board_id:
        return "Error: MONDAY_WORK_ORDERS_BOARD_ID is not set in the environment."
    data = fetch_board_data(board_id, columns_to_keep=columns_to_fetch)
    return json.dumps(data, separators=(',', ':'))

# Define the System Prompt
BI_SYSTEM_PROMPT = """You are an expert Business Intelligence AI Agent assisting founders and executives.
Your primary role is to answer complex business questions by querying live data from monday.com boards.

You have access to:
1. Deals Board: Contains sales pipeline, revenue, sector information, and deal status.
2. Work Orders Board: Contains operational workloads, ticket status, assignees, and issue details.

CRITICAL: EXHAUSTIVE DATA CLEANING & NORMALIZATION
The board data is intentionally messy. You MUST be an investigative analyst:
- COLUMN DISCOVERY: If you are searching for 'Revenue' or 'Sector' and it returns 0 results, use `get_board_columns` to see if the column is named something else (e.g., 'Masked Deal value', 'Sector/service', 'Deal Amount').
- VALUE NORMALIZATION: When filtering by sector (e.g., 'Energy'), search for partial matches and synonyms. 'Renewables', 'Powerline', and 'Energy Sector' should all be considered part of an 'Energy' query unless specified otherwise.
- CURRENCY/NUMBERS: Revenue values might look like "$1,200,000" or "1200k". Always strip non-numeric characters and cast to a float before summing.
- NULL HANDLING: If a row has a sector but no revenue, still count the deal but state that the revenue was $0 or missing for that specific record.

YOUR PROCESS:
1. Always call `get_board_columns` if you are unsure of the schema.
2. Call the data fetching tools with specific columns you identified to stay under token limits.
3. Clean and normalize the data in your "mind" (e.g., 'Renewables' -> 'Energy').
4. Calculate aggregates based ONLY on the data provided.
5. IF data is missing or inconsistent, YOU MUST EXPLICITLY STATE THIS CAVEAT in your final answer.

Example interaction:
User: "How's our pipeline looking for the energy sector?"
You: [Calls get_board_columns] -> Sees 'Sector/service' and 'Masked Deal value'.
You: [Calls get_deals_board_data(columns_to_fetch=['Sector/service', 'Masked Deal value'])]
You (to user): "We have several energy-related deals. I've aggregated 'Renewables' and 'Powerline' into this total..."
"""

# Initialize Agent
def initialize_agent():
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    tools = [get_board_columns, get_deals_board_data, get_work_orders_board_data]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", BI_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

if __name__ == "__main__":
    # Simple terminal test
    agent_exec = initialize_agent()
    print("Agent initialized. Ready for queries.")
    # result = agent_exec.invoke({"input": "What is the total revenue of all deals?", "chat_history": []})
    # print(result['output'])
