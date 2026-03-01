import streamlit as st
from langchain_core.messages import ChatMessage
from langchain_core.callbacks import BaseCallbackHandler
from src.agent_logic import initialize_agent

# -------------------------
# Page Config
# -------------------------
st.set_page_config(
    page_title="Monday.com BI Analyst",
    page_icon="📈",
    layout="centered"
)

st.title("📈 Monday.com BI Analyst Agent")
st.markdown(
    "Ask me questions about our Deals pipeline and Work Orders. "
    "I query live Monday.com data to generate insights."
)

# -------------------------
# Session State
# -------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        ChatMessage(
            role="assistant",
            content="Hello! How can I help you analyze the pipeline or operations today?"
        )
    ]

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

# -------------------------
# Streamlit Callback Handler
# -------------------------
class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, container):
        self.container = container
        self.status = None

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "tool")
        self.status = self.container.status(
            f"Querying Monday.com via `{tool_name}`...",
            expanded=True
        )
        self.status.write(f"Parameters: `{input_str}`")

    def on_tool_end(self, output, **kwargs):
        if self.status:
            output_str = str(output)
            snippet = output_str[:300] + "..." if len(output_str) > 300 else output_str
            self.status.write(f"Received {len(output_str)} bytes of data.")
            self.status.write(f"Snippet: `{snippet}`")
            self.status.update(
                label="Data fetched successfully!",
                state="complete",
                expanded=False
            )

# -------------------------
# Chat Input
# -------------------------
if prompt := st.chat_input(
    "E.g., How's our pipeline looking for the Renewables sector?"
):

    # Add user message
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    st.chat_message("user").write(prompt)

    # Initialize Agent
    try:
        agent_executor = initialize_agent()
    except Exception as e:
        st.error(f"Cannot initialize Agent. Ensure API keys are set.\n\nError: {e}")
        st.stop()

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())

        try:
            response = agent_executor.invoke(
                {
                    "input": prompt,
                    "chat_history": []
                },
                config={"callbacks": [st_callback]}
            )

            answer = response["output"]

            st.write(answer)

            st.session_state.messages.append(
                ChatMessage(role="assistant", content=answer)
            )

        except Exception as e:
            st.error(f"An error occurred during generation:\n\n{e}")