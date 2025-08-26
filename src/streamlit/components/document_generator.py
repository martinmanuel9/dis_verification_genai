import streamlit as st
import requests
import base64
from utils import *
from components.upload_documents import *
from components.agent_creator import create_agent_form


FASTAPI_API = os.getenv("FASTAPI_URL", "http://localhost:9020")

def Document_Generator():
    st.header("Standards-Requirements Test Plan Generator")
    st.info("Generate comprehensive standards-requirements test plans directly from your source documents using multi-actor + critic.")
    st.caption("Mode: Standards-Requirements (source-only)")
    # Use only the optimized version - remove confusing options
    strategy = "Optimized Multi-Agent Workflow"
    st.info("🚀 Using Optimized Multi-Agent Workflow with Redis streaming pipeline for comprehensive test plan generation")
    
    st.subheader("Generate Test Plans")

    # Using Test Plan Gen (actor + critic) strategy only
    supported_models = [
        "gpt-4", "gpt-3.5-turbo","llama"
    ]
    actor_models = st.multiselect(
        "Actor models (multi)",
        options=supported_models,
        default=["gpt-4"],
        help="Models used in parallel to extract detailed rules",
        key="gen_actor_models",
    )
    critic_model = st.selectbox(
        "Critic model",
        options=supported_models,
        index=0,
        help="Model used to synthesize and deduplicate the actors' outputs",
        key="gen_critic_model",
    )

    # No agents needed for actor + critic workflow
    agent_ids = []

    # ----------------------------
    # Select SOURCE documents for test plan generation
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
    # Output file name
    # ----------------------------
    out_name = st.text_input(
        "Output file name (no extension):",
        value="Generated_Test_Plan",
        key="gen_filename"
    ).strip()

    # Simplified tuning for optimized workflow
    with st.expander("Advanced tuning", expanded=False):
        max_actor_workers = st.number_input(
            "Max workers (parallel processing)", min_value=1, max_value=16, value=4, step=1,
            help="Number of parallel workers for section processing.",
            key="sr_max_actor_workers"
        )

    # Sectioning controls
    with st.expander("Sectioning", expanded=False):
        sectioning_strategy = st.selectbox(
            "Sectioning strategy",
            options=["auto", "by_chunks", "by_metadata"],
            index=0,
            help="How to break the source document(s) into sections for extraction.",
            key="sr_sectioning_strategy",
        )
        chunks_per_section = st.number_input(
            "Chunks per section (by_chunks)", min_value=1, max_value=50, value=15, step=1,
            help="When using by_chunks, how many vector chunks to group per section. Higher values = more comprehensive sections.",
            key="sr_chunks_per_section",
        )

        if st.button("Preview Sections", key="preview_sections_btn"):
            if not source_collection:
                st.warning("Select a source collection first.")
            elif not source_doc_ids:
                st.warning("Select at least one source document.")
            else:
                with st.spinner("Detecting sections…"):
                    try:
                        payload = {
                            "source_collections": [source_collection],
                            "source_doc_ids": source_doc_ids,
                            "sectioning_strategy": sectioning_strategy,
                            "chunks_per_section": int(chunks_per_section),
                        }
                        resp = requests.post(f"{FASTAPI_API}/preview-sections", json=payload, timeout=120)
                        if resp.ok:
                            data = resp.json()
                            st.success(f"Detected {data.get('count', 0)} sections")
                            names = data.get("section_names", [])
                            if names:
                                st.dataframe({"section": names}, use_container_width=True)
                            else:
                                st.info("No section names returned.")
                        else:
                            st.error(f"Preview failed: {resp.status_code} {resp.text}")
                    except Exception as e:
                        st.error(f"Preview error: {e}")

    # ----------------------------
    # Generate test plan
    # ----------------------------
    if st.button("Generate Test Plan", type="primary", key="generate_docs_main"):
        if not source_doc_ids:
            st.error("You must select at least one source document.")
        else:
            # Use optimized workflow only
            payload = {
                "source_collections": [source_collection],
                "source_doc_ids": source_doc_ids,
                "doc_title": out_name or "Comprehensive Test Plan",
                "max_workers": int(max_actor_workers),
                "sectioning_strategy": sectioning_strategy,
                "chunks_per_section": int(chunks_per_section),
            }
            endpoint = "/generate_optimized_test_plan"
            st.write("Processing with optimized Redis streaming pipeline...")
            
            st.write("Payload:", payload)
            progress_bar = st.progress(0)
            status_text = st.empty()
            with st.spinner("Generating Test Plan…"):
                try:
                    status_text.text("Starting document generation...")
                    progress_bar.progress(10)
                    resp = requests.post(f"{FASTAPI_API}{endpoint}", json=payload)
                    progress_bar.progress(100)
                    status_text.text("Document generation completed!")
                    # now resp is guaranteed to exist
                    if not resp.ok:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                    else:
                        docs = resp.json().get("documents", [])
                        if docs:
                            primary_doc = docs[0]
                            if 'docx_b64' in primary_doc:
                                blob = base64.b64decode(primary_doc["docx_b64"])
                                title = primary_doc.get("title", out_name or "Test_Plan")
                                st.success(f"Generated document: {title}")
                                st.download_button(
                                    label=f"Download {title}.docx",
                                    data=blob,
                                    file_name=f"{title}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key="immediate_download"
                                )
                                meta = primary_doc.get("meta") or {}
                                if meta:
                                    st.caption("Generation summary")
                                    if strategy == "Optimized Multi-Agent Workflow":
                                        # Show section-based workflow metrics
                                        st.write({
                                            "architecture": meta.get("architecture"),
                                            "processing_status": primary_doc.get("processing_status", "COMPLETED"),
                                            "total_sections": meta.get("total_sections"),
                                            "sections_with_tests": meta.get("sections_with_tests"),
                                            "total_testable_items": meta.get("total_testable_items"),
                                            "total_test_procedures": meta.get("total_test_procedures"),
                                            "section_based": meta.get("section_based"),
                                            "processing_optimized": meta.get("processing_optimized"),
                                            "cache_enabled": meta.get("cache_enabled"),
                                            "max_workers": meta.get("max_workers"),
                                        })
                                        
                                        # Show processing status
                                        processing_status = primary_doc.get("processing_status", "COMPLETED")
                                        st.success(f"Test Plan Generation: {processing_status}")
                                    else:
                                        # Show original workflow metrics
                                        st.write({
                                            "total_chunks": meta.get("total_chunks"),
                                            "actor_models": meta.get("actor_models"),
                                            "max_actor_workers": meta.get("max_actor_workers"),
                                            "critic_model": meta.get("critic_model"),
                                            "critic_batch_size": meta.get("critic_batch_size"),
                                            "critic_batch_char_cap": meta.get("critic_batch_char_cap"),
                                            "batches": meta.get("batches"),
                                            "batch_sizes": meta.get("batch_sizes"),
                                            "batch_char_lengths": meta.get("batch_char_lengths"),
                                        })
                            else:
                                st.warning("Document generated but DOCX format not available")
                        else:
                            st.warning("No documents were generated")
                except Exception as e:
                    st.error("Request exception: " + str(e))

        # Simple info section
        st.markdown("---")
        st.info("**Tip**: After clicking 'Generate Test Plan', your document will be created and ready for immediate download!")
