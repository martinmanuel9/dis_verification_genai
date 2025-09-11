import streamlit as st
import requests
import base64
import os
import time
from utils import *
from components.upload_documents import *
from components.agent_creator import create_agent_form


FASTAPI_API = os.getenv("FASTAPI_URL", "http://localhost:9020")

def _trigger_rerun():
    st.session_state['__last_refresh'] = time.time()
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

def Document_Generator():
    st.header("Standards-Requirements Test Plan Generator")
    st.info("Generate comprehensive standards-requirements test plans directly from your source documents using multi-actor + critic.")
    st.caption("Mode: Standards-Requirements (source-only)")
    # Use only the optimized version - remove confusing options
    strategy = "Optimized Multi-Agent Workflow"

    st.subheader("Generate Test Plans")

    # Using Test Plan Gen (actor + critic) strategy only
    supported_models = [
        "gpt-4", "gpt-3.5-turbo", "gpt-oss", "llama"
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

    # Processing method selection
    with st.expander("Processing Options", expanded=False):
        processing_method = st.radio(
            "Processing Method",
            options=["Auto (Recommended)", "Direct Processing", "Multi-Agent Pipeline"],
            index=0,
            help="Auto: Chooses best method based on document size. Direct: Fast for simple docs. Pipeline: Comprehensive for complex docs.",
            key="processing_method"
        )
        
        if processing_method == "Multi-Agent Pipeline":
            max_actor_workers = st.number_input(
                "Max workers (parallel processing)", min_value=1, max_value=16, value=4, step=1,
                help="Number of parallel workers for section processing.",
                key="sr_max_actor_workers"
            )
        else:
            max_actor_workers = 4  # Default for other methods

    # Sectioning controls
    with st.expander("Sectioning", expanded=False):
        sectioning_strategy = st.selectbox(
            "Sectioning strategy",
            options=["smart", "by_chunks", "by_metadata"],
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
    # Pipelines view disabled
    st.caption("Pipelines view is disabled.")

    # Pipelines API removed

    # Disable legacy pipelines UI
    auto_refresh = False
    pipelines_data = None
    # Inject auto-refresh if enabled (fixed concise interval)
    if auto_refresh:
        st.caption("Auto-refresh enabled")
        st.markdown(
            """
            <script>
            setTimeout(function(){
                window.location.reload();
            }, 8000);
            </script>
            """,
            unsafe_allow_html=True,
        )

    """
    if not pipelines_data:
        st.caption("No pipelines currently processing.")
    else:
        for i, p in enumerate(pipelines_data):
            pid = p.get("pipeline_id")
            title = p.get("title")
            status = p.get("status")
            total = p.get("total_sections", 0)
            done = p.get("sections_processed", 0)
            pct = int((done / total) * 100) if total else 0

            with st.container(border=True):
                st.write(f"**{title}**")
                st.caption(f"Pipeline: {pid}")
                st.progress(min(pct, 100))
                st.caption(f"Status: {status} | {done}/{total} sections processed")
                # Fallback info if present
                if p.get('model_fallback'):
                    st.caption(f"Fallback: {p.get('model_fallback')} ({p.get('fallback_reason')})")
                # Export from Chroma if saved
                gen_doc_id = p.get('generated_document_id')
                proposed_id = p.get('proposed_document_id')
                doc_track = p.get('doc_tracking')
                if doc_track:
                    st.caption(f"Doc tracking: {doc_track}")
                if gen_doc_id:
                    gen_coll = p.get('generated_collection') or os.getenv('GENERATED_TESTPLAN_COLLECTION', 'generated_test_plan')
                    st.caption(f"Saved: {gen_doc_id}")
                elif proposed_id:
                    st.caption(f"Proposed ID: {proposed_id}")
                    if st.button("Export (Chroma)", key=f"pp_list_export_{i}"):
                        try:
                            payload = {"document_id": gen_doc_id, "collection_name": gen_coll}
                            exp = requests.post(f"{FASTAPI_API}/export-testplan-word", json=payload, timeout=30)
                            if exp.ok:
                                data = exp.json()
                                fname = data.get('filename', f"{title.replace(' ', '_')}.docx")
                                import base64 as _b64
                                blob = _b64.b64decode(data.get('content_b64') or '')
                                st.download_button(
                                    label=f"Download {fname}",
                                    data=blob,
                                    file_name=fname,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"pp_list_export_dl_{i}"
                                )
                            else:
                                st.warning(f"Export failed: {exp.status_code}")
                        except Exception as e:
                            st.warning(f"Export error: {e}")
                    # Controls by status
                    if status in ("PROCESSING", "INITIALIZING"):
                        c1, c2 = st.columns([1,1])
                        with c1:
                            if st.button("Abort", key=f"pp_abort_{i}"):
                                try:
                                    aresp = requests.post(f"{FASTAPI_API}/testplan/pipelines/{pid}/abort", params={"purge": False, "remove_generated": True}, timeout=15)
                                    if aresp.ok:
                                        st.success("Abort requested")
                                        _trigger_rerun()
                                    else:
                                        st.warning(f"Abort failed: {aresp.status_code}")
                                except Exception as e:
                                    st.warning(f"Abort error: {e}")
                        with c2:
                            if st.button("Abort & Purge", key=f"pp_abort_purge_{i}"):
                                try:
                                    aresp = requests.post(f"{FASTAPI_API}/testplan/pipelines/{pid}/abort", params={"purge": True, "remove_generated": True}, timeout=20)
                                    if aresp.ok:
                                        st.success("Aborted and purge requested")
                                        _trigger_rerun()
                                    else:
                                        st.warning(f"Abort&purge failed: {aresp.status_code}")
                                except Exception as e:
                                    st.warning(f"Abort&purge error: {e}")
                    else:
                        # For non-processing, offer purge and generated doc removal (if any)
                        c1, c2, c3 = st.columns([1,1,1])
                        with c1:
                            if st.button("Purge Keys", key=f"pp_purge_{i}"):
                                try:
                                    presp = requests.post(f"{FASTAPI_API}/testplan/pipelines/{pid}/purge", timeout=15)
                                    if presp.ok:
                                        st.success("Pipeline purged")
                                        _trigger_rerun()
                                    else:
                                        st.warning(f"Purge failed: {presp.status_code}")
                                except Exception as e:
                                    st.warning(f"Purge error: {e}")
                        with c2:
                            if gen_doc_id and st.button("Remove Generated Doc", key=f"pp_rm_doc_{i}"):
                                try:
                                    # Prefer pipeline-based convenience endpoint
                                    rmd = requests.post(f"{FASTAPI_API}/testplan/pipelines/{pid}/remove-generated", params={"collection_name": gen_coll}, timeout=20)
                                    if rmd.ok:
                                        st.success("Removed generated doc")
                                        _trigger_rerun()
                                    else:
                                        st.warning(f"Remove failed: {rmd.status_code}")
                                except Exception as e:
                                    st.warning(f"Remove error: {e}")
                        with c3:
                            if st.button("Cleanup (Doc + Keys)", key=f"pp_cleanup_{i}"):
                                try:
                                    cresp = requests.post(f"{FASTAPI_API}/testplan/pipelines/{pid}/cleanup", params={"remove_generated": True}, timeout=30)
                                    if cresp.ok:
                                        st.success("Cleanup completed")
                                        _trigger_rerun()
                                    else:
                                        st.warning(f"Cleanup failed: {cresp.status_code}")
                                except Exception as e:
                                    st.warning(f"Cleanup error: {e}")
                # Details
                if st.button("View details", key=f"pp_view_{i}"):
                        try:
                            dresp = requests.get(f"{FASTAPI_API}/testplan/pipelines/{pid}", timeout=10)
                            if dresp.ok:
                                det = dresp.json()
                                sections = det.get("sections", [])
                                st.write({
                                    "title": det.get("meta", {}).get("title"),
                                    "status": det.get("meta", {}).get("status"),
                                    "total_sections": det.get("meta", {}).get("total_sections"),
                                    "sections_processed": det.get("meta", {}).get("sections_processed"),
                                })
                                # Fallback info if present
                                if det.get("meta", {}).get("model_fallback"):
                                    st.caption(
                                        f"Fallback: {det['meta'].get('model_fallback')} ("
                                        f"{det['meta'].get('fallback_reason')})"
                                    )
                                # Consistent saved ID display
                                _meta = det.get("meta", {})
                                _saved_id = _meta.get("generated_document_id")
                                _saved_coll = _meta.get("collection") or os.getenv('GENERATED_TESTPLAN_COLLECTION', 'generated_test_plan')
                                if _saved_id:
                                    st.caption(f"Saved in Chroma: { _saved_id } ({ _saved_coll })")
                                # Show a small table of section statuses
                                if sections:
                                    import pandas as pd
                                    df = pd.DataFrame(sections)
                                    st.dataframe(df, use_container_width=True, height=240)
                                # If final result exists and completed, offer export
                                final_res = det.get("final_result") or {}
                                if final_res.get("processing_status") == "COMPLETED":
                                    if st.button("Export DOCX", key=f"pp_export_{i}"):
                                        try:
                                            exp = requests.get(f"{FASTAPI_API}/export-pipeline-word/{pid}", timeout=30)
                                            if exp.ok:
                                                data = exp.json()
                                                fname = data.get('filename', f"{title.replace(' ', '_')}.docx")
                                                import base64 as _b64
                                                blob = _b64.b64decode(data.get('content_b64') or '')
                                                st.download_button(
                                                    label=f"Download {fname}",
                                                    data=blob,
                                                    file_name=fname,
                                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                    key=f"pp_export_dl_{i}"
                                                )
                                            else:
                                                st.warning(f"Export failed: {exp.status_code}")
                                        except Exception as e:
                                            st.warning(f"Export error: {e}")
                                    # If Chroma doc id recorded, offer export from Chroma and purge
                                    meta = det.get("meta", {})
                                    gen_doc_id = meta.get("generated_document_id")
                                    gen_coll = meta.get("collection") or os.getenv('GENERATED_TESTPLAN_COLLECTION', 'generated_test_plan')
                                    if gen_doc_id:
                                        if st.button("Export from Chroma", key=f"pp_export_chroma_{i}"):
                                            try:
                                                payload = {"document_id": gen_doc_id, "collection_name": gen_coll}
                                                exp = requests.post(f"{FASTAPI_API}/export-testplan-word", json=payload, timeout=30)
                                                if exp.ok:
                                                    data = exp.json()
                                                    fname = data.get('filename', f"{title.replace(' ', '_')}.docx")
                                                    import base64 as _b64
                                                    blob = _b64.b64decode(data.get('content_b64') or '')
                                                    st.download_button(
                                                        label=f"Download {fname}",
                                                        data=blob,
                                                        file_name=fname,
                                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                        key=f"pp_export_chroma_dl_{i}"
                                                    )
                                                else:
                                                    st.warning(f"Export failed: {exp.status_code}")
                                            except Exception as e:
                                                    st.warning(f"Export error: {e}")
                                        if det.get("meta", {}).get("status") in ("ABORTED", "ABORTING"):
                                            if st.button("Delete from Chroma", key=f"pp_del_chroma_{i}"):
                                                try:
                                                    dresp = requests.delete(f"{FASTAPI_API}/generated-testplan/{gen_doc_id}", params={"collection_name": gen_coll}, timeout=15)
                                                    if dresp.ok:
                                                        st.success("Deleted from Chroma")
                                                    else:
                                                        st.warning(f"Delete failed: {dresp.status_code}")
                                                except Exception as e:
                                                    st.warning(f"Delete error: {e}")
                            else:
                                st.warning(f"Detail fetch failed: {dresp.status_code}")
                        except Exception as e:
                            st.warning(f"Failed to load details: {e}")

        # Simple info section
        st.markdown("---")
        st.info("**Tip**: After clicking 'Generate Test Plan', your document will be created and ready for immediate download!")
    """

    # Recent Generated Test Plans panel removed

    # ----------------------------
    # Generate test plan
    # ----------------------------
    if st.button("Generate Test Plan", type="primary", key="generate_docs_main"):
        if not source_doc_ids:
            st.error("You must select at least one source document.")
        else:
            # Determine processing method
            use_direct = None
            if processing_method == "Direct Processing":
                use_direct = True
            elif processing_method == "Multi-Agent Pipeline":
                use_direct = False
            # Auto lets the service decide
            
            payload = {
                "source_collections": [source_collection],
                "source_doc_ids": source_doc_ids,
                "doc_title": out_name or "Comprehensive Test Plan",
                "max_workers": int(max_actor_workers),
                "sectioning_strategy": sectioning_strategy,
                "chunks_per_section": int(chunks_per_section),
                "use_direct_processing": use_direct
            }
            endpoint = "/generate"
            
            if processing_method == "Direct Processing":
                st.write("Processing with direct LLM generation (fast)...")
            elif processing_method == "Multi-Agent Pipeline":
                st.write("Processing with multi-agent Redis pipeline (comprehensive)...")
            else:
                st.write("Processing with auto-selected method...")
            
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
                    
   
