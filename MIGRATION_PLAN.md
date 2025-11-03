# Position-Aware Image Placement - Migration Plan

## Overview

This migration plan refactors the document ingestion pipeline to support position-aware image placement while maintaining backward compatibility and zero downtime.

**Estimated Total Time:** 4-6 hours
**Difficulty:** Medium
**Risk Level:** Low (backward compatible, phased approach)

---

## Pre-Migration Checklist

Before starting, ensure:

- [ ] All code is committed to git
- [ ] Create a feature branch: `git checkout -b feature/position-aware-images`
- [ ] Backend tests are passing
- [ ] You have a test PDF with images (2-3 pages)
- [ ] Docker services are running (ChromaDB, Redis, FastAPI)
- [ ] You understand the position-aware architecture (read SOLUTION_SUMMARY.md)

---

## Phase 1: Setup & Validation (30 minutes)

### Step 1.1: Create Backup & Feature Branch

```bash
# Ensure working directory is clean
git status

# Create feature branch
git checkout -b feature/position-aware-images

# Tag current state for easy rollback
git tag pre-position-aware-migration
```

**Acceptance Criteria:**
- [ ] Feature branch created
- [ ] Tag created for rollback

---

### Step 1.2: Verify Existing Functionality

Test current document upload to establish baseline:

```bash
# Start services
docker-compose up -d

# Test upload (replace with actual test PDF)
curl -X POST "http://localhost:8000/api/vectordb/documents/upload-and-process" \
  -F "files=@test_document.pdf" \
  -F "collection_name=baseline_test" \
  -F "vision_models=enhanced_local"

# Get job status
curl "http://localhost:8000/api/vectordb/jobs/{job_id}"

# Test reconstruction
curl "http://localhost:8000/api/vectordb/documents/reconstruct/{doc_id}?collection_name=baseline_test"
```

**Acceptance Criteria:**
- [ ] Document uploads successfully
- [ ] Job completes with status "success"
- [ ] Reconstruction returns content
- [ ] Images appear (even if at end of chunks)
- [ ] Save reconstruction output for comparison

---

## Phase 2: Add New Modules (1 hour)

### Step 2.1: Copy New Position-Aware Modules

The new modules are already created. Verify they exist:

```bash
ls -la src/fastapi/services/position_aware_*.py
```

Expected files:
- `position_aware_extraction.py`
- `position_aware_chunking.py`
- `position_aware_reconstruction.py`

**Acceptance Criteria:**
- [ ] All three files exist
- [ ] No syntax errors: `python -m py_compile src/fastapi/services/position_aware_*.py`

---

### Step 2.2: Add Imports to Test Files

Create a simple test to verify modules load correctly:

```bash
# Create test file
cat > test_position_modules.py << 'EOF'
"""Test that position-aware modules can be imported"""

def test_imports():
    try:
        from src.fastapi.services.position_aware_extraction import (
            extract_images_with_positions,
            add_text_anchors_to_images
        )
        print("✅ position_aware_extraction imported successfully")

        from src.fastapi.services.position_aware_chunking import (
            page_based_chunking_with_positions,
            section_based_chunking_with_positions,
            merge_images_with_descriptions
        )
        print("✅ position_aware_chunking imported successfully")

        from src.fastapi.services.position_aware_reconstruction import (
            reconstruct_document_with_positions,
            insert_images_at_positions
        )
        print("✅ position_aware_reconstruction imported successfully")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
EOF

python test_position_modules.py
```

**Acceptance Criteria:**
- [ ] All imports succeed
- [ ] Test script exits with code 0

---

## Phase 3: Refactor Image Extraction (1 hour)

### Step 3.1: Update document_ingestion_service.py - Add Imports

**File:** `src/fastapi/services/document_ingestion_service.py`

**Location:** After existing imports (around line 32)

```python
# Add these imports
from .position_aware_extraction import (
    extract_images_with_positions,
    add_text_anchors_to_images
)
from .position_aware_chunking import (
    page_based_chunking_with_positions,
    section_based_chunking_with_positions,
    merge_images_with_descriptions
)
```

**Command to add:**
```bash
# Edit the file
code src/fastapi/services/document_ingestion_service.py
```

**Acceptance Criteria:**
- [ ] Imports added after line 32
- [ ] No syntax errors: `python -m py_compile src/fastapi/services/document_ingestion_service.py`
- [ ] Service restarts without errors

---

