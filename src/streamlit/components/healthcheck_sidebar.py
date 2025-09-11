import streamlit as st
import requests
from utils import *


FASTAPI_API = os.getenv("FASTAPI_URL", "http://localhost:9020")
HEALTH_ENDPOINT = f"{FASTAPI_API}/health"


def Healthcheck_Sidebar():
    """Render the sidebar with system health check and collections"""
    
    # Initialize session state for health status
    if "health_status" not in st.session_state:
        st.session_state.health_status = None
    
    # Render sidebar
    st.sidebar.title("System Health")
    
    # Check if collections are loaded
    if "collections" not in st.session_state:
        st.session_state.collections = []

    # Render sidebar
    with st.sidebar:
        # Health check
        if st.button("Check Health"):
            try:
                with st.spinner("Checking health..."):
                    response = requests.get(HEALTH_ENDPOINT, timeout=60)
                    if response.ok:
                        st.session_state.health_status = response.json()
                        st.success("Online")
                    else:
                        st.error("System Issues")
            except Exception as e:
                st.error(f"Cannot connect to API: {e}")
    
        # Display cached health status
        if st.session_state.health_status:
            with st.expander("System Details"):
                hs = st.session_state.health_status
                st.json(hs)
                # Ollama quick view
                if isinstance(hs, dict) and 'ollama' in hs:
                    o = hs['ollama'] or {}
                    st.markdown("---")
                    st.subheader("Ollama Models")
                    st.caption(f"Status: {o.get('status')} | Host: {o.get('base_url')}")
                    st.write("Available:")
                    st.code("\n".join(o.get('available_models', [])) or "(none)")
                    st.write("Resolved (UI → Tag):")
                    resolved = o.get('resolved', {})
                    for k, v in (resolved.items() if isinstance(resolved, dict) else []):
                        st.text(f"{k} → {v}")
                    missing = o.get('missing', [])
                    if missing:
                        st.warning(f"Missing tags: {missing}")
                        if st.button("Pull Missing Models", key="pull_missing_models"):
                            try:
                                with st.spinner("Pulling models..."):
                                    r = requests.post(f"{FASTAPI_API}/ollama/pull-required", timeout=300)
                                if r.ok:
                                    res = r.json()
                                    st.success("Pull completed")
                                    st.json(res)
                                else:
                                    st.error(f"Pull failed: {r.status_code} {r.text}")
                            except Exception as e:
                                st.error(f"Pull error: {e}")

        st.header("Collections")
        
        if st.button("Load Collections"):
            try:
                # Load collections from both sources
                chromadb_collections = get_chromadb_collections()
                
                # Combine and deduplicate
                all_collections = list(set(chromadb_collections))
                st.session_state.collections = all_collections
                st.success("Collections loaded!")
            except Exception as e:
                st.error(f"Error: {e}")
        
        # Display collections
        collections = st.session_state.collections
        if collections:
            for collection in collections:
                st.text(f"{collection}")
        else:
            st.info("Click 'Load Collections' to see available databases")

        # Get collections for main interface
        try:
            if not st.session_state.collections:
                chromadb_collections = get_chromadb_collections()
                collections = list(set(chromadb_collections))
                st.session_state.collections = collections
            else:
                collections = st.session_state.collections
        except:
            collections = []
