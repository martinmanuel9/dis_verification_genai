"""
Document Generator Component
Migrated to new architecture - uses centralized config and services
"""
import streamlit as st
import base64
from config.settings import config
from lib.api.client import api_client
from services.chromadb_service import chromadb_service
from components.agent_creator import create_agent_form


def Document_Generator():
    st.header("Document Generator")
    st.info("Upload templates, and generate comprehensive documentation using AI analysis.")

    # Document Generator sub-modes
    doc_gen_mode = st.radio(
        "Select Action:",
        ["Rule Development Agents", "Template Management", "Generate Documents"],
        horizontal=True
    )

    # RULE DEVELOPMENT AGENTS SUB-MODE
    if doc_gen_mode == "Rule Development Agents":
        # Use the unified agent creation component for rule development agents
        create_agent_form(
            template_category="rule_development",
            key_prefix="doc_gen",
            form_title="Create Rule Development Agent"
        )

    elif doc_gen_mode == "Template Management":
        st.subheader("Template Management")
        st.info("Upload and manage document templates for generation.")

        # Get collections
        if "collections" not in st.session_state:
            st.session_state.collections = chromadb_service.get_collections()

        collections = st.session_state.collections

        if collections:
            template_collection = st.selectbox(
                "Select Template Collection:",
                collections,
                key="template_mgmt_collection"
            )

            if st.button("View Templates", key="view_templates"):
                with st.spinner("Loading templates..."):
                    try:
                        documents = chromadb_service.get_documents(template_collection)
                        st.session_state.template_docs = [
                            {
                                'document_id': doc.document_id,
                                'document_name': doc.document_name,
                                'file_type': doc.file_type,
                                'total_chunks': doc.total_chunks
                            }
                            for doc in documents
                        ]
                        st.success(f"Found {len(documents)} templates")
                    except Exception as e:
                        st.error(f"Failed to load templates: {e}")

            # Display templates if loaded
            if st.session_state.get("template_docs"):
                st.write("**Available Templates:**")
                for template in st.session_state.template_docs:
                    with st.expander(f"{template['document_name']} ({template['file_type']})"):
                        st.write(f"Document ID: {template['document_id']}")
                        st.write(f"Total Chunks: {template['total_chunks']}")
        else:
            st.warning("No collections available. Please upload documents first.")

    elif doc_gen_mode == "Generate Documents":
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
            st.warning("No agents available. Please create agents first in 'Rule Development Agents' mode.")
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
                    "doc_title": out_name
                }

                with st.spinner("Generating documents..."):
                    try:
                        response = api_client.post(
                            f"{config.endpoints.doc_gen}/generate_documents",
                            data=payload,
                            timeout=300
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

        # Simple info section
        st.markdown("---")
        st.info("**Tip**: After clicking 'Generate Documents', your document will be created and ready for immediate download!")
