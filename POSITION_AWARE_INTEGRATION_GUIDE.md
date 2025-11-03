# Position-Aware Image Placement Integration Guide

## Overview

This guide explains how to integrate the new position-aware image extraction, chunking, and reconstruction modules into your existing document ingestion pipeline.

## Architecture

```
┌──────────────────────────────────────┐
│  Document Upload (PDF, DOCX, etc.)  │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│  Position-Aware Image Extraction     │
│  • Captures X,Y coordinates          │
│  • Records page sequence              │
│  • Estimates text flow position      │
│  • Adds text anchors (before/after)  │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│  Vision Model Processing             │
│  • OpenAI, HuggingFace, etc.         │
│  • Adds descriptions to images       │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│  Position-Aware Chunking             │
│  • Page-based (1 chunk per page)     │
│  • Section-based (by headings)       │
│  • Fixed-size (with overlap)         │
│  • Preserves image positions         │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│  Embedding & ChromaDB Storage        │
│  • Stores image_positions as JSON    │
│  • Maintains all position metadata   │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│  Position-Aware Reconstruction       │
│  • Retrieves chunks from ChromaDB    │
│  • Parses image_positions             │
│  • Inserts images at correct spots   │
│  • Generates markdown/Word output    │
└──────────────────────────────────────┘
```

## Integration Steps

### Step 1: Update Image Extraction

In `document_ingestion_service.py`, replace the existing `extract_and_store_images_from_file` function:

```python
# Import the new module
from services.position_aware_extraction import (
    extract_images_with_positions,
    add_text_anchors_to_images
)

# In your processing function:
def process_pdf_document(file_content, filename, temp_dir, doc_id):
    # Extract images with position data
    pages_data = extract_images_with_positions(
        file_content=file_content,
        filename=filename,
        temp_dir=temp_dir,
        doc_id=doc_id,
        images_dir=IMAGES_DIR
    )

    # Add text anchors for better positioning
    pages_data = add_text_anchors_to_images(pages_data, context_chars=100)

    return pages_data
```

### Step 2: Update Vision Processing

The vision processing workflow remains the same, but now operates on images with position data:

```python
from services.document_ingestion_service import describe_images_for_pages

# Describe images (positions are preserved)
pages_data = await describe_images_for_pages(
    pages_data,
    api_key_override=openai_api_key,
    run_all_models=True,
    enabled_models={"openai", "huggingface", "enhanced_local"},
    vision_flags={"openai": True, "huggingface": True, "enhanced_local": True}
)
```

### Step 3: Update Chunking Strategy

Replace chunking logic with position-aware versions:

```python
from services.position_aware_chunking import (
    page_based_chunking_with_positions,
    section_based_chunking_with_positions,
    fixed_size_chunking_with_positions,
    merge_images_with_descriptions
)

# Choose chunking strategy based on document type
if ext == ".pdf":
    # Page-based chunking (recommended for PDFs)
    chunks = page_based_chunking_with_positions(
        pages_data=pages_data,
        document_name=filename
    )
elif use_section_based:
    # Section-based chunking (for structured documents)
    chunks = section_based_chunking_with_positions(
        content=full_text,
        images_data=all_images,
        document_name=filename
    )
else:
    # Fixed-size chunking (fallback)
    chunks = fixed_size_chunking_with_positions(
        content=full_text,
        images_data=all_images,
        chunk_size=1000,
        overlap=200
    )
```

### Step 4: Update Metadata Storage

When storing chunks in ChromaDB, ensure image_positions is serialized to JSON:

```python
import json

for chunk in chunks:
    metadata = {
        "document_id": document_id,
        "document_name": filename,
        "chunk_index": chunk["chunk_index"],
        "page_number": chunk.get("page_number", -1),
        "section_title": chunk.get("section_title", ""),
        "section_type": chunk.get("section_type", "chunk"),
        "has_images": chunk.get("has_images", False),
        "image_count": chunk.get("image_count", 0),

        # NEW: Store image positions as JSON
        "image_positions": json.dumps(chunk.get("image_positions", [])),

        # Legacy fields for backward compatibility
        "image_filenames": json.dumps([img["filename"] for img in chunk.get("images", [])]),
        "image_storage_paths": json.dumps([img["storage_path"] for img in chunk.get("images", [])]),
        "image_descriptions": json.dumps([img.get("description", "") for img in chunk.get("images", [])]),
    }

    # Store in ChromaDB
    collection.add(
        documents=[chunk["content"]],
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[chunk_id]
    )
```

