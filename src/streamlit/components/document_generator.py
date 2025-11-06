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
    # 1) Pick agents
    # ----------------------------
    try:
        agents_response = api_client.get(f"{config.endpoints.agent}/get-agents")
        agents = agents_response.get("agents", [])
    except Exception as e:
        st.error(f"Failed to fetch agents: {e}")
        agents = st.session_state.get("available_rule_agents", [])

    if not agents:
        st.warning("No agents available. Please create agents first in the 'AI Agent' component.")
        st.stop()

    agent_map = {f"{a['name']} ({a['model_name']})": a["id"] for a in agents}
    selected_agents = st.multiselect(
        "Select Agents",
        list(agent_map.keys()),
        key="gen_agents"
    )

    if not selected_agents:
        st.info("Choose at least one agent to proceed")
        st.stop()

    # ----------------------------
    # 2) Get collections
    # ----------------------------
    if "collections" not in st.session_state:
        st.session_state.collections = chromadb_service.get_collections()

    collections = st.session_state.collections

    if not collections:
        st.warning("No collections available. Please upload documents first.")
        st.stop()

    # ----------------------------
    # 2a) Pick TEMPLATE collection & load template docs
    # ----------------------------
    template_collection = st.selectbox(
        "Template Collection (the one you uploaded as templates)",
        collections,
        key="gen_template_coll",
    )

    if st.button("Load Template Library", key="gen_load_templates"):
        with st.spinner("Loading templates..."):
            try:
                documents = chromadb_service.get_documents(template_collection)
                st.session_state.template_docs = [
                    {
                        'document_id': doc.document_id,
                        'document_name': doc.document_name
                    }
                    for doc in documents
                ]
                st.success(f"Loaded {len(documents)} templates")
            except Exception as e:
                st.error(f"Failed to load templates: {e}")

    template_docs = st.session_state.get("template_docs", [])
    template_map = {d["document_name"]: d["document_id"] for d in template_docs}
    selected_templates = st.multiselect(
        "Select Template(s)",
        list(template_map.keys()),
        key="gen_templates"
    )
    template_doc_ids = [template_map[name] for name in selected_templates]

    # ----------------------------
    # 2b) Pick SOURCE collection & load source docs
    # ----------------------------
    source_collection = st.selectbox(
        "Source Collection (your requirements/standards)",
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
    # 3) Get agent IDs
    # ----------------------------
    agent_ids = [agent_map[label] for label in selected_agents]

    # ----------------------------
    # 4) Let user name the output file
    # ----------------------------
    out_name = st.text_input(
        "Output file name (no extension):",
        value="Generated_Test_Plan",
        key="gen_filename"
    ).strip()

    # ----------------------------
    # 4b) Test Card & Export Options (Phase 3 Enhancement)
    # ----------------------------
    st.markdown("---")
    st.subheader("📋 Test Card & Export Options")

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
    # 5) Generate analyses
    # ----------------------------
    if st.button("Generate Documents", type="primary", key="generate_docs_main"):
        if not template_doc_ids or not source_doc_ids:
            st.error("You must select at least one template and one source document.")
        else:
            payload = {
                "template_collection": template_collection,
                "template_doc_ids": template_doc_ids,
                "source_collections": [source_collection],
                "source_doc_ids": source_doc_ids,
                "agent_ids": agent_ids,
                "use_rag": True,
                "top_k": 5,
                "doc_title": out_name,
                # Phase 3 enhancements
                "include_test_cards": include_test_cards,
                "export_format": "pandoc" if "Pandoc" in export_method else "python-docx",
                "include_toc": include_toc,
                "number_sections": number_sections
            }

            with st.spinner("Generating documents... (This may take a few minutes)"):
                try:
                    response = api_client.post(
                        f"{config.endpoints.doc_gen}/generate_documents",
                        data=payload,
                        timeout=600  # Increased timeout for test card generation
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
    with st.expander("ℹ️ Tips & Information"):
        st.markdown("""
        ### Document Generation Tips

        **Test Card Options:**
        - ✅ **Include Test Cards**: Automatically generates executable test checklists for each section
        - 📝 Test cards include: Test ID, procedures, expected results, and acceptance criteria
        - 🔄 After generation, view detailed test cards in the **Test Card Viewer** page

        **Export Methods:**
        - 📄 **Standard (python-docx)**: Basic Word document formatting
        - 🎨 **Professional (Pandoc)**: Enhanced formatting with:
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
