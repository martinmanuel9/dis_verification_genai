"""
Migration Example: Integrating Position-Aware Image Placement
This file shows exactly how to modify run_ingest_job in document_ingestion_service.py
"""

# ============================================================================
# BEFORE: Original run_ingest_job (simplified for clarity)
# ============================================================================

def run_ingest_job_OLD(job_id, payloads, collection_name, ...):
    def process_one(item_with_index):
        item, doc_index = item_with_index
        fname = item["filename"]
        content = item["content"]

        # OLD: Extract images without position data
        if ext == ".pdf":
            pages_data = extract_and_store_images_from_file(content, fname, tmp_dir, fname)

        # OLD: Describe images
        pages_data = asyncio.new_event_loop().run_until_complete(
            describe_images_for_pages(pages_data, ...)
        )

        # OLD: Simple page-based chunking
        chunks = []
        for page in pages_data:
            pg_text = extract_text(page)
            img_list = [{"filename": img, ...} for img in page["images"]]
            chunks.append({
                "content": pg_text,
                "images": img_list,  # Just list of images
                "page_number": page["page"]
            })

        # OLD: Store chunks
        for c in chunks:
            meta = {
                "document_name": fname,
                "page_number": c["page_number"],
                "image_filenames": json.dumps([img["filename"] for img in c["images"]]),
                # Missing: position data
            }
            collection.add(documents=[c["content"]], metadatas=[meta], ...)


# ============================================================================
# AFTER: Updated run_ingest_job with Position-Aware Support
# ============================================================================

# NEW IMPORTS
from services.position_aware_extraction import (
    extract_images_with_positions,
    add_text_anchors_to_images
)
from services.position_aware_chunking import (
    page_based_chunking_with_positions,
    merge_images_with_descriptions
)

