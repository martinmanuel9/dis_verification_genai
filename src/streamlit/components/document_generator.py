import streamlit as st
import requests
import base64
from utils import *
from components.upload_documents import *
from components.agent_creator import create_agent_form


FASTAPI_API = os.getenv("FASTAPI_URL", "http://localhost:9020")

def Document_Generator():
    st.header("Document Generator")
    st.info("Upload templates, and generate comprehensive documentation using AI analysis.")
    
    # Document Generator sub-modes
    doc_gen_mode = st.radio(
        "Select Action:",
        ["Rule Development Agents", "Generate Documents"],
        horizontal=True
    )
    
    # ----------------------------------------------------------------------
    # RULE DEVELOPMENT AGENTS SUB-MODE
    # ----------------------------------------------------------------------
    if doc_gen_mode == "Rule Development Agents":
        # Use the unified agent creation component for rule development agents
        create_agent_form(
            template_category="rule_development",
            key_prefix="doc_gen",
            form_title="Create Rule Development Agent"
        )
    
    
    elif doc_gen_mode == "Generate Documents":
        st.subheader("Generate Test Plans")

        # ----------------------------
        # 1) Pick agents
        # ----------------------------
        agents = st.session_state.get("available_rule_agents") or requests.get(f"{FASTAPI_API}/get-agents").json()["agents"]
        # rule_agents = [a for a in agents if "rule" in a["name"].lower()]
        agent_map = {f"{a['name']} ({a['model_name']})": a["id"] for a in agents}
        selected_agents = st.multiselect("Select Agents", list(agent_map.keys()), key="gen_agents")
        if not selected_agents:
            st.info("Choose at least one agent to proceed"); st.stop()

        # ----------------------------
        # 2a) Pick TEMPLATE collection & load template docs
        # ----------------------------
        template_collection = st.selectbox(
            "Template Collection (the one you uploaded as templates)",
            st.session_state.collections,
            key="gen_template_coll",
        )
        if st.button("Load Template Library", key="gen_load_templates"):
            st.session_state.template_docs = get_all_documents_in_collection(template_collection)

        template_docs = st.session_state.get("template_docs", [])
        template_map = {d["document_name"]: d["document_id"] for d in template_docs}
        selected_templates = st.multiselect(
            "Select Template(s)", list(template_map.keys()), key="gen_templates"
        )
        template_doc_ids = [template_map[name] for name in selected_templates]

        # ----------------------------
        # 2b) Pick SOURCE collection & load source docs
        # ----------------------------
        source_collection = st.selectbox(
            "Source Collection (your requirements/standards)",
            st.session_state.collections,
            key="gen_source_coll",
        )
        if st.button("Load Source Documents", key="gen_load_sources"):
            st.session_state.source_docs = get_all_documents_in_collection(source_collection)

        source_docs = st.session_state.get("source_docs", [])
        source_map = {d["document_name"]: d["document_id"] for d in source_docs}
        selected_sources = st.multiselect(
            "Select Source Document(s)", list(source_map.keys()), key="gen_sources"
        )
        source_doc_ids = [source_map[name] for name in selected_sources]

        # ----------------------------
        # 3) Pick agents 
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
                st.error("You must select at least one templated and one source doc.")
            else:
                payload = {
                    "template_collection": template_collection,
                    "template_doc_ids":    template_doc_ids,
                    "source_collections":  [source_collection],
                    "source_doc_ids":      source_doc_ids,
                    "agent_ids":           agent_ids,
                    "use_rag":             True,
                    "top_k":               5,
                    "doc_title":           out_name
                }
                st.write("about to call /generate_documents on", FASTAPI_API)
                st.write("Payload:", payload)
                with st.spinner("Calling Document Generator…"):
                    try:
                        resp = requests.post(
                            f"{FASTAPI_API}/generate_documents",
                            json=payload
                            # timeout=300
                        )
                        # now resp is guaranteed to exist
                        if not resp.ok:
                            st.error(f"Error {resp.status_code}: {resp.text}")
                        else:
                            docs = resp.json().get("documents", [])
                            
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
                                        combined_content.append(f"## Document {i+1}: {doc['title']}\n\n{doc.get('content', '')}")
                                    
                                    primary_doc = {
                                        'title': combined_title,
                                        'content': '\n\n---\n\n'.join(combined_content),
                                        'docx_b64': docs[0].get('docx_b64', '')  # Use first doc's DOCX as base
                                    }
                                
                                # Provide immediate download
                                if 'docx_b64' in primary_doc:
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
                            st.error("Request exception: " + str(e))

        # Simple info section
        st.markdown("---")
        st.info("**Tip**: After clicking 'Generate Documents', your document will be created and ready for immediate download!")