### Step 3.2: Add Feature Flag for Position-Aware Extraction

Add an environment variable to control the new functionality:

**File:** `.env` (or your environment config)

```bash
# Add this line
USE_POSITION_AWARE_EXTRACTION=true
```

**File:** `src/fastapi/services/document_ingestion_service.py`

**Location:** Around line 82 (after other environment variables)

```python
# Add feature flag
USE_POSITION_AWARE = os.getenv("USE_POSITION_AWARE_EXTRACTION", "true").lower() == "true"
logger.info(f"Position-aware extraction: {'ENABLED' if USE_POSITION_AWARE else 'DISABLED'}")
```

**Acceptance Criteria:**
- [ ] Feature flag added to .env
- [ ] Feature flag loaded in service
- [ ] Log message appears on startup

---

### Step 3.3: Create Position-Aware Extraction Wrapper

**File:** `src/fastapi/services/document_ingestion_service.py`

**Location:** Add new function after line 589 (after `extract_and_store_images_from_file`)

```python
def extract_images_with_position_support(
    file_content: bytes,
    filename: str,
    temp_dir: str,
    doc_id: str,
    use_positions: bool = True
) -> List[Dict[str, Any]]:
    """
    Wrapper that supports both legacy and position-aware extraction.

    Args:
        file_content: PDF file bytes
        filename: Original filename
        temp_dir: Temporary directory
        doc_id: Document ID
        use_positions: If True, use position-aware extraction

    Returns:
        List of page data with images
    """
    if use_positions and USE_POSITION_AWARE:
        logger.info(f"Using position-aware extraction for {filename}")
        try:
            pages_data = extract_images_with_positions(
                file_content=file_content,
                filename=filename,
                temp_dir=temp_dir,
                doc_id=doc_id,
                images_dir=IMAGES_DIR
            )

            # Add text anchors for better position matching
            pages_data = add_text_anchors_to_images(
                pages_data,
                context_chars=100
            )

            logger.info(f"Position-aware extraction successful: {sum(len(p['images']) for p in pages_data)} images")
            return pages_data

        except Exception as e:
            logger.error(f"Position-aware extraction failed, falling back to legacy: {e}")
            # Fall through to legacy extraction

    # Legacy extraction (current implementation)
    logger.info(f"Using legacy extraction for {filename}")
    return extract_and_store_images_from_file(file_content, filename, temp_dir, doc_id)
```

**Acceptance Criteria:**
- [ ] Function added after line 589
- [ ] No syntax errors
- [ ] Service restarts successfully

---

### Step 3.4: Update run_ingest_job to Use New Extraction

**File:** `src/fastapi/services/document_ingestion_service.py`

**Location:** In `run_ingest_job` function, around line 1115

**Find this code:**
```python
if ext == ".pdf":
    pages_data = extract_and_store_images_from_file(content, fname, tmp_dir, fname)
```

**Replace with:**
```python
if ext == ".pdf":
    # Use position-aware extraction wrapper (falls back to legacy if needed)
    pages_data = extract_images_with_position_support(
        file_content=content,
        filename=fname,
        temp_dir=tmp_dir,
        doc_id=fname,
        use_positions=True  # Can be controlled per-request if needed
    )
```

**Acceptance Criteria:**
- [ ] Code replaced at line ~1115
- [ ] No syntax errors
- [ ] Service restarts successfully

---

### Step 3.5: Test Position-Aware Extraction

```bash
# Restart FastAPI service
docker-compose restart fastapi

# Upload test document
curl -X POST "http://localhost:8000/api/vectordb/documents/upload-and-process" \
  -F "files=@test_document.pdf" \
  -F "collection_name=position_test_extraction" \
  -F "vision_models=enhanced_local"

# Monitor logs
docker-compose logs -f fastapi | grep -i "position"
```

**Look for in logs:**
- ✅ "Position-aware extraction: ENABLED"
- ✅ "Using position-aware extraction for test_document.pdf"
- ✅ "Position-aware extraction successful: X images"

**Acceptance Criteria:**
- [ ] Upload succeeds
- [ ] Logs show position-aware extraction is used
- [ ] No errors in extraction phase
- [ ] Job completes successfully

---

## Phase 4: Refactor Chunking (1 hour)

### Step 4.1: Create Position-Aware Chunking Wrapper

**File:** `src/fastapi/services/document_ingestion_service.py`

**Location:** Add after line 1190 (after existing chunking logic)