def run_ingest_job_NEW(
    job_id: str,
    payloads: List[Dict[str, Any]],
    collection_name: str,
    chunk_size: int,
    chunk_overlap: int,
    store_images: bool,
    model_name: str,
    vision_models: List[str],
    openai_api_key: Optional[str],
    enable_ocr: bool,
):
    """Enhanced ingest job with position-aware image placement."""

    redis_client.set(job_id, "running")
    progress_key = f"job:{job_id}:progress"

    redis_client.hset(progress_key, mapping={
        "total_chunks": 0,
        "processed_chunks": 0,
        "total_documents": len(payloads),
        "processed_documents": 0
    })

    def process_one(item_with_index):
        item, doc_index = item_with_index
        fname = item["filename"]
        content = item["content"]
        document_id = uuid.uuid4().hex
        doc_status_key = f"job:{job_id}:doc:{doc_index}"

        redis_client.hset(doc_status_key, mapping={
            "status": "processing",
            "start_time": datetime.now().isoformat()
        })

        try:
            ext = Path(fname).suffix.lower()

            with tempfile.TemporaryDirectory() as tmp_dir:
                # =============================================================
                # STEP 1: Extract images WITH POSITIONS
                # =============================================================
                if ext == ".pdf":
                    # NEW: Extract with position data
                    pages_data = extract_images_with_positions(
                        file_content=content,
                        filename=fname,
                        temp_dir=tmp_dir,
                        doc_id=fname,
                        images_dir=IMAGES_DIR
                    )

                    # NEW: Add text anchors for better position matching
                    pages_data = add_text_anchors_to_images(
                        pages_data,
                        context_chars=100
                    )

                    logger.info(f"Extracted {sum(len(p['images']) for p in pages_data)} images with positions")

                elif ext == ".docx":
                    # Similar implementation for DOCX
                    pages_data = extract_images_from_docx(content, fname, tmp_dir, fname)
                else:
                    pages_data = [{"page": 1, "images": [], "text": None}]

                # =============================================================
                # STEP 2: Describe images (positions are preserved)
                # =============================================================
                pages_data = asyncio.new_event_loop().run_until_complete(
                    describe_images_for_pages(
                        pages_data,
                        api_key_override=openai_api_key,
                        run_all_models=len(vision_models) > 1,
                        enabled_models=set(vision_models),
                        vision_flags={m: (m in vision_models) for m in vision_models},
                    )
                )

                # =============================================================
                # STEP 3: Position-aware chunking
                # =============================================================
                if ext == ".pdf":
                    # NEW: Page-based chunking with positions
                    chunks = page_based_chunking_with_positions(
                        pages_data=pages_data,
                        document_name=fname
                    )
                    logger.info(f"Page-based chunking created {len(chunks)} chunks with position data")
                else:
                    # Fallback to standard processing
                    doc_data = process_document_with_context_multi_model(...)
                    chunks = smart_chunk_with_context(...)

                # Update chunk count
                redis_client.hset(doc_status_key, "chunks_total", len(chunks))
                redis_client.hincrby(progress_key, "total_chunks", len(chunks))

                coll = chroma_client.get_collection(name=collection_name)

                # =============================================================
                # STEP 4: Store chunks with position metadata
                # =============================================================
                for c in chunks:
                    try:
                        text = c["content"]

                        # Build metadata with IMAGE POSITIONS
                        meta = {
                            "document_id": document_id,
                            "document_name": fname,
                            "file_type": ext,
                            "chunk_index": c.get("chunk_index", 0),
                            "total_chunks": len(chunks),
                            "page_number": c.get("page_number", -1),
                            "section_title": c.get("section_title", ""),
                            "section_type": c.get("section_type", "chunk"),
                            "has_images": c.get("has_images", False),
                            "image_count": len(c.get("image_positions", [])),
                            "start_position": c.get("start_position", 0),
                            "end_position": c.get("end_position", len(text)),
                            "timestamp": datetime.now().isoformat(),

                            # NEW: Store complete image position data as JSON
                            "image_positions": json.dumps(c.get("image_positions", [])),

                            # Legacy compatibility fields
                            "image_filenames": json.dumps([
                                img.get("filename", "")
                                for img in c.get("image_positions", [])
                            ]),
                            "image_storage_paths": json.dumps([
                                img.get("storage_path", "")
                                for img in c.get("image_positions", [])
                            ]),
                            "image_descriptions": json.dumps([
                                img.get("description", "")
                                for img in c.get("image_positions", [])
                            ]),
                        }

                        # Validate metadata (no None values for ChromaDB)
                        validated_meta = {}
                        for key, value in meta.items():
                            if value is None:
                                validated_meta[key] = ""
                            elif isinstance(value, (str, int, float, bool)):
                                validated_meta[key] = value
                            else:
                                validated_meta[key] = str(value)

                        # Generate embedding
                        emb = embedding_model.encode([text],
                                                    convert_to_numpy=True,
                                                    batch_size=1).tolist()

                        chunk_id = f"{document_id}_chunk_{c.get('chunk_index', 0)}"
                        validated_meta["chunk_id"] = chunk_id

                        # Store in ChromaDB
                        coll.add(
                            documents=[text],
                            embeddings=emb,
                            metadatas=[validated_meta],
                            ids=[chunk_id],
                        )

                        redis_client.hincrby(progress_key, "processed_chunks", 1)
                        redis_client.hincrby(doc_status_key, "chunks_processed", 1)

                        logger.info(f"[{job_id}] Ingested chunk {c['chunk_index']} with {len(c.get('image_positions', []))} positioned images")

                    except Exception as chunk_error:
                        logger.error(f"[{job_id}] Error processing chunk: {chunk_error}")
                        redis_client.hincrby(doc_status_key, "chunks_failed", 1)
                        continue

            # Document completed
            redis_client.hset(doc_status_key, mapping={
                "status": "completed",
                "end_time": datetime.now().isoformat()
            })
            redis_client.hincrby(progress_key, "processed_documents", 1)
            return fname

        except Exception as e:
            redis_client.hset(doc_status_key, mapping={
                "status": "failed",
                "end_time": datetime.now().isoformat(),
                "error_message": str(e)
            })
            logger.error(f"[{job_id}] Error processing {fname}: {e}")
            raise

    # Launch threads
    max_workers = min(4, os.cpu_count() or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(process_one, (p, i)): p["filename"]
            for i, p in enumerate(payloads)
        }
        for fut in as_completed(futures):
            fname = futures[fut]
            try:
                fut.result()
                logger.info(f"[{job_id}] Finished {fname}")
            except Exception as e:
                logger.error(f"[{job_id}] Error ingesting {fname}: {e!r}")

    redis_client.set(job_id, "success")


