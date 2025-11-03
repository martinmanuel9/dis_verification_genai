import streamlit as st
from config.settings import config
from lib.api.client import api_client
import base64

# Use centralized config for endpoints
FASTAPI = config.endpoints.api
CHROMADB_API = config.endpoints.vectordb
CHAT_ENDPOINT = config.endpoints.chat
HISTORY_ENDPOINT = config.endpoints.history
EVALUATE_ENDPOINT = f"{config.endpoints.api}/evaluate_doc"


def Chat_History(key_prefix: str = "",):  
    def pref(k): return f"{key_prefix}_{k}" if key_prefix else k
    with st.container(border=False, key=pref("history_container")):
        st.header("Chat History")
        
        col_hist1, col_hist2 = st.columns([1, 1])
        
        with col_hist1:
            if st.button("Load Chat History", key=pref("history_button")):
                try:
                    with st.spinner("Loading..."):
                        hist = api_client.get(HISTORY_ENDPOINT, timeout=10)
                        st.session_state[pref("chat_history_data")] = hist
                    if not hist:
                        st.info("No history found.")
                    else:
                        for rec in reversed(hist[-10:]):
                            with st.expander(rec['timestamp'][:19]):
                                st.markdown(f"**User:** {rec['user_query']}")
                                st.markdown(f"**Response:** {rec['response']}")
                except Exception as e:
                    st.error(f"Failed to load history: {e}")
        
        with col_hist2:
            if st.button("Export to Word", key=pref("export_word_button")):
                # Get chat history data
                chat_data = st.session_state.get(pref("chat_history_data"))
                if not chat_data:
                    try:
                        with st.spinner("Loading chat history..."):
                            chat_data = api_client.get(HISTORY_ENDPOINT, timeout=10)
                    except:
                        chat_data = None
                
                if chat_data:
                    try:
                        with st.spinner("Generating Word document..."):
                            export_response = api_client.post(
                                f"{FASTAPI}/doc_gen/export-chat-history-word",
                                params={"limit": 100},
                                timeout=30
                            )

                            file_content = export_response.get("content_b64")
                            filename = export_response.get("filename", "chat_history_export.docx")

                            if file_content:
                                
                                doc_bytes = base64.b64decode(file_content)

                                st.download_button(
                                    label=f"Download {filename}",
                                    data=doc_bytes,
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=pref("download_chat")
                                )
                                st.success("Chat history exported successfully!")
                            else:
                                st.error("No file content received")
                    except Exception as e:
                        st.error(f"Error exporting chat history: {str(e)}")
                else:
                    st.warning("No chat history to export. Load history first.")
                
