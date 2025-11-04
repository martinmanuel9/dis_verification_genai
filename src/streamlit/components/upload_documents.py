import streamlit as st
import requests
import time
import re
import pandas as pd
from sentence_transformers import SentenceTransformer
from config.constants import EMBEDDING_MODEL_NAME
from config.settings import config
from services.chromadb_service import chromadb_service
from lib.utils import render_reconstructed_document


@st.cache_resource(show_spinner=False)
def get_embedding_model() -> SentenceTransformer:
    """Cache the embedding model to avoid reloading on every query."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)

def browse_documents(key_prefix: str = "",):
    def pref(k): return f"{key_prefix}_{k}" if key_prefix else k
    if st.session_state.collections:
        col = st.selectbox("Select Collection to Browse", st.session_state.collections, key=pref("browse_collection"))
        if st.button("Load Documents", key=pref("load_documents")):
            st.session_state.documents = chromadb_service.get_documents(col)

        #set collection name in session state for later use
        st.session_state.selected_collection = col

        if "documents" in st.session_state:
            docs = st.session_state.documents
            if docs:
                # Convert Pydantic objects to dicts for DataFrame
                docs_dicts = [doc.dict() if hasattr(doc, 'dict') else doc for doc in docs]
                df = pd.DataFrame(docs_dicts)
                st.dataframe(df, width='stretch')
            else:
                st.info("No documents found in this collection.")
    else:
        st.warning("No collections available. Upload or create one first.") 

def query_documents(key_prefix: str = "",):
    def pref(k): return f"{key_prefix}_{k}" if key_prefix else k
    if st.session_state.collections:
        query_collection = st.selectbox("Select Collection to Query", st.session_state.collections, key=pref("query_collection"))
        query_text = st.text_input("Enter your search query", placeholder="e.g., 'dog with tongue out' or 'red square with text'", key=pref("query_text"))
        n_results = st.slider("Number of results", min_value=1, max_value=20, value=5)
        
        if query_text and st.button("Search Documents", key=pref("search_documents")):
            with st.spinner("Searching..."):
                try:
                    embedding_model = get_embedding_model()
                    query_vector = embedding_model.encode([query_text]).tolist()[0]
                    results = chromadb_service.query_documents(
                        collection_name=query_collection,
                        query_text=query_text,
                        query_embedding=query_vector,
                        n_results=n_results
                    )
                except Exception as e:
                    st.error(f"Query failed: {e}")
                    return

                if results:
                    st.success(f"Found {len(results['ids'][0])} results")
                    
                    # Display results
                    for i, (doc_id, document, metadata, distance) in enumerate(zip(
                        results['ids'][0], 
                        results['documents'][0], 
                        results['metadatas'][0], 
                        results['distances'][0]
                    )):
                        with st.expander(f"Result {i+1} - Score: {1-distance:.3f}"):
                            st.write(f"**Document**: {metadata.get('document_name', 'Unknown')}")
                            st.write(f"**Chunk**: {metadata.get('chunk_index', 0)} of {metadata.get('total_chunks', 0)}")
                            st.write(f"**Has Images**: {metadata.get('has_images', False)}")
                            if metadata.get('has_images'):
                                st.write(f"**Image Count**: {metadata.get('image_count', 0)}")
                            
                            st.text_area("Content", document, height=150, key=f"content_{i}")
                            
                            # Show document ID for easy reconstruction
                            st.code(f"Document ID: {metadata.get('document_id', 'Unknown')}")
                                
def view_images(key_prefix: str = "",):
    def pref(k): return f"{key_prefix}_{k}" if key_prefix else k

    # Initialize session state for reconstruction result
    result_key = pref("reconstructed_result")
    if result_key not in st.session_state:
        st.session_state[result_key] = None

    if st.session_state.collections:
        reconstruct_collection = st.selectbox("Select Collection", st.session_state.collections, key=pref("reconstruct_collection"))

        # Load documents in the selected collection (like Document Generator)
        if st.button("Load Documents", key=pref("load_reconstruct_docs")):
            try:
                with st.spinner("Loading documents…"):
                    st.session_state.reconstruct_docs = chromadb_service.get_documents(reconstruct_collection)
            except Exception as e:
                st.error(f"Failed to load documents: {e}")

        docs = st.session_state.get("reconstruct_docs", [])
        # Handle both Pydantic objects and dicts
        name_to_id = {
            (d.document_name if hasattr(d, 'document_name') else d["document_name"]):
            (d.document_id if hasattr(d, 'document_id') else d["document_id"])
            for d in docs
        }
        selected_name = st.selectbox(
            "Select Document",
            list(name_to_id.keys()) if docs else [],
            key=pref("reconstruct_doc_select")
        )
        document_id = name_to_id.get(selected_name)

        if st.button("Reconstruct Document", disabled=not document_id, key=pref("reconstruct_document")):
            try:
                with st.spinner("Reconstructing document..."):
                    result = chromadb_service.reconstruct_document(
                        document_id=document_id,
                        collection_name=reconstruct_collection
                    )

                # Store result in session state
                st.session_state[result_key] = result
                st.success(f"✅ Document reconstructed: {result['document_name']}")

            except Exception as e:
                st.error(f"❌ Error reconstructing document: {str(e)}")

        # Display reconstruction result if it exists (outside button conditional)
        if st.session_state[result_key]:
            result = st.session_state[result_key]

            # Show document info
            with st.expander("Document Information"):
                st.write(f"**Document ID**: {result['document_id']}")
                st.write(f"**Document Name**: {result['document_name']}")
                st.write(f"**Total Chunks**: {result['total_chunks']}")
                st.write(f"**File Type**: {result['metadata']['file_type']}")
                st.write(f"**Total Images**: {result['metadata']['total_images']}")
                if 'ocr_pages' in result.get('metadata', {}):
                    st.write(f"**Pages with OCR**: {result['metadata']['ocr_pages']}")
                vm_used = result.get('metadata', {}).get('vision_models_used') or []
                if vm_used:
                    st.write(f"**Vision Models Used**: {', '.join(vm_used)}")

            # Build rich markdown with embedded images
            render_reconstructed_document(result)

            # ---- EXPORT DOCUMENTS (SEPARATE SECTION) ----
            st.markdown("---")  # Visual separator
            st.subheader("📄 Export Document")

            # Initialize session state for export
            export_state_key = pref("export_word_data")
            if export_state_key not in st.session_state:
                st.session_state[export_state_key] = None

            # Use centralized FastAPI word_export_service for Word export
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📝 Export to Word", key=pref("export_reconstructed_word"), use_container_width=True):
                    try:
                        with st.spinner("Generating Word document…"):
                            export_resp = requests.post(
                                f"{config.endpoints.doc_gen}/export-reconstructed-word",
                                json=result,
                                timeout=60
                            )
                            export_resp.raise_for_status()
                        payload = export_resp.json()
                        b64 = payload.get("content_b64")
                        filename = payload.get("filename", f"{result['document_name']}.docx")

                        if b64:
                            import base64
                            blob = base64.b64decode(b64)
                            # Store in session state
                            st.session_state[export_state_key] = {
                                "data": blob,
                                "filename": filename
                            }
                            st.success("✅ Word document ready!")
                        else:
                            st.error("No file returned from export service.")
                    except Exception as e:
                        st.error(f"❌ Error exporting: {e}")

            # Show download button if export data exists in session state
            with col2:
                if st.session_state[export_state_key]:
                    export_data = st.session_state[export_state_key]
                    st.download_button(
                        label=f"📥 Download {export_data['filename']}",
                        data=export_data["data"],
                        file_name=export_data["filename"],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=pref("download_reconstructed_word"),
                        use_container_width=True
                    )

def render_upload_component(
    available_collections: list[str],
    load_collections_func: callable,
    create_collection_func: callable,
    upload_endpoint: str,
    job_status_endpoint: str,
    key_prefix: str = "",
):
    """
    Renders a unified document upload & ingestion UI.

    Parameters:
    - available_collections: current list of collection names
    - load_collections_func: fn() -> list[str], repopulates collections
    - create_collection_func: fn(name: str) -> dict, creates a new collection
    - upload_endpoint: URL to POST files to
    - job_status_endpoint: URL template to poll job status, e.g. .../jobs/{job_id}
    """
    def pref(k): return f"{key_prefix}_{k}" if key_prefix else k
    
    with st.container(border=True, key=pref("upload_container")):
        st.header("Upload & Ingesting")
        # # Refresh collections
        col_refresh, _ = st.columns([1, 3])
        with col_refresh:
            if st.button("Refresh Collections", key=pref("refresh_collections")):
                try:
                    with st.spinner("Loading collections..."):
                        new = load_collections_func()
                        st.session_state.collections = new
                        st.success("Collections updated")
                        st.dataframe(new, width='stretch')
                except Exception as e:
                    st.error(f"Failed to load collections: {e}")
        

        # Choose to use or create
        action = st.radio(
            "Collection Action:",
            ["Use Existing Collection", "Create New Collection"],
            horizontal=True,
            key=pref("create_or_use")
        )

        target_collection = None
        if action == "Use Existing Collection":
            if available_collections:
                target_collection = st.selectbox(
                    "Select Collection:",
                    available_collections,
                    key=pref("browse_collection")
                )
            else:
                st.warning("No collections available. Create one below.")
        else:
            new_name = st.text_input(
                "New Collection Name:",
                placeholder="e.g. standards, templates, policies"
            )
            
            if new_name:
                # Normalize collection name according to ChromaDB rules
                normalized_name = new_name.strip().lower()
                # Replace spaces with underscores
                normalized_name = normalized_name.replace(' ', '_')
                # Keep only alphanumeric, underscores, and hyphens
                normalized_name = re.sub(r'[^a-zA-Z0-9_-]', '', normalized_name)
                # Ensure it starts and ends with alphanumeric
                normalized_name = re.sub(r'^[^a-zA-Z0-9]+', '', normalized_name)
                normalized_name = re.sub(r'[^a-zA-Z0-9]+$', '', normalized_name)
                
                # Ensure length is 3-63 characters
                if len(normalized_name) < 3:
                    normalized_name = normalized_name + "_collection"
                elif len(normalized_name) > 63:
                    normalized_name = normalized_name[:60] + "..."
                    # Ensure it still ends with alphanumeric after truncation
                    normalized_name = re.sub(r'[^a-zA-Z0-9]+$', '', normalized_name)
                
                # Show normalization if changed
                if normalized_name != new_name:
                    st.info(f"Collection name will be normalized to: `{normalized_name}`")
                
                # Validate final name
                if len(normalized_name) < 3:
                    st.error("Collection name must be at least 3 characters after normalization")
                    new_name = None
                else:
                    new_name = normalized_name
                    
            if new_name:
                if st.button("Create Collection"):
                    try:
                        with st.spinner(f"Creating '{new_name}'..."):
                            create_collection_func(new_name)
                            st.success(f"Created collection '{new_name}'")
                            target_collection = new_name
                    except Exception as e:
                        st.error(f"Failed to create collection: {e}")

        st.markdown("---")
        st.subheader("Upload Documents")
        uploaded = st.file_uploader(
            "Select files to upload:",
            type=['pdf', 'docx', 'txt', 'xlsx', 'pptx', 'html', 'csv'],
            accept_multiple_files=True,
            key=pref("files")
        )

        st.subheader("Ingest Web URL")
        url = st.text_input(
            "Enter product page URL (optional):",
            placeholder="https://example.com/product/1234",
            key="ingest_url"
        )

        # Vision model selection
        st.subheader("Vision Models")
        openai_v = st.checkbox("OpenAI Vision", value=False, key=pref("openai_vision"))
        # ollama_v = st.checkbox("Ollama Vision", value=False, key=pref("ollama_vision"))
        hf_v = st.checkbox("HuggingFace BLIP Vision", value=False, key=pref("hf_vision"))
        enhanced_v = st.checkbox("Enhanced Vision Model", value=False, key=pref("enhanced_vision"))
        basic_v = st.checkbox("Basic Vision Model", value=False, key=pref("basic_vision"))
        vision_models = []
        if openai_v: vision_models.append("openai")
        # if ollama_v: vision_models.append("ollama")
        if hf_v: vision_models.append("huggingface")
        if enhanced_v: vision_models.append("enhanced_local")
        if basic_v: vision_models.append("basic")

        # Chunk settings
        st.subheader("Chunk Settings")
        chunk_size = st.number_input("Chunk Size", min_value=500, max_value=5000, value=1000, key=pref("chunk_size"))
        chunk_overlap = st.number_input("Chunk Overlap", min_value=0, max_value=chunk_size//2, value=200, key=pref("chunk_overlap"))

        if st.button("Upload and Process", key=pref("upload_button")):
            if not target_collection:
                st.error("Please select or create a collection first.")
            elif not uploaded and not url:
                st.error("Please choose at least one file or enter a URL.")
            else:
                # prepare payload - DIRECTLY from uploaded files (like extend-refactor branch)
                if uploaded:
                    st.info(f"Processing {len(uploaded)} file(s): {[f.name for f in uploaded]}")
                    # Build files list directly from uploaded file objects
                    files = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in uploaded]
                    st.success(f"Built files list with {len(files)} file(s), total size: {sum(len(f[1][1]) for f in files)} bytes")
                    params = {
                        "collection_name": target_collection,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                        "store_images": True,
                        "model_name": "enhanced",
                        "vision_models": ",".join(vision_models),
                    }

                    try:
                        with st.spinner("Uploading and processing files…"):
                            resp = requests.post(upload_endpoint, files=files, params=params, timeout=300)
                            if resp.status_code != 200:
                                st.error(f"Upload failed with status {resp.status_code}")
                                st.error(f"Response: {resp.text}")
                                return
                            resp.raise_for_status()
                            job_id = resp.json().get("job_id")
                        # Overall progress
                        overall_progress = st.progress(0)
                        overall_status_text = st.empty()
                        
                        # Document-specific progress containers
                        doc_containers = {}
                        doc_progress_bars = {}
                        doc_status_texts = {}
                        
                        while True:
                            time.sleep(1)
                            job_status = requests.get(job_status_endpoint.format(job_id=job_id)).json()
                            total = job_status.get("total_chunks", 0)
                            done = job_status.get("processed_chunks", 0)
                            total_docs = job_status.get("total_documents", 0)
                            done_docs = job_status.get("processed_documents", 0)
                            documents = job_status.get("documents", [])
                            
                            # Update overall progress - use document completion primarily
                            if total_docs > 0:
                                # Calculate progress based on document completion + chunk progress within current documents
                                doc_completion_pct = (done_docs / total_docs) * 80  # 80% weight for completed docs
                                
                                # Add partial progress for documents currently being processed
                                current_doc_progress = 0
                                processing_docs = [d for d in documents if d["status"] == "processing"]
                                if processing_docs and total_docs > done_docs:
                                    # Average progress of currently processing documents
                                    avg_current_progress = sum(
                                        (d["chunks_processed"] / max(d["chunks_total"], 1)) * 100 
                                        for d in processing_docs
                                    ) / len(processing_docs)
                                    current_doc_progress = (avg_current_progress / 100) * (20 / total_docs)  # 20% weight distributed
                                
                                overall_pct = min(int(doc_completion_pct + current_doc_progress), 100)
                            else:
                                overall_pct = int(done/total*100) if total else 0
                            
                            overall_progress.progress(overall_pct)
                            
                            # Enhanced status text
                            if total_docs > 0:
                                status_summary = []
                                pending_count = len([d for d in documents if d["status"] == "pending"])
                                processing_count = len([d for d in documents if d["status"] == "processing"])
                                completed_count = len([d for d in documents if d["status"] == "completed"])
                                failed_count = len([d for d in documents if d["status"] == "failed"])
                                
                                if pending_count > 0:
                                    status_summary.append(f"{pending_count} pending")
                                if processing_count > 0:
                                    status_summary.append(f"{processing_count} processing")
                                if completed_count > 0:
                                    status_summary.append(f"{completed_count} completed")
                                if failed_count > 0:
                                    status_summary.append(f"{failed_count} failed")
                                
                                overall_status_text.text(f"Progress: {overall_pct}% | {' | '.join(status_summary)} | Chunks: {done}/{total}")
                            else:
                                overall_status_text.text(f"Overall: {done}/{total} chunks processed ({done_docs}/{total_docs} documents)")
                            
                            # Update individual document progress
                            for doc in documents:
                                doc_idx = doc["index"]
                                filename = doc["filename"]
                                doc_status = doc["status"]
                                chunks_done = doc["chunks_processed"]
                                chunks_total = doc["chunks_total"]
                                
                                if doc_idx not in doc_containers:
                                    doc_containers[doc_idx] = st.container()
                                    with doc_containers[doc_idx]:
                                        st.write(f"**{filename}**")
                                        doc_progress_bars[doc_idx] = st.progress(0)
                                        doc_status_texts[doc_idx] = st.empty()
                                
                                # Update progress bar
                                if chunks_total > 0:
                                    doc_pct = int(chunks_done / chunks_total * 100)
                                    doc_progress_bars[doc_idx].progress(min(doc_pct, 100))
                                
                                # Update status text with appropriate emoji
                                status_text = {
                                    "pending": "Pending",
                                    "processing": "Processing",
                                    "completed": "Completed!",
                                    "failed": "FAILED"
                                }.get(doc_status, "?")
                                
                                if doc_status == "failed":
                                    error_msg = doc.get("error_message", "Unknown error")
                                    doc_status_texts[doc_idx].text(f"{status_text}: {error_msg}")
                                else:
                                    doc_status_texts[doc_idx].text(f"{status_text}: {chunks_done}/{chunks_total} chunks")
                            
                            if job_status.get("status") in ("success","failed"): 
                                # Final update: ensure all progress bars show completion
                                overall_progress.progress(100)
                                overall_status_text.text("Processing complete!")
                                
                                # Update all document progress bars to 100% on success
                                if job_status.get("status") == "success":
                                    for doc in documents:
                                        doc_idx = doc["index"]
                                        if doc_idx in doc_progress_bars:
                                            doc_progress_bars[doc_idx].progress(100)
                                            doc_status_texts[doc_idx].text("Completed: 100%")
                                break
                        
                        if job_status.get("status") == "success":
                            st.success("File ingestion complete!")
                            latest = job_status.get("latest_document_id")
                            if latest:
                                st.session_state.latest_doc_id = latest
                            st.session_state['collections'] = chromadb_service.get_collections()
                        else:
                            st.error("File ingestion failed.")
                    except Exception as e:
                        st.error(f"Upload failed: {e}")
            if url:
                payload = {"url": url, "collection_name": target_collection}
                try:
                    with st.spinner("Ingesting web page…"):
                        data = chromadb_service.ingest_url(url=url, collection_name=target_collection)
                    st.success(f"Ingested URL into collection {target_collection}")
                    st.session_state['collections'] = chromadb_service.get_collections()
                except Exception as e:
                    st.error(f"URL ingestion failed: {e}")
                        
