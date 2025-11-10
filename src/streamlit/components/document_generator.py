"""
Document Generator Component
Migrated to new architecture - uses centralized config and services
"""
import streamlit as st
import base64
from config.settings import config
from lib.api.client import api_client
from services.chromadb_service import chromadb_service


def Document_Generator():
    st.header("Document Generator")
    st.info("Generate comprehensive documentation using AI agents and templates.")
    st.subheader("Generate Documents")

    # ----------------------------
    # Agent Set Selection
    # ----------------------------
    st.markdown("---")
    st.subheader("Agent Orchestration")

    # Fetch available agent sets
    try:
        agent_sets_response = api_client.get(f"{config.fastapi_url}/api/agent-sets")
        agent_sets = agent_sets_response.get("agent_sets", [])
        active_agent_sets = [s for s in agent_sets if s.get('is_active', True)]
    except Exception as e:
        st.warning(f"Could not load agent sets: {e}")
        active_agent_sets = []

    # Agent set selector
    if active_agent_sets:
        agent_set_options = [s['name'] for s in active_agent_sets]
        selected_agent_set = st.selectbox(
            "Select Agent Pipeline",
            options=agent_set_options,
            key="gen_agent_set",
            help="Choose an agent set to define the orchestration pipeline."
        )

        # Show agent set details
        agent_set = next((s for s in active_agent_sets if s['name'] == selected_agent_set), None)
        if agent_set:
            with st.expander("View Agent Set Configuration"):
                st.write(f"**Description:** {agent_set.get('description', 'No description')}")
                st.write(f"**Type:** {agent_set.get('set_type', 'sequence')}")
                st.write(f"**Usage Count:** {agent_set.get('usage_count', 0)}")
                st.write("**Pipeline Stages:**")
                for idx, stage in enumerate(agent_set.get('set_config', {}).get('stages', []), 1):
                    st.write(f"  {idx}. **{stage.get('stage_name')}** - {len(stage.get('agent_ids', []))} agent(s) ({stage.get('execution_mode')})")
                    if stage.get('description'):
                        st.caption(f"     {stage.get('description')}")
    else:
        st.error("No agent sets available. Please create an agent set in the Agent Set Manager.")
        st.stop()

    # ----------------------------
    # 2) Select source documents
    # ----------------------------
    st.markdown("---")
    st.subheader("Source Documents")

    if "collections" not in st.session_state:
        st.session_state.collections = chromadb_service.get_collections()

    collections = st.session_state.collections

    if not collections:
        st.warning("No collections available. Please upload documents first.")
        st.stop()

    # Pick collection & load source docs
    source_collection = st.selectbox(
        "Select Collection",
        collections,
        key="gen_source_coll",
    )

    if st.button("Load Source Documents", key="gen_load_sources"):
        with st.spinner("Loading source documents..."):
            try:
                documents = chromadb_service.get_documents(source_collection)
                st.session_state.source_docs = [
                    {
                        'document_id': doc.document_id,
                        'document_name': doc.document_name
                    }
                    for doc in documents
                ]
                st.success(f"Loaded {len(documents)} source documents")
            except Exception as e:
                st.error(f"Failed to load source documents: {e}")

    source_docs = st.session_state.get("source_docs", [])
    source_map = {d["document_name"]: d["document_id"] for d in source_docs}
    selected_sources = st.multiselect(
        "Select Source Document(s)",
        list(source_map.keys()),
        key="gen_sources"
    )
    source_doc_ids = [source_map[name] for name in selected_sources]

    # ----------------------------
    # 3) Let user name the output file
    # ----------------------------
    out_name = st.text_input(
        "Output file name (no extension):",
        value="Generated_Test_Plan",
        key="gen_filename"
    ).strip()

    # ----------------------------
    # 4) Test Card & Export Options
    # ----------------------------
    st.markdown("---")
    st.subheader("Test Card & Export Options")

    col1, col2 = st.columns(2)

    with col1:
        include_test_cards = st.checkbox(
            "Include Test Cards in Generated Document",
            value=True,
            help="Add executable test card tables after each section",
            key="gen_include_test_cards"
        )

    with col2:
        export_method = st.radio(
            "Export Method:",
            ["Standard (python-docx)", "Professional (Pandoc)"],
            horizontal=True,
            help="Pandoc provides better formatting with automatic TOC and section numbering",
            key="gen_export_method"
        )

    # Show Pandoc-specific options if Pandoc is selected
    if "Pandoc" in export_method:
        pandoc_col1, pandoc_col2 = st.columns(2)

        with pandoc_col1:
            include_toc = st.checkbox(
                "Include Table of Contents",
                value=True,
                key="gen_include_toc"
            )

        with pandoc_col2:
            number_sections = st.checkbox(
                "Number Sections Automatically",
                value=True,
                key="gen_number_sections"
            )
    else:
        include_toc = False
        number_sections = False

    st.markdown("---")

    # ----------------------------
    # 5) Generate document
    # ----------------------------
    if st.button("Generate Documents", type="primary", key="generate_docs_main"):
        if not source_doc_ids:
            st.error("You must select at least one source document.")
        else:
            payload = {
                "source_collections": [source_collection],
                "source_doc_ids": source_doc_ids,
                "use_rag": True,
                "top_k": 5,
                "doc_title": out_name,
                "include_test_cards": include_test_cards,
                "export_format": "pandoc" if "Pandoc" in export_method else "python-docx",
                "include_toc": include_toc,
                "number_sections": number_sections
            }

            # Add agent_set_id
            agent_set = next((s for s in active_agent_sets if s['name'] == selected_agent_set), None)
            if agent_set:
                payload["agent_set_id"] = agent_set['id']
                st.info(f"Using agent set: **{selected_agent_set}**")

            with st.spinner("Generating documents... (This may take 5-15 minutes depending on document size)"):
                try:
                    response = api_client.post(
                        f"{config.endpoints.doc_gen}/generate_documents",
                        data=payload,
                        timeout=1200  # 20 minutes - sufficient for large documents with multiple agents
                    )

                    docs = response.get("documents", [])

                    if docs:
                        # Get the first/primary document or combine if multiple
                        if len(docs) == 1:
                            primary_doc = docs[0]
                            st.success(f"Generated document: {primary_doc['title']}")
                        else:
                            # Combine multiple documents into one
                            st.success(f"Generated and combined {len(docs)} chunks")
                            combined_content = []
                            combined_title = f"Combined_{out_name}"

                            for i, doc in enumerate(docs):
                                combined_content.append(
                                    f"## Document {i+1}: {doc['title']}\n\n{doc.get('content', '')}"
                                )

                            primary_doc = {
                                'title': combined_title,
                                'content': '\n\n---\n\n'.join(combined_content),
                                'docx_b64': docs[0].get('docx_b64', '')  # Use first doc's DOCX as base
                            }

                        # Provide immediate download
                        if 'docx_b64' in primary_doc and primary_doc['docx_b64']:
                            blob = base64.b64decode(primary_doc["docx_b64"])
                            st.download_button(
                                label=f"Download {primary_doc['title']}.docx",
                                data=blob,
                                file_name=f"{primary_doc['title']}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key="immediate_download"
                            )
                        else:
                            st.warning("Document generated but DOCX format not available")
                    else:
                        st.warning("No documents were generated")

                except Exception as e:
                    st.error(f"Failed to generate documents: {e}")

    # Info section with Phase 3 tips
    st.markdown("---")
    with st.expander("Tips & Information"):
        st.markdown("""
        ### Document Generation Tips

        **Test Card Options:**
        - **Include Test Cards**: Automatically generates executable test checklists for each section
        - Test cards include: Test ID, procedures, expected results, and acceptance criteria
        - After generation, view detailed test cards in the **Test Card Viewer** page

        **Export Methods:**
        - **Standard (python-docx)**: Basic Word document formatting
        - **Professional (Pandoc)**: Enhanced formatting with:
          - Auto-generated Table of Contents
          - Automatic section numbering
          - Professional typography
          - Better table rendering

        **Pro Tips:**
        - Use **Pandoc export** for client-facing documents
        - Enable **Test Cards** to create executable test plans
        - **TOC** and **Section Numbering** improve navigation in large documents
        - Visit **Test Card Viewer** to track test execution progress

        After clicking 'Generate Documents', your document will be created and ready for immediate download!
        """)