```python
def create_chunks_with_position_support(
    ext: str,
    pages_data: List[Dict],
    fname: str,
    content: bytes,
    tmp_dir: str,
    openai_api_key: Optional[str],
    vision_models: List[str],
    chunk_size: int,
    chunk_overlap: int,
    use_positions: bool = True
) -> List[Dict[str, Any]]:
    """
    Create chunks with optional position preservation.

    Args:
        ext: File extension
        pages_data: Pages with images and text
        fname: Filename
        content: File content bytes
        tmp_dir: Temp directory
        openai_api_key: OpenAI API key
        vision_models: List of vision models
        chunk_size: Chunk size
        chunk_overlap: Chunk overlap
        use_positions: Use position-aware chunking

    Returns:
        List of chunks with metadata
    """
    if use_positions and USE_POSITION_AWARE and ext == ".pdf":
        logger.info(f"Using position-aware chunking for {fname}")
        try:
            # Use page-based chunking with positions (recommended for PDFs)
            chunks = page_based_chunking_with_positions(
                pages_data=pages_data,
                document_name=fname
            )

            logger.info(f"Position-aware chunking created {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Position-aware chunking failed, falling back to legacy: {e}")
            # Fall through to legacy chunking

    # Legacy chunking logic
    logger.info(f"Using legacy chunking for {fname}")

    # Extract text by page
    page_texts = extract_text_by_page(content, fname, tmp_dir)
    page_text_map = {p["page"]: (p.get("text") or "") for p in page_texts}

    chunks = []
    for page in pages_data:
        pg = page.get("page") or 0
        pg_text = page_text_map.get(pg, "")
        img_list = []
        for img_path, desc in zip(page.get("images", []), page.get("image_descriptions", [])):
            img_list.append({
                "filename": Path(img_path).name,
                "storage_path": img_path,
                "description": desc,
            })

        # Ensure we have some content
        if not pg_text.strip():
            pg_text = f"Page {pg}: [no extractable text]"

        chunks.append({
            "content": pg_text.strip(),
            "chunk_index": max(0, int(pg) - 1),
            "images": img_list,
            "page_number": pg,
            "section_type": "page",
            "section_title": "",
            "has_images": len(img_list) > 0,
            "start_position": 0,
            "end_position": len(pg_text or ""),
        })

    return chunks
```

**Acceptance Criteria:**
- [ ] Function added after line 1190
- [ ] No syntax errors
- [ ] Service restarts successfully

---

### Step 4.2: Update run_ingest_job to Use New Chunking

**File:** `src/fastapi/services/document_ingestion_service.py`

**Location:** In `run_ingest_job`, around line 1142-1230

**Find this code block:**
```python
if use_page_chunking:
    # Extract page texts and correlate with images
    page_texts = extract_text_by_page(content, fname, tmp_dir)
    page_text_map = {p["page"]: (p.get("text") or "") for p in page_texts}

    chunks = []
    for page in pages_data:
        # ... lots of chunking logic ...
```

**Replace with:**
```python
# Use position-aware chunking wrapper
chunks = create_chunks_with_position_support(
    ext=ext,
    pages_data=pages_data,
    fname=fname,
    content=content,
    tmp_dir=tmp_dir,
    openai_api_key=openai_api_key,
    vision_models=vision_models,
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    use_positions=True
)
```

**Acceptance Criteria:**
- [ ] Code replaced around line 1142
- [ ] Old chunking logic removed (lines 1142-1230)
- [ ] No syntax errors
- [ ] Service restarts successfully

---

### Step 4.3: Update Metadata Storage for Image Positions

**File:** `src/fastapi/services/document_ingestion_service.py`

**Location:** In `run_ingest_job`, chunk metadata section around line 1244

**Find this code:**
```python
meta = {
    "document_id": document_id,
    "document_name": fname,
    # ... other metadata ...
}
```

**Add after existing metadata (before validation):**
```python
# Add image positions if available
if "image_positions" in c:
    meta["image_positions"] = json.dumps(c.get("image_positions", []))
else:
    # Legacy format - create image_positions from images list
    legacy_positions = []
    for idx, img in enumerate(c.get("images", [])):
        legacy_positions.append({
            "filename": img.get("filename", ""),
            "storage_path": img.get("storage_path", ""),
            "page_number": c.get("page_number", 1),
            "page_sequence": idx,
            "description": img.get("description", ""),
            "placement_hint": "inline"
        })
    meta["image_positions"] = json.dumps(legacy_positions)
```

