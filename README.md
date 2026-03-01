# Monday.com BI Analyst Agent 📈

An AI-powered Business Intelligence agent that queries live data from Monday.com boards to provide real-time insights for founders and executives.

## 🚀 Features
- **Live Tool Calling**: Queries Monday.com GraphQL API (`v2`) in real-time without caching.
- **Cross-Board Reasoning**: Seamlessly joins data from "Deals" and "Work Orders" boards.
- **Data Resilience**: Built-in logic to handle messy, inconsistent, and unstructured board data.
- **Token Optimization**: Dynamically requests only necessary columns to avoid LLM rate limits.
- **Dynamic Schema Discovery**: Automatically identifies column names (e.g., matching "Revenue" to "Masked Deal value").
- **Interactive UI**: Built with Streamlit, featuring a live trace of agent tool-calls.

## 📁 Project Structure
```text
.
├── app.py              # Streamlit Web Application (Entry Point)
├── src/
│   ├── agent_logic.py  # AI Agent definition, Tools, and System Prompt
│   └── monday_client.py# Monday.com GraphQL API Client
├── data/               # Project datasets (Excel)
├── docs/               
│   ├── Decision_Log.md # Technical design decisions
│   └── assignment.pdf  # Original requirement specifications
├── .env                # Environment variables (API Keys/Board IDs)
└── requirements.txt    # Python dependencies
```

## 🛠️ Installation & Setup

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables**:
   Create a `.env` file in the root directory with the following:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   MONDAY_API_KEY=your_monday_api_key
   MONDAY_DEALS_BOARD_ID=your_deals_board_id
   MONDAY_WORK_ORDERS_BOARD_ID=your_work_orders_board_id
   ```

## 🖥️ Usage
Run the application using Streamlit:
```bash
streamlit run app.py
```

## 🎯 Example Prompts
- *"How is our pipeline looking for the energy sector this quarter?"*
- *"Which clients have deals in 'Negotiation' but also have 'Open' work orders?"*
- *"Analyze the workload of our top 3 assignees and correlate it with their deal closures."*
