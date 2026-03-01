import streamlit as st
from langchain_core.messages import ChatMessage
from langchain.callbacks.base import BaseCallbackHandler
from src.agent_logic import initialize_agent

# Config UI
st.set_page_config(page_title="Monday.com BI Analyst", page_icon="📈", layout="centered")
st.title("📈 Monday.com BI Analyst Agent")
st.markdown("Ask me questions about our Deals pipeline and Work Orders. I query live Monday.com data to generate insights.")

# Keep chat history in session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        ChatMessage(role="assistant", content="Hello! How can I help you analyze the pipeline or operations today?")
    ]
    
# Display existing chat messages
for msg in st.session_state.messages:
    st.chat_message(msg.role).write(msg.content)

# Custom callback to stream tool usage to UI 
class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, container):
        self.container = container
        self.status = None

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "tool")
        # Ensure we're creating a new status container if needed
        self.status = self.container.status(f"Querying Monday.com via `{tool_name}`...", expanded=True)
        self.status.write(f"Parameters: `{input_str}`")

    def on_tool_end(self, output, **kwargs):
        if self.status:
            # We truncate the output since it can be massive JSON payloads
            snippet = str(output)[:300] + "..." if len(str(output)) > 300 else str(output)
            self.status.write(f"Received {len(str(output))} bytes of data.")
            self.status.write(f"Snippet: `{snippet}`")
            self.status.update(label="Data fetched successfully!", state="complete", expanded=False)

    def on_agent_action(self, action, **kwargs):
      pass

# Input
if prompt := st.chat_input("E.g., How's our pipeline looking for the Renewables sector?"):
    # Add user message to UI and history
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    st.chat_message("user").write(prompt)

    # Initialize agent (this could be cached in session state, but we init here for simplicity)
    try:
        agent_executor = initialize_agent()
    except Exception as e:
        st.error(f"Cannot initialize Agent. Ensure API keys are set. Error: {e}")
        st.stop()

    with st.chat_message("assistant"):
        # We pass an empty container into the handler so `st.status` elements render inside the chat message bubble
        st_callback = StreamlitCallbackHandler(st.container())
        
        try:
            # Run Agent
            response = agent_executor.invoke(
                {"input": prompt, "chat_history": []},
                config={"callbacks": [st_callback]}
            )
            
            answer = response["output"]
            
            # Print answer
            st.write(answer)
            
            # Save to history
            st.session_state.messages.append(ChatMessage(role="assistant", content=answer))
            
        except Exception as e:
            st.error(f"An error occurred during generation: {e}")