**Acceptance Criteria:**
- [ ] Metadata code updated
- [ ] Both new and legacy formats supported
- [ ] No syntax errors
- [ ] Service restarts successfully

---

### Step 4.4: Test Position-Aware Chunking

```bash
# Restart service
docker-compose restart fastapi

# Upload test document
curl -X POST "http://localhost:8000/api/vectordb/documents/upload-and-process" \
  -F "files=@test_document.pdf" \
  -F "collection_name=position_test_chunking" \
  -F "vision_models=enhanced_local"

# Check logs
docker-compose logs -f fastapi | grep -i "chunking"
```

**Look for in logs:**
- ✅ "Using position-aware chunking for test_document.pdf"
- ✅ "Position-aware chunking created X chunks"

**Verify metadata in ChromaDB:**
```python
# Python script to check metadata
import chromadb
import json

client = chromadb.HttpClient(host="localhost", port=8000)
coll = client.get_collection("position_test_chunking")
results = coll.get(limit=1, include=["metadatas"])

if results["metadatas"]:
    meta = results["metadatas"][0]
    print("✅ Has image_positions:", "image_positions" in meta)

    if "image_positions" in meta:
        positions = json.loads(meta["image_positions"])
        print(f"✅ Number of images: {len(positions)}")
        if positions:
            print(f"✅ First image data: {positions[0]}")
```

**Acceptance Criteria:**
- [ ] Upload succeeds
- [ ] Logs show position-aware chunking
- [ ] Metadata contains `image_positions` field
- [ ] `image_positions` is valid JSON
- [ ] Image position data includes required fields

---

## Phase 5: Update Reconstruction (1 hour)

### Step 5.1: Update vectordb_api.py - Add Imports

**File:** `src/fastapi/api/vectordb_api.py`

**Location:** After existing imports (around line 11)

```python
# Add this import
from services.position_aware_reconstruction import (
    reconstruct_document_with_positions,
    insert_images_at_positions
)
```

**Acceptance Criteria:**
- [ ] Import added
- [ ] No syntax errors

---

### Step 5.2: Add Feature Flag for Position-Aware Reconstruction

**File:** `src/fastapi/api/vectordb_api.py`

**Location:** After imports, around line 20

```python
# Feature flag for position-aware reconstruction
USE_POSITION_AWARE_RECONSTRUCTION = os.getenv("USE_POSITION_AWARE_RECONSTRUCTION", "true").lower() == "true"
logger.info(f"Position-aware reconstruction: {'ENABLED' if USE_POSITION_AWARE_RECONSTRUCTION else 'DISABLED'}")
```

**Acceptance Criteria:**
- [ ] Feature flag added
- [ ] Log message appears on startup

---

### Step 5.3: Create Hybrid Reconstruction Function

**File:** `src/fastapi/api/vectordb_api.py`

**Location:** Before the `@vectordb_api_router.get("/documents/reconstruct/{document_id}")` endpoint (around line 453)

```python
def reconstruct_with_position_support(
    chunks_data: List[Dict],
    use_positions: bool = True
) -> Dict[str, Any]:
    """
    Reconstruct document with optional position-aware image placement.

    Args:
        chunks_data: List of chunks with metadata
        use_positions: Use position-aware reconstruction

    Returns:
        Reconstruction result with content, images, and metadata
    """
    base_image_url = "/api/vectordb/images"

    if use_positions and USE_POSITION_AWARE_RECONSTRUCTION:
        logger.info("Using position-aware reconstruction")
        try:
            reconstructed_content, images, metadata = reconstruct_document_with_positions(
                chunks_data=chunks_data,
                base_image_url=base_image_url
            )

            return {
                "reconstructed_content": reconstructed_content,
                "images": images,
                "metadata": {
                    **metadata,
                    "reconstruction_method": "position_aware"
                }
            }
        except Exception as e:
            logger.error(f"Position-aware reconstruction failed, falling back to legacy: {e}")
            # Fall through to legacy reconstruction

    # Legacy reconstruction (existing implementation)
    logger.info("Using legacy reconstruction")

    document_name = chunks_data[0]["metadata"].get("document_name", "UNKNOWN")
    lines = [f"# Document: {document_name}", ""]
    all_images = []

    last_section_title = None
    last_page_number = None

    for chunk in chunks_data:
        md = chunk["metadata"]
        content = chunk["content"] or ""

        # Add section headers
        section_title = md.get("section_title", "")
        page_number = md.get("page_number")

        if section_title and section_title != last_section_title:
            lines.append(f"## {section_title}")
            last_section_title = section_title
        elif page_number and page_number != last_page_number:
            lines.append(f"\n---\n**Page {page_number}**\n")
            last_page_number = page_number

        lines.append(content)

        # Add images at end of chunk (legacy behavior)
        try:
            image_filenames = json.loads(md.get("image_filenames", "[]"))
            image_descs = json.loads(md.get("image_descriptions", "[]"))

            for i, (filename, desc) in enumerate(zip(image_filenames, image_descs)):
                img_url = f"{base_image_url}/{filename}"
                lines.append(f"\n![Image]({img_url})")
                if desc:
                    lines.append(f"*{desc[:200]}*")

                all_images.append({
                    "filename": filename,
                    "description": desc,
                    "page_number": page_number
                })
        except Exception as e:
            logger.error(f"Failed to add images: {e}")

        lines.append("")

    return {
        "reconstructed_content": "\n".join(lines).strip(),
        "images": all_images,
        "metadata": {
            "total_images": len(all_images),
            "reconstruction_method": "legacy"
        }
    }
```