### Step 5: Update Reconstruction Endpoint

In `vectordb_api.py`, replace the reconstruction logic:

```python
from services.position_aware_reconstruction import reconstruct_document_with_positions

@vectordb_api_router.get("/documents/reconstruct/{document_id}")
def reconstruct_document(document_id: str, collection_name: str = Query(...)):
    """Reconstruct document with images at correct positions."""
    try:
        collection = chroma_client.get_collection(name=collection_name)

        # Get all chunks
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

        # Reconstruct with positions
        reconstructed_content, images, metadata = reconstruct_document_with_positions(
            chunks_data=chunks_data,
            base_image_url="/api/vectordb/images"
        )

        return {
            "document_id": document_id,
            "document_name": chunks_data[0]["metadata"].get("document_name", "Unknown"),
            "total_chunks": len(chunks_data),
            "reconstructed_content": reconstructed_content,
            "images": images,
            "metadata": metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reconstructing: {str(e)}")
```

## Testing the Integration

### 1. Upload a Test Document

```bash
curl -X POST "http://localhost:8000/api/vectordb/documents/upload-and-process" \
  -F "files=@test_document.pdf" \
  -F "collection_name=test_collection" \
  -F "chunk_size=1000" \
  -F "vision_models=openai,enhanced_local"
```

### 2. Check Job Status

```bash
curl "http://localhost:8000/api/vectordb/jobs/{job_id}"
```

### 3. Reconstruct Document

```bash
curl "http://localhost:8000/api/vectordb/documents/reconstruct/{document_id}?collection_name=test_collection"
```

### 4. Verify Image Positions

The reconstructed markdown should have images at the correct positions:

```markdown
# Test Document

## Introduction

This is the introduction text.

![Image 1: Diagram](http://api/vectordb/images/img1.png)
*Diagram showing the architecture*

The diagram above illustrates...
```

## Migration for Existing Documents

If you have existing documents without position data, you can:

### Option 1: Re-ingest Documents

Delete and re-upload documents to get full position tracking.

### Option 2: Add Fallback Logic

The reconstruction logic already handles legacy documents by:
1. Detecting missing `image_positions`
2. Falling back to legacy `image_filenames` format
3. Placing images at the end of chunks (old behavior)

## Advanced Configuration

### Custom Placement Strategies

You can customize how images are placed based on their `placement_hint`:

```python
PLACEMENT_STRATEGIES = {
    "inline": lambda img, content: insert_inline(img, content),
    "float_right": lambda img, content: float_right(img, content),
    "float_left": lambda img, content: float_left(img, content),
    "page_top": lambda img, content: prepend_to_content(img, content),
    "page_bottom": lambda img, content: append_to_content(img, content),
}
```

### Coordinate-Based Positioning for PDFs

For even more precise positioning, you can parse PDF content streams to get exact (x, y) coordinates. This requires additional PDF parsing libraries like `pdfplumber` or `PyMuPDF`.

## Troubleshooting

### Images not appearing in correct positions

**Check:**
1. `image_positions` is being stored as JSON string
2. Chunks are sorted by page_number and chunk_index
3. `char_offset` values are reasonable (0 to length of content)

### Duplicate images

**Check:**
1. Image deduplication in extraction
2. Proper char_offset ranges (no overlapping chunks capturing same images)

### Missing images

**Check:**
1. Image files exist in `stored_images` directory
2. `image_storage_paths` are correct
3. Image extraction didn't fail (check logs)

## Performance Considerations

1. **Image position calculation**: Adds ~10-20% overhead to extraction
2. **Metadata storage**: image_positions JSON can be large (500B-2KB per image)
3. **Reconstruction**: Position-based insertion is O(n*m) where n=chunks, m=images per chunk

For large documents (>100 pages), consider:
- Batch processing pages
- Caching position calculations
- Lazy image loading in UI

## Next Steps

After integration:
1. Test with various PDF types (scanned, native, mixed)
2. Validate image positioning accuracy
3. Tune `context_chars` for text anchors
4. Add user feedback mechanism for position corrections
5. Consider ML model for image position prediction

## Support

For issues or questions:
- Check logs for detailed error messages
- Review `image_position_schema.md` for metadata structure
- Test with simple single-page PDFs first
- Validate ChromaDB metadata constraints (no None values)
