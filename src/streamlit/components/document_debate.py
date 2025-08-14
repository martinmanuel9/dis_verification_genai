import streamlit as st
import requests
import os
from utils import *
from components.upload_documents import browse_documents, render_upload_component

FASTAPI_API = os.getenv("FASTAPI_URL", "http://localhost:9020")
CHROMADB_API = os.getenv("CHROMA_URL", "http://localhost:8020")

def document_based_debate(agents, agent_choices, collections):
    """
    Document-Based Agent Debate Component
    
    Args:
        agents: List of available agents
        agent_choices: Dict mapping agent display names to IDs
        collections: List of available collections
    """
    st.subheader("Document-Based Agent Debate")
    st.info("Select a specific document from your collections for agents to debate about. This uses RAG to pull content from your uploaded documents and allows multiple agents to analyze the same content with different perspectives.")
    
    # === CONTENT INPUT SELECTION ===
    st.write("**Step 1: Choose Document Input Method**")
    
    input_method = st.radio(
        "Select Document Input Method:",
        ["Upload Document", "Use Existing Document"],
        horizontal=True,
        key="document_debate_input_method"
    )
    
    debate_content = None
    collection_for_debate = None
    
    # === UPLOAD DOCUMENT ===
    if input_method == "Upload Document":
        with st.container(border=True):
            st.write("**Upload Document for Debate**")
            
            # Upload section
            st.write("**Step 1a: Upload Document**")
            render_upload_component(
                available_collections=collections,
                load_collections_func=get_chromadb_collections,
                create_collection_func=create_collection,
                upload_endpoint=f"{CHROMADB_API}/documents/upload-and-process",
                job_status_endpoint=f"{CHROMADB_API}/jobs/{{job_id}}",
                key_prefix="doc_debate_upload"
            )
            
            st.markdown("---")
            
            # Debate prompt for uploaded document
            st.write("**Step 1b: Debate Prompt**")
            debate_content = st.text_area(
                "Debate Topic/Prompt for Uploaded Document:",
                placeholder="e.g., 'Debate the legal implications and business risks of this contract...'\n\n'Analyze this document from multiple perspectives: risk management, legal compliance, and operational impact...'",
                height=120,
                key="doc_debate_upload_prompt"
            )
            
            # Collection selection for uploaded document
            if collections:
                collection_for_debate = st.selectbox(
                    "Select Collection (where document was uploaded):",
                    collections,
                    key="doc_debate_upload_collection",
                    help="Choose the collection where you uploaded your document"
                )
            else:
                st.warning("No collections available. Upload a document first.")
    
    # === USE EXISTING DOCUMENT ===
    elif input_method == "Use Existing Document":
        with st.container(border=True):
            st.write("**Use Existing Document for Debate**")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Browse Documents**")
                browse_documents(key_prefix="doc_debate_browse")
            
            with col2:
                st.write("**Document Selection**")
                if collections:
                    collection_for_debate = st.selectbox(
                        "Select Collection:", 
                        collections, 
                        key="doc_debate_existing_collection",
                        help="Choose which collection contains your document"
                    )
                    
                    document_id = st.text_input(
                        "Document ID:",
                        placeholder="e.g. 12345abcde",
                        key="doc_debate_existing_doc_id",
                        help="Copy the document ID from the browse section above"
                    )
                    
                    # Use selected document ID from browse if available
                    if st.session_state.get('selected_doc_id'):
                        document_id = st.session_state.get('selected_doc_id')
                        st.success(f"Using selected document: {document_id}")
                else:
                    st.warning("No collections available. Upload documents first.")
                    collection_for_debate = None
                    document_id = None
            
            # Debate prompt for existing document
            debate_content = st.text_area(
                "Debate Topic/Prompt for Document:",
                placeholder="e.g., 'Debate the legal implications and business risks of this contract...'\n\n'Analyze this document from multiple perspectives: risk management, legal compliance, and operational impact...'",
                height=120,
                key="doc_debate_existing_prompt"
            )
    
    # === AGENT SELECTION ===
    st.markdown("---")
    st.write("**Step 2: Select Agents for Document Debate**")
    
    doc_selected_agents = st.multiselect(
        "Choose Agents for Document Analysis:", 
        list(agent_choices.keys()),
        key="doc_debate_agents",
        help="Select multiple agents to get different analytical perspectives on the same document"
    )
    
    # === START DOCUMENT DEBATE ===
    st.markdown("---")
    st.write("**Step 3: Start Document-Based Debate**")
    
    if st.button("Start Document Debate", type="primary", key="start_doc_debate"):
        if not debate_content:
            st.warning("Please enter a debate topic/prompt.")
        elif not collection_for_debate:
            st.warning("Please select a collection.")
        elif not doc_selected_agents:
            st.warning("Please select at least one agent.")
        else:
            doc_agent_ids = [agent_choices[name] for name in doc_selected_agents]
            
            # Show debate setup
            with st.expander("🔍 Document Debate Setup", expanded=True):
                st.write(f"**Debate Prompt**: {debate_content[:100]}{'...' if len(debate_content) > 100 else ''}")
                st.write(f"**Collection**: {collection_for_debate}")
                st.write(f"**Agents**: {len(doc_agent_ids)} selected")
                st.write(f"**Input Method**: {input_method}")
                for i, agent_name in enumerate(doc_selected_agents, 1):
                    st.write(f"  {i}. {agent_name}")
            
            # Execute document-based debate using RAG
            debate_payload = {
                "query_text": debate_content,
                "collection_name": collection_for_debate,
                "agent_ids": doc_agent_ids
            }
            
            with st.spinner(f"{len(doc_agent_ids)} agents analyzing document..."):
                status_placeholder = st.empty()
                try:
                    status_placeholder.info("Connecting to document analysis service...")
                    response = requests.post(f"{FASTAPI_API}/rag-check", json=debate_payload, timeout=300)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Document Debate Complete!")
                        
                        # Display session info
                        session_id = result.get("session_id")
                        if session_id:
                            st.info(f"Document Debate Session ID: `{session_id}`")
                        
                        # Display debate results
                        st.subheader("Document Analysis Results")
                        
                        # Handle different response formats
                        agent_responses = result.get("agent_responses", {})
                        if agent_responses:
                            for i, (agent_key, response_text) in enumerate(agent_responses.items(), 1):
                                # Try to get agent name from the selected agents
                                if i <= len(doc_selected_agents):
                                    display_name = doc_selected_agents[i-1]
                                else:
                                    display_name = agent_key
                                
                                with st.expander(f"{display_name}", expanded=True):
                                    st.markdown(response_text)
                        
                        else:
                            # Handle alternative response formats
                            details = result.get("details", {})
                            for idx, analysis in details.items():
                                agent_name = analysis.get("agent_name", f"Agent {idx}")
                                reason = analysis.get("reason", analysis.get("raw_text", "No analysis"))
                                
                                with st.expander(f"{agent_name}", expanded=True):
                                    st.markdown(reason)
                        
                        # Show response time
                        if "response_time_ms" in result:
                            st.caption(f"Total analysis time: {result['response_time_ms']/1000:.2f}s")
                            
                    else:
                        error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                        st.error(f"Document debate failed ({response.status_code}): {error_detail}")
                        
                except requests.exceptions.Timeout:
                    status_placeholder.empty()
                    st.error("Request timed out. The model might be loading - please try again in a moment.")
                    st.info("Large models can take 1-2 minutes to load on first use.")
                except Exception as e:
                    status_placeholder.empty()
                    st.error(f"Document debate failed: {str(e)}")
    
    # === HELP SECTION ===
    with st.expander("How Document-Based Debate Works"):
        st.markdown("""
        **Document-Based Agent Debate Process:**
        
        **Step 1: Document Input Options**
        
        **Upload Document:**
        - Upload new documents (PDF, DOCX, TXT, etc.) for analysis
        - Documents are processed and stored in ChromaDB collections
        - Best for: New documents that need fresh multi-perspective analysis
        
        **Use Existing Document:**
        - Select from previously uploaded documents in your collections
        - Browse collections and choose specific documents
        - Best for: Getting new perspectives on existing documents
        
        **Step 2: Agent Selection**
        - Choose multiple specialized agents for different analytical perspectives
        - Each agent applies their configured prompts and expertise
        - All agents analyze the same document content but from their unique viewpoints
        
        **Step 3: Document Debate Execution**
        - Uses RAG (Retrieval Augmented Generation) to pull relevant content from your document
        - Each agent receives the same document context but analyzes it through their specialized lens
        - Results show diverse analytical perspectives on the same content
        
        **Key Features:**
        - **RAG-Enhanced**: Pulls actual content from your uploaded documents
        - **Multi-Perspective**: Different agents provide specialized viewpoints
        - **Document-Focused**: All analysis is grounded in your specific document content
        - **Comparative Analysis**: Easy to compare different expert opinions on the same material
        
        **Example Use Cases:**
        - **Contract Analysis**: Legal vs. Risk vs. Business perspectives on the same contract
        - **Technical Documentation**: Engineering vs. QA vs. Product Management viewpoints
        - **Policy Review**: Compliance vs. Operations vs. HR perspectives on policy documents
        - **Research Papers**: Different domain experts analyzing the same research from their specialties
        
        **Why Document-Based Debate:**
        - **Grounded Analysis**: All responses are based on actual document content
        - **Comprehensive Coverage**: Multiple expert viewpoints on the same material
        - **Decision Support**: Compare different professional opinions to make informed decisions
        - **Quality Assurance**: Cross-validate findings across different analytical approaches
        """)