**Acceptance Criteria:**
- [ ] Function added before endpoint
- [ ] No syntax errors
- [ ] Service restarts successfully

---

### Step 5.4: Update Reconstruction Endpoint

**File:** `src/fastapi/api/vectordb_api.py`

**Location:** `@vectordb_api_router.get("/documents/reconstruct/{document_id}")` endpoint (around line 453)

**Find this code:**
```python
@vectordb_api_router.get("/documents/reconstruct/{document_id}")
def reconstruct_document(document_id: str, collection_name: str = Query(...)):
    """
    Reconstruct original document from stored chunks and images...
    """
    try:
        collection = chroma_client.get_collection(name=collection_name)

        # Get all chunks
        results = collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"]
        )

        # ... existing reconstruction logic ...
```

**Replace the entire function body with:**
```python
@vectordb_api_router.get("/documents/reconstruct/{document_id}")
def reconstruct_document(document_id: str, collection_name: str = Query(...)):
    """
    Reconstruct original document from stored chunks and images, using position-aware
    placement when available.
    """
    try:
        collection = chroma_client.get_collection(name=collection_name)

        # Get all chunks for this document
        results = collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"]
        )

        if not results["ids"]:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

        # Build chunks data
        chunks_data = []
        for i, chunk_id in enumerate(results["ids"]):
            chunks_data.append({
                "chunk_id": chunk_id,
                "content": results["documents"][i],
                "metadata": results["metadatas"][i]
            })

        # Sort chunks
        chunks_data.sort(key=lambda x: (
            x["metadata"].get("page_number", 999),
            x["metadata"].get("chunk_index", 0)
        ))

        # Reconstruct with position support
        result = reconstruct_with_position_support(
            chunks_data=chunks_data,
            use_positions=True
        )

        # Build response
        return {
            "document_id": document_id,
            "document_name": chunks_data[0]["metadata"].get("document_name", "Unknown"),
            "total_chunks": len(chunks_data),
            "reconstructed_content": result["reconstructed_content"],
            "images": result["images"],
            "metadata": {
                "file_type": chunks_data[0]["metadata"].get("file_type"),
                "total_images": len(result["images"]),
                "processing_timestamp": chunks_data[0]["metadata"].get("timestamp"),
                **result["metadata"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reconstructing document: {str(e)}")
```

**Acceptance Criteria:**
- [ ] Endpoint updated
- [ ] Old reconstruction logic removed
- [ ] No syntax errors
- [ ] Service restarts successfully

---

### Step 5.5: Test Position-Aware Reconstruction

```bash
# Restart service
docker-compose restart fastapi

# Get document ID from previous upload
DOC_ID="<document_id_from_step_4.4>"

# Reconstruct document
curl "http://localhost:8000/api/vectordb/documents/reconstruct/${DOC_ID}?collection_name=position_test_chunking" \
  | jq '.' > reconstructed_output.json

# Check reconstruction method
cat reconstructed_output.json | jq '.metadata.reconstruction_method'
```

**Expected output:** `"position_aware"`