# ============================================================================
# COMPARISON: Key Differences
# ============================================================================

"""
BEFORE vs AFTER:

1. IMAGE EXTRACTION:
   BEFORE: extract_and_store_images_from_file() → just filenames and page numbers
   AFTER:  extract_images_with_positions() → full position data (bbox, char_offset, anchors)

2. TEXT CONTEXT:
   BEFORE: None
   AFTER:  add_text_anchors_to_images() → adds text_before/text_after for each image

3. CHUNKING:
   BEFORE: Manual loop creating chunks with images list
   AFTER:  page_based_chunking_with_positions() → structured chunks with image_positions

4. METADATA STORAGE:
   BEFORE:
       "image_filenames": json.dumps([...])
       "image_storage_paths": json.dumps([...])
   AFTER:
       "image_positions": json.dumps([{
           "filename": "...",
           "storage_path": "...",
           "bbox": [x0, y0, x1, y1],
           "char_offset": 123,
           "text_before": "...",
           "text_after": "...",
           "placement_hint": "inline",
           "description": "..."
       }])

5. RECONSTRUCTION:
   BEFORE: Images dumped at end of chunks
   AFTER:  Images inserted at correct positions using char_offset and text anchors

BENEFITS:
- Accurate image placement during reconstruction
- Preserves document layout and flow
- Better for Word export and document review
- Maintains backward compatibility via legacy fields
"""


# ============================================================================
# Example Usage of Reconstructed Document
# ============================================================================

def example_reconstruction():
    """
    Example showing how reconstructed content looks with position-aware images.
    """

    # Get reconstructed document
    response = requests.get(
        "http://localhost:8000/api/vectordb/documents/reconstruct/abc123",
        params={"collection_name": "test_collection"}
    )

    result = response.json()

    # Example result:
    example_result = {
        "document_id": "abc123",
        "document_name": "Report.pdf",
        "total_chunks": 5,
        "reconstructed_content": """
# Report.pdf

---
**Page 1**

This is the introduction to our report.

![Image 1: Company Logo](http://api/vectordb/images/report_page_1_im1.png)
*The company logo showing our brand identity*

The logo above represents our organization's values...

---
**Page 2**

## Technical Architecture

Our system uses a modern microservices architecture.

![Image 2: Architecture Diagram](http://api/vectordb/images/report_page_2_im1.png)
*Diagram showing the microservices architecture with API gateway, services, and databases*

As illustrated in the diagram, we have three main components...

![Image 3: Data Flow](http://api/vectordb/images/report_page_2_im2.png)
*Chart depicting data flow between components*

The data flow follows a specific pattern...
        """,
        "images": [
            {
                "filename": "report_page_1_im1.png",
                "description": "The company logo...",
                "page_number": 1,
                "position": 45
            },
            {
                "filename": "report_page_2_im1.png",
                "description": "Diagram showing...",
                "page_number": 2,
                "position": 89
            },
            {
                "filename": "report_page_2_im2.png",
                "description": "Chart depicting...",
                "page_number": 2,
                "position": 234
            }
        ],
        "metadata": {
            "total_images": 3,
            "pages": [1, 2],
            "vision_models_used": ["openai", "enhanced_local"]
        }
    }

    return example_result


if __name__ == "__main__":
    print("Position-Aware Migration Example")
    print("=" * 50)
    print("\nThis file shows the key changes needed to integrate")
    print("position-aware image placement into your document")
    print("ingestion pipeline.")
    print("\nMain changes:")
    print("1. Use extract_images_with_positions()")
    print("2. Use page_based_chunking_with_positions()")
    print("3. Store image_positions as JSON in metadata")
    print("4. Use position-aware reconstruction")
    print("\nSee POSITION_AWARE_INTEGRATION_GUIDE.md for full details.")
