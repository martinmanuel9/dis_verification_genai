import streamlit as st
import requests
import os
from utils import *
from components.upload_documents import browse_documents, render_upload_component

FASTAPI_API = os.getenv("FASTAPI_URL", "http://localhost:9020")
CHROMADB_API = os.getenv("CHROMA_URL", "http://localhost:8020")

def single_agent_analysis(agents, agent_choices, collections):
    """
    Single Agent Analysis Component
    
    Args:
        agents: List of available agents
        agent_choices: Dict mapping agent display names to IDs
        collections: List of available collections
    """
    st.subheader("Single Agent Analysis")
    st.info("Analyze content using selected specialized agents with multiple input options: direct text, document upload, or collection documents.")
    
    # Input method selection
    input_method = st.radio(
        "Choose Input Method:",
        ["Direct Text Input", "Upload Document", "Use Existing Document"],
        horizontal=True,
        key="single_input_method"
    )
    
    analysis_content = None
    collection_name = None
    
    # === DIRECT TEXT INPUT ===
    if input_method == "Direct Text Input":
        with st.container(border=True):
            st.write("**Direct Text Analysis**")
            analysis_content = st.text_area(
                "Content for Agent Analysis:", 
                placeholder="Paste contract text, documents, or content for analysis...",
                height=200,
                key="direct_text_analysis"
            )
            
            # RAG Enhancement option
            use_rag = st.checkbox("Enhance with RAG context", key="direct_rag")
            if use_rag and collections:
                collection_name = st.selectbox(
                    "Select Collection for RAG context:", 
                    collections,
                    key="direct_rag_collection"
                )
            elif use_rag:
                st.warning("No collections available for RAG enhancement")
    
    # === UPLOAD DOCUMENT ===
    elif input_method == "Upload Document":
        with st.container(border=True):
            st.write("**Upload Document for Analysis**")
            
            # Upload section
            st.write("**Step 1: Upload Document**")
            render_upload_component(
                available_collections=collections,
                load_collections_func=get_chromadb_collections,
                create_collection_func=create_collection,
                upload_endpoint=f"{CHROMADB_API}/documents/upload-and-process",
                job_status_endpoint=f"{CHROMADB_API}/jobs/{{job_id}}",
                key_prefix="single_upload"
            )
            
            st.markdown("---")
            
            # Analysis prompt for uploaded document
            st.write("**Step 2: Analysis Prompt**")
            analysis_content = st.text_area(
                "Analysis Prompt for Uploaded Document:",
                placeholder="e.g., 'Analyze this document for compliance risks and regulatory requirements...'",
                height=100,
                key="upload_analysis_prompt"
            )
            
            # Collection selection for uploaded document
            if collections:
                collection_name = st.selectbox(
                    "Select Collection (where document was uploaded):",
                    collections,
                    key="upload_collection_select",
                    help="Choose the collection where you uploaded your document"
                )
            else:
                st.warning("No collections available. Upload a document first.")
                collection_name = None
    
    # === USE EXISTING DOCUMENT ===
    elif input_method == "Use Existing Document":
        with st.container(border=True):
            st.write("**Use Existing Document from Collections**")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Browse Documents**")
                browse_documents(key_prefix="single_browse")
            
            with col2:
                st.write("**Document Selection**")
                if collections:
                    collection_name = st.selectbox(
                        "Select Collection:", 
                        collections, 
                        key="existing_collection",
                        help="Choose which collection contains your document"
                    )
                    
                    document_id = st.text_input(
                        "Document ID:",
                        placeholder="e.g. 12345abcde",
                        key="existing_doc_id",
                        help="Copy the document ID from the browse section above"
                    )
                    
                    # Use selected document ID from browse if available
                    if st.session_state.get('selected_doc_id'):
                        document_id = st.session_state.get('selected_doc_id')
                        st.success(f"Using selected document: {document_id}")
                else:
                    st.warning("No collections available. Upload documents first.")
                    collection_name = None
                    document_id = None
            
            # Analysis prompt for existing document
            analysis_content = st.text_area(
                "Analysis Prompt for Document:",
                placeholder="e.g., 'Analyze this document for compliance risks and regulatory requirements...'",
                height=100,
                key="existing_analysis_prompt"
            )
    
    # === AGENT SELECTION ===
    st.markdown("---")
    st.write("**Agent Selection**")
    selected_agents = st.multiselect(
        "Select Specialized Agents for Analysis:", 
        list(agent_choices.keys()),
        key="single_selected_agents",
        help="Choose multiple agents to get different perspectives on your content"
    )
    
    # === RUN ANALYSIS ===
    if st.button("Run Agent Analysis", type="primary", key="single_run_analysis"):
        if not analysis_content:
            st.warning("Please provide content or analysis prompt.")
        elif not selected_agents:
            st.warning("Please select at least one agent.")
        else:
            agent_ids = [agent_choices[name] for name in selected_agents]
            
            # Determine endpoint and payload based on input method
            if input_method in ["Upload Document", "Use Existing Document"] and collection_name:
                # RAG-enhanced analysis
                payload = {
                    "query_text": analysis_content,
                    "collection_name": collection_name,
                    "agent_ids": agent_ids
                }
                endpoint = f"{FASTAPI_API}/rag-check"
                analysis_type = "RAG-Enhanced"
            elif input_method == "Direct Text Input" and collection_name:
                # Direct text with RAG context
                payload = {
                    "query_text": analysis_content,
                    "collection_name": collection_name,
                    "agent_ids": agent_ids
                }
                endpoint = f"{FASTAPI_API}/rag-check"
                analysis_type = "RAG-Enhanced"
            else:
                # Direct analysis without RAG
                payload = {
                    "data_sample": analysis_content,
                    "agent_ids": agent_ids
                }
                endpoint = f"{FASTAPI_API}/compliance-check"
                analysis_type = "Direct"
            
            with st.spinner(f"{len(selected_agents)} agents analyzing content..."):
                status_placeholder = st.empty()
                try:
                    status_placeholder.info(f"Connecting to AI model... ({analysis_type} Analysis)")
                    response = requests.post(endpoint, json=payload, timeout=300)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Analysis Complete!")
                        
                        # Display results
                        st.subheader("Analysis Results")
                        
                        # Handle different response formats
                        agent_responses = result.get("agent_responses", {})
                        if agent_responses:
                            for agent_name, analysis in agent_responses.items():
                                with st.expander(f"{agent_name} Analysis", expanded=True):
                                    st.markdown(analysis)
                        else:
                            # Handle compliance check format
                            details = result.get("details", {})
                            for idx, analysis in details.items():
                                agent_name = analysis.get("agent_name", f"Agent {idx}")
                                reason = analysis.get("reason", analysis.get("raw_text", "No analysis"))
                                
                                with st.expander(f"{agent_name} Analysis", expanded=True):
                                    st.markdown(reason)
                        
                        # Show session info
                        if "session_id" in result:
                            st.info(f"Analysis Session ID: `{result['session_id']}`")
                        
                        # Show response time
                        if "response_time_ms" in result:
                            st.caption(f"Response time: {result['response_time_ms']/1000:.2f}s")
                        
                        # Word Export Section
                        st.markdown("---")
                        st.subheader("Export Results")
                        if st.button("Export to Word", type="secondary", key="export_single_analysis"):
                            try:
                                with st.spinner("Generating Word document..."):
                                    # Prepare simulation data for export
                                    simulation_data = {
                                        "type": "single_agent_analysis",
                                        "query": analysis_content,
                                        "agent_responses": result.get("agent_responses", {}),
                                        "details": result.get("details", {}),
                                        "session_id": result.get("session_id"),
                                        "response_time_ms": result.get("response_time_ms"),
                                        "agents": [{"name": agent["name"], "model_name": agent["model_name"], "id": agent["id"]} 
                                                  for agent in selected_agents]
                                    }
                                    
                                    # Call FastAPI export endpoint
                                    export_response = requests.post(
                                        f"{FASTAPI_API}/export-simulation-word",
                                        json=simulation_data,
                                        timeout=30
                                    )
                                    
                                    if export_response.status_code == 200:
                                        response_data = export_response.json()
                                        file_content = response_data.get("content_b64")
                                        filename = response_data.get("filename", "agent_simulation_export.docx")
                                        
                                        if file_content:
                                            import base64
                                            doc_bytes = base64.b64decode(file_content)
                                            
                                            st.download_button(
                                                label=f"Download {filename}",
                                                data=doc_bytes,
                                                file_name=filename,
                                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                key="download_single_analysis"
                                            )
                                            st.success("Analysis exported successfully!")
                                        else:
                                            st.error("No file content received")
                                    else:
                                        st.error(f"Export failed: {export_response.text}")
                            except Exception as e:
                                st.error(f"Error exporting analysis: {str(e)}")
                            
                    else:
                        error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                        st.error(f"Analysis failed ({response.status_code}): {error_detail}")
                        
                except requests.exceptions.Timeout:
                    status_placeholder.empty()
                    st.error("Request timed out. The model might be loading - please try again in a moment.")
                    st.info("Large models can take 1-2 minutes to load on first use.")
                except Exception as e:
                    status_placeholder.empty()
                    st.error(f"Analysis failed: {str(e)}")
    
    # === HELP SECTION ===
    with st.expander("How Single Agent Analysis Works"):
        st.markdown("""
        **Single Agent Analysis Options:**
        
        **Direct Text Input:**
        - Paste text directly for immediate analysis
        - Optional RAG enhancement from your collections
        - Best for: Quick analysis of copied text or short content
        
        **Upload Document:**
        - Upload files (PDF, DOCX, TXT, etc.) for analysis
        - Documents are automatically processed and stored
        - Best for: New documents you want to analyze and keep
        
        **Use Existing Document:**
        - Select from previously uploaded documents
        - Browse your collections and select specific documents
        - Best for: Re-analyzing or getting new perspectives on existing documents
        
        **Agent Selection:**
        - Choose multiple agents for different analytical perspectives
        - Each agent applies their specialized expertise
        - Results show individual agent analyses
        
        **Example Use Cases:**
        - Contract analysis with Legal + Risk agents
        - Technical documentation review with multiple engineering agents  
        - Compliance assessment with Regulatory + Business agents
        """)