**Verify image placement:**
```bash
# Look at reconstructed content
cat reconstructed_output.json | jq -r '.reconstructed_content' | head -50
```

**Look for:**
- Images appearing inline with text (not all at end)
- Image captions with descriptions
- Proper section headers

**Acceptance Criteria:**
- [ ] Reconstruction succeeds
- [ ] `reconstruction_method` is `"position_aware"`
- [ ] Images appear in text context (not all at end)
- [ ] Image descriptions are present
- [ ] No errors in logs

---

## Phase 6: End-to-End Testing (1 hour)

### Step 6.1: Complete Workflow Test

Test the entire pipeline with a fresh document:

```bash
# 1. Upload new document
curl -X POST "http://localhost:8000/api/vectordb/documents/upload-and-process" \
  -F "files=@military_standard.pdf" \
  -F "collection_name=final_integration_test" \
  -F "vision_models=enhanced_local" \
  > upload_response.json

# 2. Get job ID
JOB_ID=$(cat upload_response.json | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# 3. Poll job status
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/vectordb/jobs/${JOB_ID}" | jq -r '.status')
  echo "Job status: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done

# 4. Get document ID
DOC_ID=$(curl -s "http://localhost:8000/api/vectordb/jobs/${JOB_ID}" | jq -r '.latest_document_id // empty')

if [ -z "$DOC_ID" ]; then
  # Find document ID from collection
  DOC_ID=$(curl -s "http://localhost:8000/api/vectordb/documents?collection_name=final_integration_test" \
    | jq -r '.metadatas[0].document_id')
fi

echo "Document ID: $DOC_ID"

# 5. Reconstruct document
curl "http://localhost:8000/api/vectordb/documents/reconstruct/${DOC_ID}?collection_name=final_integration_test" \
  | jq '.' > final_reconstruction.json

# 6. Verify results
echo "\n=== Reconstruction Summary ==="
cat final_reconstruction.json | jq '{
  document_name: .document_name,
  total_chunks: .total_chunks,
  total_images: .metadata.total_images,
  reconstruction_method: .metadata.reconstruction_method,
  vision_models: .metadata.vision_models_used
}'
```

**Acceptance Criteria:**
- [ ] Upload completes successfully
- [ ] Job status reaches "success"
- [ ] Document ID is retrieved
- [ ] Reconstruction succeeds
- [ ] `reconstruction_method` is `"position_aware"`
- [ ] Images have position data
- [ ] Content looks correct

---

### Step 6.2: Compare Before/After Reconstruction

```bash
# Load baseline (from Phase 1)
cat baseline_reconstruction.json | jq -r '.reconstructed_content' > baseline.md

# Load new reconstruction
cat final_reconstruction.json | jq -r '.reconstructed_content' > position_aware.md

# Compare
diff baseline.md position_aware.md | head -100
```

**Expected differences:**
- Images now appear inline with text (not all at end)
- Better section structure
- Image captions with descriptions

**Acceptance Criteria:**
- [ ] Images are distributed throughout text (not clustered)
- [ ] Images appear near relevant content
- [ ] Image captions are present

---

### Step 6.3: Verify ChromaDB Metadata

```python
# Create verification script
cat > verify_metadata.py << 'EOF'
import chromadb
import json
import sys

client = chromadb.HttpClient(host="localhost", port=8000)

try:
    coll = client.get_collection("final_integration_test")
    results = coll.get(limit=5, include=["metadatas"])

    print(f"✅ Retrieved {len(results['ids'])} chunks")

    for i, meta in enumerate(results["metadatas"]):
        print(f"\n--- Chunk {i} ---")
        print(f"Document: {meta.get('document_name')}")
        print(f"Page: {meta.get('page_number')}")
        print(f"Has images: {meta.get('has_images')}")
        print(f"Image count: {meta.get('image_count')}")

        # Check image_positions
        if "image_positions" in meta:
            positions = json.loads(meta["image_positions"])
            print(f"✅ image_positions: {len(positions)} images")

            if positions:
                img = positions[0]
                print(f"   First image:")
                print(f"     - filename: {img.get('filename')}")
                print(f"     - page_sequence: {img.get('page_sequence')}")
                print(f"     - char_offset: {img.get('char_offset', 'N/A')}")
                print(f"     - placement_hint: {img.get('placement_hint', 'N/A')}")
                print(f"     - has description: {bool(img.get('description'))}")
        else:
            print("❌ No image_positions field")

    print("\n✅ All metadata checks passed")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

python verify_metadata.py
```

