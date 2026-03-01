# Decision Log - Monday.com BI Agent

## Tech Stack Chosen
1. **Frontend**: Streamlit
   - *Why*: Allows for the fastest possible development of conversational AI interfaces with built-in support for status elements (perfect for displaying live tool-call traces). No setup is required for the evaluator since it can be easily hosted on Streamlit Community Cloud.
2. **AI Logic & Routing**: LangChain & OpenAI functions (`gpt-4o`)
   - *Why*: GPT-4o is currently best-in-class for function calling and interpreting messy JSON structures. LangChain provides a robust `AgentExecutor` to handle the iterative loop of thought -> action -> observation, abstracting away the boilerplate of raw OpenAI API calls.
3. **Data Integration**: Direct GraphQL REST API Calls (via `requests`)
   - *Why*: The assignment specifically requested live API calls at query time without preloading or caching data. Direct API requests guarantee that when a user asks a question, the agent has the freshest possible state of the Monday boards.

## Data Resilience Strategies
The provided data (`Deals` and `Work Orders`) contains deliberate inconsistencies such as missing revenue, differing date formats, and string-typed numbers.
To handle this without pre-processing data pipelines, I implemented a robust **System Prompt** strategy. The agent is explicitly instructed to:
1. Expect unstructured data (nulls, string currencies).
2. Clean and cast the data internally during its "Thought" phase before performing mathematical aggregations.
3. **Most importantly**: Report any caveats to the user. If 3 deals are missing revenue, the LLM will provide the total revenue while adding a disclaimer that 3 deals were excluded.

## Agent Action Visibility
To satisfy the requirement of showing a visible API/tool-call trace:
- In the Streamlit UI, the `st.status` expander is utilized via a custom callback handler.
- When the LLM decides to hit the `/v2` Monday endpoint, the UI immediately expands a status block saying "Querying Monday.com via `get_deals_board_data`", proving to the user that live external tools are actively being leveraged to formulate their answer.

## Project Structure
The project is organized into a professional modular structure:
- `app.py`: Streamlit entry point.
- `src/`: Core logic and client implementations.
  - `agent_logic.py`: LLM agent and tool definitions.
  - `monday_client.py`: API interaction layer.
- `data/`: Provided datasets.
- `docs/`: Technical documentation and assignment specs.

## Future Improvements & Limitations
Given the 6-hour time limit, the following compromises were made:
1. **No Vector Database**: A pure function-calling approach is used. If the boards scale to tens of thousands of rows, fetching the *entire* board via an API call every time would be too slow/expensive. A production system should use webhooks to sync Monday.com data into a PostgreSQL or Vector DB and have the agent write SQL to query it instead.
2. **Simple Authentication**: The prototype uses server-side environment variables. A true multi-tenant saas would implement Monday.com OAuth so users could easily connect their own workspaces.
3. **Token Limits**: If a board contains >1000 items, the JSON payload stringified back to the LLM might exceed context window limits. For large boards, the tools should be adjusted to accept filtering arguments (e.g., `fetch_deals(status="Won")`) to only retrieve relevant items.
