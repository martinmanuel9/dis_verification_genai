# Image Position Metadata Schema

This document defines the metadata structure for preserving image positions during document ingestion and reconstruction.

## Position Metadata Per Image

Each image should have the following metadata fields:

### Core Identification
- `filename`: Original image filename
- `storage_path`: Path to stored image file
- `image_id`: Unique identifier for the image

### Page-Level Position
- `page_number`: Which page the image appears on (1-indexed)
- `page_sequence`: Order of image on the page (0-indexed, first image = 0)

### Coordinate Position (for PDFs)
- `bbox_x0`: Left edge of image bounding box (PDF coordinates)
- `bbox_y0`: Bottom edge of image bounding box (PDF coordinates)
- `bbox_x1`: Right edge of image bounding box (PDF coordinates)
- `bbox_y1`: Top edge of image bounding box (PDF coordinates)
- `width_pts`: Image width in points
- `height_pts`: Image height in points

### Text Flow Position
- `char_offset_start`: Character offset where image appears in extracted text
- `char_offset_end`: Character offset where image ends
- `paragraph_index`: Index of paragraph containing/preceding the image
- `text_anchor_before`: First 50 chars of text before the image (for context)
- `text_anchor_after`: First 50 chars of text after the image (for context)

### Content Metadata
- `description`: Vision model description of image content
- `vision_models_used`: List of models that described the image
- `ocr_text`: Any text extracted from the image via OCR (optional)
- `image_type`: Type of image (photo, diagram, chart, table, etc.)

### Reconstruction Hints
- `placement_strategy`: How to place during reconstruction
  - `inline`: Place inline with text at exact position
  - `before_paragraph`: Place before the paragraph
  - `after_paragraph`: Place after the paragraph
  - `page_top`: Place at top of page
  - `page_bottom`: Place at bottom of page
  - `float_right`: Float to right of text
  - `float_left`: Float to left of text

## Storage in ChromaDB

Since ChromaDB metadata only supports primitive types (str, int, float, bool), we store complex structures as JSON:

```python
metadata = {
    # Per-chunk metadata
    "document_id": "abc123",
    "document_name": "report.pdf",
    "chunk_index": 0,
    "page_number": 1,

    # Images stored as JSON arrays
    "image_positions": json.dumps([
        {
            "filename": "img1.png",
            "storage_path": "/path/to/img1.png",
            "page_number": 1,
            "page_sequence": 0,
            "bbox_x0": 72.0,
            "bbox_y0": 500.0,
            "bbox_x1": 272.0,
            "bbox_y1": 700.0,
            "char_offset_start": 150,
            "char_offset_end": 150,
            "paragraph_index": 2,
            "text_anchor_before": "The following diagram shows...",
            "text_anchor_after": "As illustrated above, the system...",
            "description": "Diagram showing network architecture",
            "placement_strategy": "inline"
        }
    ])
}
```

## Reconstruction Algorithm

When reconstructing a document:

1. **Sort chunks** by page_number, then chunk_index
2. **For each chunk**:
   - Parse `image_positions` from JSON
   - Sort images by `char_offset_start` (or `page_sequence` if no char offset)
   - Build content with images inserted at correct positions
3. **Position images** using:
   - Primary: `char_offset_start` - insert at exact character position
   - Fallback 1: `text_anchor_before/after` - find matching text and insert nearby
   - Fallback 2: `page_sequence` - insert in order at page breaks
   - Fallback 3: `placement_strategy` - use hint for positioning

## Example Reconstruction

```markdown
# Document: Report

## Section 1

This is the introduction paragraph with some text.

![Image 1: Network diagram](http://api/images/img1.png)
*Diagram showing network architecture*

The diagram above illustrates the key components...

More text continues here.

![Image 2: Data flow](http://api/images/img2.png)
*Chart showing data flow patterns*

## Section 2

Additional content...
```

## Migration Path

For existing documents without position data:
1. Assign sequential ordering based on chunk_index
2. Use page_number from existing metadata
3. Set placement_strategy = "after_paragraph"
4. Mark as "legacy_positioning" in metadata