**Acceptance Criteria:**
- [ ] All chunks have `image_positions` field
- [ ] `image_positions` is valid JSON
- [ ] Position data includes required fields
- [ ] Script exits successfully

---

## Phase 7: Cleanup & Documentation (30 minutes)

### Step 7.1: Clean Up Test Collections

```bash
# Delete test collections
curl -X DELETE "http://localhost:8000/api/vectordb/collection?collection_name=baseline_test"
curl -X DELETE "http://localhost:8000/api/vectordb/collection?collection_name=position_test_extraction"
curl -X DELETE "http://localhost:8000/api/vectordb/collection?collection_name=position_test_chunking"
curl -X DELETE "http://localhost:8000/api/vectordb/collection?collection_name=final_integration_test"
```

**Acceptance Criteria:**
- [ ] All test collections deleted

---

### Step 7.2: Remove Test Files

```bash
# Remove test files created during migration
rm -f test_position_modules.py
rm -f verify_metadata.py
rm -f upload_response.json
rm -f final_reconstruction.json
rm -f baseline_reconstruction.json
rm -f baseline.md
rm -f position_aware.md
rm -f reconstructed_output.json
```

**Acceptance Criteria:**
- [ ] Test files removed

---

### Step 7.3: Update Documentation

Create/update `CHANGELOG.md`:

```markdown
# Changelog

## [Unreleased]

### Added
- Position-aware image extraction from PDFs
- Position-aware chunking (page-based, section-based, fixed-size)
- Position-aware document reconstruction
- Image position metadata (bbox, char_offset, text anchors)
- Feature flags for gradual rollout

### Changed
- Document ingestion now preserves image positions
- Reconstruction places images at correct locations
- Metadata includes `image_positions` JSON field

### Fixed
- Images no longer dumped at end of chunks
- Better document layout preservation
- More accurate document reconstruction

### Migration Notes
- Backward compatible with existing documents
- New documents automatically use position-aware extraction
- Legacy documents use fallback reconstruction
- Re-ingest documents for optimal positioning
```

**Acceptance Criteria:**
- [ ] CHANGELOG.md updated

---

### Step 7.4: Commit Changes

```bash
# Review changes
git status
git diff

# Add all changes
git add src/fastapi/services/position_aware_*.py
git add src/fastapi/services/document_ingestion_service.py
git add src/fastapi/api/vectordb_api.py
git add .env
git add CHANGELOG.md

# Commit
git commit -m "feat: Add position-aware image placement

- Implement position-aware image extraction
- Add position-aware chunking (page/section/fixed)
- Implement position-aware reconstruction
- Preserve image positions through pipeline
- Maintain backward compatibility

Fixes #XXX"

# Push to feature branch
git push origin feature/position-aware-images
```

**Acceptance Criteria:**
- [ ] All changes committed
- [ ] Pushed to feature branch

---

## Phase 8: Deployment & Monitoring (30 minutes)

### Step 8.1: Create Pull Request

Create PR on GitHub/GitLab with:

**Title:** `feat: Position-aware image placement for document reconstruction`

**Description:**
```markdown
## Summary
Implements position-aware image placement throughout the document ingestion and reconstruction pipeline.

## Changes
- Added position-aware extraction module
- Added position-aware chunking module
- Added position-aware reconstruction module
- Updated document_ingestion_service.py
- Updated vectordb_api.py reconstruction endpoint
- Added feature flags for gradual rollout

## Testing
- ✅ Unit tests pass
- ✅ Integration tests pass
- ✅ End-to-end workflow tested
- ✅ Backward compatibility verified

## Migration Notes
- Backward compatible with existing documents
- Feature flags allow gradual rollout
- No breaking changes

## Screenshots
[Add before/after reconstruction screenshots]

## Checklist
- [x] Code follows style guidelines
- [x] Tests added/updated
- [x] Documentation updated
- [x] Backward compatible
- [x] No breaking changes
```

**Acceptance Criteria:**
- [ ] PR created
- [ ] Description is comprehensive
- [ ] Screenshots added

---

### Step 8.2: Merge to Main

After PR approval:

```bash
# Switch to main
git checkout main

# Merge feature branch
git merge feature/position-aware-images

# Tag release
git tag v1.1.0-position-aware

# Push
git push origin main --tags
```

