# Document Upload & Management

Learn how to upload, organize, and manage documents in DIS Verification GenAI.

## Quick Start

1. Navigate to **📁 Files** page in the sidebar
2. Click **Upload Files** or drag-and-drop documents
3. Wait for processing to complete
4. Documents are ready for RAG chat and test plan generation

[Screenshot: File management interface]

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Most common, best support |
| Word | `.docx` | Converted to markdown automatically |
| Text | `.txt` | Plain text files |
| Markdown | `.md` | Preserved formatting |

**Maximum File Size**: 100 MB per file

## Uploading Documents

### Method 1: Drag and Drop

1. Go to **Files** page
2. Drag files from your computer
3. Drop into the upload area
4. Files upload automatically

[Screenshot: Drag-and-drop upload]

### Method 2: File Browser

1. Click **Browse Files** button
2. Select one or multiple files
3. Click **Open**
4. Upload begins automatically

### Upload Process

```
Uploading: Technical_Spec.pdf
██████████████████░░░░ 75% (3.1 MB / 4.2 MB)

Processing Steps:
✓ File validation
✓ Text extraction
▶ Image extraction (12/45 images)
⏳ Markdown conversion
⏳ Chunking strategy: page-based
⏳ Embedding generation
⏳ Vector database storage
⏳ PostgreSQL metadata storage
```

**Processing Time**:
- Small docs (< 20 pages): 1-2 minutes
- Medium docs (50-100 pages): 3-5 minutes
- Large docs (200+ pages): 10-20 minutes

## Document Processing Features

### Text Extraction

- Uses PyMuPDF for PDFs
- Preserves document structure
- Maintains formatting where possible
- Handles multi-column layouts

### Image Extraction

**Automatic Image Handling**:
1. Images extracted from PDFs with position tracking
2. Sent to vision AI for description (GPT-4o, Ollama, or BLIP)
3. Descriptions inserted at correct document positions
4. Images stored for reference

[Screenshot: Image extraction in progress]

**Vision Models Used**:
- **OpenAI GPT-4o**: Best quality, requires API key
- **Ollama LLaVa**: Good quality, local
- **HuggingFace BLIP**: Fast, local

### Chunking Strategies

Choose how documents are divided for RAG:

**Page-Based** (default):
```
Chunk = One page of text
Best for: Technical docs, specifications
Preserves: Page structure
```

**Section-Based**:
```
Chunk = One section/chapter
Best for: Long reports, manuals
Preserves: Logical structure
```

**Fixed-Size**:
```
Chunk = N tokens (e.g., 512 tokens)
Best for: Consistent chunk sizes
Preserves: Nothing specific
```

**Configure in**: Files page → Settings → Chunking Strategy

### Embedding Generation

Documents converted to vector embeddings for semantic search:

- **Model**: Snowflake Arctic Embed 2 (US-based)
- **Dimensions**: 768
- **Storage**: ChromaDB vector database

## Managing Documents

### View Document Details

Click any document to see:

[Screenshot: Document details panel]

```
┌────────────────────────────────────────┐
│ Technical_Spec_v2.pdf                  │
├────────────────────────────────────────┤
│ Uploaded: 2025-11-18 14:30:22         │
│ Size: 4.2 MB                          │
│ Pages: 87                             │
│ Status: ✓ Processed                   │
│                                        │
│ Processing Details:                    │
│ • Text chunks: 234                    │
│ • Images extracted: 45                │
│ • Embedding model: arctic-embed       │
│ • Chunking: page-based                │
│ • Collection: Technical Specs         │
│                                        │
│ [View Content] [Download] [Delete]     │
└────────────────────────────────────────┘
```

### Search Documents

Use the search bar to find documents:

```
🔍 Search: [network security          ]

Results:
• Network_Security_Plan.pdf (87% match)
• Technical_Spec_v2.pdf (62% match)
• Architecture_Doc.pdf (51% match)
```

### Filter Documents

Filter by:
- **Date**: Upload date range
- **Size**: File size
- **Status**: Processed, Processing, Error
- **Collection**: Document collection
- **Type**: PDF, DOCX, TXT

### Sort Documents

Click column headers to sort:
- **Name** (A-Z)
- **Date** (newest/oldest)
- **Size** (largest/smallest)
- **Pages** (most/least)

## Collections

Group related documents together.

### Create Collection

1. Click **New Collection**
2. Enter name: e.g., "Technical Specifications"
3. Add description (optional)
4. Click **Create**

[Screenshot: Create collection dialog]

### Add Documents to Collection

**During Upload**:
```
Collection: [Select or create collection ▼]
☑ Create new collection: "Project Apollo Docs"
```

**After Upload**:
1. Select document(s)
2. Click **Add to Collection**
3. Choose collection
4. Click **Add**

### Collection Management

[Screenshot: Collections list]

```
Collections
├─ Technical Specifications (5 docs, 234 chunks)
├─ Test Plans (12 docs, 567 chunks)
├─ Architecture Documents (3 docs, 189 chunks)
└─ Meeting Notes (23 docs, 456 chunks)

[New Collection] [Merge] [Delete]
```

**Collection Actions**:
- **View**: See all documents in collection
- **Export**: Download all documents
- **Share**: Generate shareable collection (future feature)
- **Delete**: Remove collection (keeps documents)

## Vector Database Management

### View Vector Store

Go to **Database Manager** → **Vector Database** tab

[Screenshot: Vector database view]

```
ChromaDB Status: 🟢 Healthy

Collections: 4
Total Chunks: 1,446
Storage Used: 234 MB
Memory Usage: 512 MB

Recent Activity:
• 2025-11-18 14:45 - Added 87 chunks
• 2025-11-18 14:30 - Created collection "Project Apollo"
• 2025-11-18 13:15 - Deleted collection "Old Tests"
```

