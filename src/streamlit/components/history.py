import streamlit as st
import requests
from utils import * 


FASTAPI_API      = os.getenv("FASTAPI_URL", "http://localhost:9020")
CHROMADB_API     = os.getenv("CHROMA_URL", "http://localhost:8020")
CHAT_ENDPOINT    = f"{FASTAPI_API}/chat"
HISTORY_ENDPOINT = f"{FASTAPI_API}/chat-history"
EVALUATE_ENDPOINT = f"{FASTAPI_API}/evaluate_doc"


def Chat_History(key_prefix: str = "",):  
    def pref(k): return f"{key_prefix}_{k}" if key_prefix else k
    with st.container(border=False, key=pref("history_container")):
        st.header("Chat History")
        
        col_hist1, col_hist2 = st.columns([1, 1])
        
        with col_hist1:
            if st.button("Load Chat History", key=pref("history_button")):
                try:
                    with st.spinner("Loading..."):
                        hist = requests.get(HISTORY_ENDPOINT, timeout=10).json()
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
                    # Try to fetch if not already loaded
                    try:
                        with st.spinner("Loading chat history..."):
                            chat_data = requests.get(HISTORY_ENDPOINT, timeout=10).json()
                    except:
                        chat_data = None
                
                if chat_data:
                    try:
                        with st.spinner("Generating Word document..."):
                            # Call FastAPI export endpoint with query parameters
                            export_response = requests.post(
                                f"{FASTAPI_API}/export-chat-history-word",
                                params={"limit": 100},  # Export up to 100 recent chats
                                timeout=30
                            )
                            
                            if export_response.status_code == 200:
                                response_data = export_response.json()
                                file_content = response_data.get("content_b64")
                                filename = response_data.get("filename", "chat_history_export.docx")
                                
                                if file_content:
                                    import base64
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
                            else:
                                st.error(f"Export failed: {export_response.text}")
                    except Exception as e:
                        st.error(f"Error exporting chat history: {str(e)}")
                else:
                    st.warning("No chat history to export. Load history first.")
                