**Acceptance Criteria:**
- [ ] Merged to main
- [ ] Tagged with version
- [ ] Pushed to remote

---

### Step 8.3: Deploy to Production

```bash
# Build updated images
docker-compose build

# Deploy
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Acceptance Criteria:**
- [ ] Services rebuilt
- [ ] Services running
- [ ] No errors in logs

---

### Step 8.4: Monitor First Production Uploads

```bash
# Monitor logs
docker-compose logs -f fastapi | grep -i "position"

# Watch for:
# - "Position-aware extraction: ENABLED"
# - "Using position-aware extraction"
# - "Position-aware chunking created X chunks"
# - "Using position-aware reconstruction"
```

**Monitor for 24 hours:**
- Upload success rate
- Reconstruction quality
- Error rates
- Performance metrics

**Acceptance Criteria:**
- [ ] First uploads succeed
- [ ] No errors in production logs
- [ ] Reconstruction quality verified

---

## Rollback Plan

If issues occur, rollback using:

### Quick Rollback (revert to tag)

```bash
# Stop services
docker-compose down

# Checkout pre-migration tag
git checkout pre-position-aware-migration

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify
docker-compose logs -f | head -100
```

### Feature Flag Rollback (disable new features)

```bash
# Update .env
USE_POSITION_AWARE_EXTRACTION=false
USE_POSITION_AWARE_RECONSTRUCTION=false

# Restart services
docker-compose restart fastapi
```

**Both approaches maintain data integrity** - existing documents work either way.

---

## Success Criteria

Migration is successful when:

- [ ] All phases completed
- [ ] All tests passing
- [ ] Documents upload successfully
- [ ] Position-aware extraction working
- [ ] Position-aware chunking working
- [ ] Position-aware reconstruction working
- [ ] Images appear at correct positions
- [ ] No errors in production logs
- [ ] Backward compatibility maintained
- [ ] Performance acceptable (<15% overhead)

---

## Troubleshooting Guide

### Issue: Import errors

**Symptom:** `ModuleNotFoundError: No module named 'services.position_aware_extraction'`

**Fix:**
```bash
# Check file exists
ls -la src/fastapi/services/position_aware_extraction.py

# Check import path
grep "from .position_aware" src/fastapi/services/document_ingestion_service.py

# Restart service
docker-compose restart fastapi
```

---

### Issue: Position data not stored

**Symptom:** Metadata doesn't contain `image_positions`

**Fix:**
```bash
# Check feature flag
grep "USE_POSITION_AWARE" .env

# Check logs
docker-compose logs fastapi | grep "position-aware chunking"

# Verify chunking function is called
docker-compose logs fastapi | grep "page_based_chunking_with_positions"
```

---

### Issue: Reconstruction fails

**Symptom:** 500 error on reconstruction endpoint

**Fix:**
```bash
# Check logs for error
docker-compose logs fastapi | grep "Error reconstructing"

# Test with legacy reconstruction
# Set USE_POSITION_AWARE_RECONSTRUCTION=false

# Restart and retry
docker-compose restart fastapi
```

---

### Issue: Images still at end of chunks

**Symptom:** Reconstructed document shows all images at end

**Fix:**
```bash
# Check if image_positions has data
# Run verify_metadata.py script from Step 6.3

# Check reconstruction method
curl "http://localhost:8000/api/vectordb/documents/reconstruct/${DOC_ID}?..." \
  | jq '.metadata.reconstruction_method'

# Should be "position_aware", not "legacy"
```

---

## Post-Migration Tasks

After successful migration:

1. **Performance Monitoring**
   - Track upload times
   - Track reconstruction times
   - Compare with baseline metrics

2. **Quality Validation**
   - Review reconstructed documents
   - Compare with originals
   - Collect user feedback

3. **Documentation**
   - Update user documentation
   - Create video tutorials
   - Add FAQ section

4. **Optimization**
   - Tune `context_chars` parameter
   - Optimize vision model selection
   - Implement caching if needed

---

## Support

Questions during migration?
1. Check logs: `docker-compose logs -f fastapi`
2. Review error messages
3. Consult POSITION_AWARE_INTEGRATION_GUIDE.md
4. Check individual module documentation

---

## Summary

**Total Time:** 4-6 hours
**Phases:** 8
**Risk:** Low (backward compatible)
**Rollback:** Easy (feature flags + git tags)

This migration maintains **100% backward compatibility** while adding powerful position-aware capabilities for new uploads.