### Reprocess Documents

If processing failed or settings changed:

1. Select document
2. Click **⚙️ Reprocess**
3. Choose new settings:
   - Chunking strategy
   - Vision model for images
   - Embedding model
4. Click **Start Reprocessing**

### Clean Up Orphaned Vectors

Remove vectors for deleted documents:

1. Go to **Database Manager**
2. Click **🧹 Clean Orphaned Vectors**
3. Review what will be deleted
4. Confirm deletion

## Bulk Operations

### Upload Multiple Files

1. Select multiple files in file browser (Ctrl+Click or Shift+Click)
2. Or drag-and-drop multiple files
3. All upload in parallel
4. Progress shown for each file

### Bulk Delete

1. **Select Mode**: Click **☑ Select** button
2. Check boxes next to documents
3. Click **🗑 Delete Selected**
4. Confirm deletion

[Screenshot: Bulk selection mode]

**Warning**: This also deletes vector embeddings!

### Bulk Download

1. Select multiple documents
2. Click **⬇️ Download Selected**
3. Downloads as ZIP file

### Bulk Move to Collection

1. Select documents
2. Click **📁 Move to Collection**
3. Choose destination collection
4. Click **Move**

## Advanced Features

### Metadata Management

Each document stores metadata:

```json
{
  "filename": "Technical_Spec_v2.pdf",
  "upload_date": "2025-11-18T14:30:22Z",
  "file_size": 4398046,
  "page_count": 87,
  "collection": "Technical Specifications",
  "processed": true,
  "chunking_strategy": "page-based",
  "embedding_model": "snowflake-arctic-embed-l",
  "image_count": 45,
  "chunk_count": 234,
  "custom_tags": ["v2.0", "production", "approved"]
}
```

**Edit Metadata**:
1. Click document
2. Click **✏️ Edit Metadata**
3. Modify fields
4. Click **Save**

### Custom Tags

Add tags for organization:

```
Tags: [v2.0] [production] [approved] [+Add Tag]
```

**Filter by Tags**: Click tag to show all documents with that tag

### Version Control

Track document versions:

```
Technical_Spec_v2.pdf ← Current
├─ Technical_Spec_v1.5.pdf (superseded)
└─ Technical_Spec_v1.0.pdf (archived)

[Compare Versions]
```

**Upload New Version**:
1. Upload file with same base name
2. System detects version
3. Previous version marked as superseded
4. Both versions kept for comparison

### Document Preview

View document contents without downloading:

1. Click document
2. Click **👁️ Preview**
3. Scroll through pages
4. Search within document
5. Jump to specific pages

[Screenshot: Document preview pane]

## Troubleshooting

### Upload Fails

**Problem**: File won't upload

**Solutions**:
- Check file size (< 100 MB)
- Verify file format (PDF, DOCX, TXT)
- Ensure disk space available
- Check network connection
- Try smaller file first

### Processing Stuck

**Problem**: Processing never completes

**Solutions**:
1. Check Celery worker health (sidebar)
2. View processing logs: `docker compose logs celery-worker`
3. Cancel and retry: Click **✕ Cancel** → **🔄 Retry**
4. Restart Celery: `docker compose restart celery-worker`

### Images Not Extracted

**Problem**: PDF images missing

**Solutions**:
- Check if PDF has selectable images (not scanned)
- Verify vision model is configured (GPT-4o or Ollama)
- Review extraction logs
- Try reprocessing with different vision model

### Poor RAG Results

**Problem**: Document search doesn't find relevant content

**Solutions**:
- **Reprocess with different chunking**: Try section-based instead of page-based
- **Check chunk size**: May be too large or too small
- **Verify document content**: Ensure document has extractable text
- **Try different embedding model**: Reprocess with different settings

### Vector Database Full

**Problem**: ChromaDB storage full

**Solutions**:
1. **Delete old collections**: Remove unused documents
2. **Clean orphaned vectors**: Database Manager → Clean Up
3. **Increase disk space**: Allocate more to Docker
4. **Archive old documents**: Export and delete from active DB

## Best Practices

### Document Naming

✅ **Good Names**:
- `Technical_Spec_v2.0_2025-01-15.pdf`
- `Test_Plan_Authentication_Module.pdf`
- `Architecture_Microservices_Design.pdf`

❌ **Bad Names**:
- `doc1.pdf`
- `final_FINAL_v3_ACTUAL_FINAL.pdf`
- `untitled.pdf`

### Collection Organization

**Organize by**:
- Project/product
- Document type
- Time period
- Topic/domain

**Example Structure**:
```
Project_Apollo/
├─ Requirements/
├─ Design/
├─ Test_Plans/
└─ Meeting_Notes/
```

### Document Preparation

Before uploading:

1. **Ensure text is selectable** (not scanned image)
2. **Use clear section headers** (helps chunking)
3. **Include table of contents** (improves structure)
4. **Optimize file size** (compress large PDFs)
5. **Remove unnecessary pages** (covers, blank pages)

### Maintenance

**Regular Tasks**:
- **Weekly**: Review uploaded documents, delete obsolete
- **Monthly**: Clean orphaned vectors
- **Quarterly**: Archive old collections
- **As needed**: Reprocess with improved settings

## Next Steps

- **[Direct Chat](04-direct-chat.md)** - Ask questions about your documents
- **[Document Generator](06-document-generator.md)** - Generate test plans
- **[Database Manager](10-database-manager.md)** - Advanced database operations

---

**Need help?** See [Troubleshooting Guide](12-troubleshooting.md) or [FAQ](13-faq.md)
