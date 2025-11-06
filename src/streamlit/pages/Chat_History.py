import streamlit as st
import torch
from components.history import Chat_History
from components.healthcheck_sidebar import Healthcheck_Sidebar

torch.classes.__path__ = []

# Page configuration
st.set_page_config(
    page_title="Chat History - ClaimPilot",
    layout="wide",
)

# Sidebar - System status
Healthcheck_Sidebar()

# Page header
st.title("Chat History")
st.markdown("---")

# Render the chat history component
Chat_History(key_prefix="page_chat_history")

# Footer
st.markdown("---")
st.caption("Chat history is stored securely and can be exported for record-keeping purposes.")
