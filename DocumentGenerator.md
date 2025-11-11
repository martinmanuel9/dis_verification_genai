# Document Generator

The document generation capability creates test plans based on a standard or document selected from the vector database. This system uses a sophisticated multi-agent pipeline to extract requirements, synthesize test procedures, and generate comprehensive test plans.

## Overview

### Purpose
Generate comprehensive test plans from standards documents (like `disr_ipv6_50.pdf` or `rfc9293.pdf`) using AI-powered multi-agent orchestration.

### Output Format
Generated test plans follow the structure and format of reference documents like `ipv6v4_may09.pdf`, including:
- Test objectives and scope
- Requirements matrix
- Detailed test procedures
- Expected results and acceptance criteria
- Test cards for execution tracking

---

## Architecture

### Multi-Agent Pipeline

The system uses a configurable multi-agent architecture:

```
1. Document Ingestion
   ↓
2. Section Extraction (Auto/Metadata-based/Chunk-based)
   ↓
3. Actor Agents (Parallel) - Extract requirements from sections
   ↓
4. Critic Agent - Synthesize and deduplicate actor outputs
   ↓
5. QA Agents (Optional) - Contradiction detection + Gap analysis
   ↓
6. Final Consolidation - Merge all sections
   ↓
7. Export to Word with Test Cards
```

### Key Components

1. **DocumentService** (`src/fastapi/services/generate_docs_service.py`)
   - Orchestrates the generation process
   - Handles section extraction and document reconstruction

2. **MultiAgentTestPlanService** (`src/fastapi/services/multi_agent_test_plan_service.py`)
   - Manages agent execution pipeline
   - Coordinates actor → critic → QA workflow
   - Stores intermediate results in Redis

3. **Agent Set System** (`src/fastapi/models/agent_set.py`)
   - Database-backed agent configurations
   - Reusable pipelines (Standard, Quick Draft, Comprehensive QA)
   - User-customizable workflows

4. **Test Card Service** (`src/fastapi/services/test_card_service.py`)
   - Generates executable test cards from requirements
   - Embeds test cards into generated documents

---

## Prerequisites

### 1. Database Initialization

Ensure the database has been initialized with default agents and agent sets:

```bash
docker exec -it fastapi python3 -m db.init_db
```

This creates:
- **4 Test Plan Agents**:
  - Actor Agent (ID: 1) - Extracts testable requirements
  - Critic Agent (ID: 2) - Synthesizes and deduplicates
  - Contradiction Detection Agent (ID: 3) - Identifies conflicts
  - Gap Analysis Agent (ID: 4) - Finds missing coverage

- **4 Default Agent Sets**:
  - **Standard Test Plan Pipeline** (ID: 1) - Recommended
  - Quick Draft Pipeline (ID: 2) - Faster, less thorough
  - Comprehensive QA Pipeline (ID: 3) - Most thorough
  - Mixed Agent Set Example (ID: 4) - Template for custom sets

### 2. Document Upload

Upload your source document to ChromaDB:
1. Navigate to the **Document Management** page in Streamlit
2. Upload `disr_ipv6_50.pdf` or other standards document
3. Select or create a collection name
4. Wait for vectorization to complete

### 3. Agent Set Selection

Choose an agent set from the **Agent Set Manager** or use the default "Standard Test Plan Pipeline".

---

## Usage Guide

### Using the Streamlit UI

1. **Navigate to Document Generator**
   - Open Streamlit interface
   - Go to "Document Generator" page

2. **Select Agent Pipeline**
   - Choose from available agent sets
   - Default: "Standard Test Plan Pipeline"
   - View pipeline configuration in the expander

3. **Select Source Documents**
   - Choose collection containing your uploaded documents
   - Click "Load Source Documents"
   - Select one or more source documents

4. **Configure Output**
   - Enter output file name (e.g., "Test_Plan_IPv6")
   - Enable/disable test cards
   - Choose export method:
     - **Standard (python-docx)**: Basic Word formatting
     - **Professional (Pandoc)**: Enhanced formatting with TOC and section numbering

5. **Start Generation (Background - No Timeout!)**
   - Click "Generate Documents (Background)"
   - Generation starts immediately and runs in the background
   - **No timeout!** Process can take as long as needed (20+ minutes for large documents)

6. **Track Progress**
   - UI automatically polls for status every 5 seconds
   - Shows current status: `queued` → `processing` → `completed`
   - Progress bar indicates activity
   - **Can navigate away** - generation continues in background!
   - **Can close browser** - generation continues on server!

7. **Resume/Check Status (Even After Refresh!)**
   - **If you refresh or close browser**: Your pipeline is NOT lost!
   - Open Document Generator page
   - Click **"📋 Resume Existing Generation"** expander
   - See list of all your recent pipelines with status
   - Click **"Resume"** button next to your pipeline
   - Or enter pipeline ID manually
   - **Pipeline ID in URL** - Can bookmark the page!
   - Results stored for 7 days

8. **Download When Ready**
   - When status changes to `completed`:
     - Stats displayed (sections, requirements, procedures)
     - Download button appears
     - Click "📥 Download" to get Word document
   - Result stored for 7 days - can retrieve later using pipeline_id

### Using the API

#### **RECOMMENDED**: Background Generation (POST /doc_gen/generate_documents_async)

For long-running generations without timeout:

```bash
# Step 1: Start generation (returns immediately)
curl -X POST "http://localhost:9020/api/doc_gen/generate_documents_async" \
  -H "Content-Type: application/json" \
  -d '{
    "source_collections": ["standards_collection"],
    "source_doc_ids": ["disr_ipv6_50"],
    "doc_title": "IPv6 Test Plan",
    "agent_set_id": 1,
    "sectioning_strategy": "auto",
    "chunks_per_section": 5
  }'

# Response:
# {
#   "pipeline_id": "pipeline_abc123def456",
#   "status": "queued",
#   "message": "Document generation started in background...",
#   "doc_title": "IPv6 Test Plan",
#   "agent_set_name": "Standard Test Plan Pipeline"
# }

# Step 2: Check status (poll every 5-10 seconds)
curl -X GET "http://localhost:9020/api/doc_gen/generation-status/pipeline_abc123def456"

# Response (processing):
# {
#   "pipeline_id": "pipeline_abc123def456",
#   "status": "processing",
#   "doc_title": "IPv6 Test Plan",
#   "progress_message": "Generation in progress...",
#   "sections_processed": "5",
#   "total_sections": "12"
# }

# Step 3: Get result when completed
curl -X GET "http://localhost:9020/api/doc_gen/generation-result/pipeline_abc123def456"

# Response (completed):
# {
#   "documents": [{
#     "title": "IPv6 Test Plan",
#     "content": "Markdown content...",
#     "docx_b64": "base64_encoded_word_document",
#     "total_sections": 42,
#     "total_requirements": 156,
#     "total_test_procedures": 89,
#     "pipeline_id": "pipeline_abc123def456"
#   }]
# }
```

#### Legacy: Synchronous Generation (POST /doc_gen/generate_documents)

**Note**: This endpoint has a 20-minute timeout. Use async endpoint above for large documents.

```bash
curl -X POST "http://localhost:9020/api/doc_gen/generate_documents" \
  -H "Content-Type: application/json" \
  -d '{
    "source_collections": ["standards_collection"],
    "source_doc_ids": ["disr_ipv6_50"],
    "doc_title": "IPv6 Test Plan",
    "agent_set_id": 1,
    "sectioning_strategy": "auto",
    "chunks_per_section": 5
  }'
```

#### Parameters

- `source_collections`: List of ChromaDB collection names
- `source_doc_ids`: List of specific document IDs to process
- `doc_title`: Title for the generated test plan
- `agent_set_id`: **Required** - ID of the agent set to use (default: 1)
- `sectioning_strategy`: "auto" (default), "by_metadata", "by_chunks"
- `chunks_per_section`: Number of chunks per section (default: 5)

---

## Evaluation Process

### Goal
Compare generated test plans to reference documents to evaluate quality and format similarity.

### Steps

1. **Generate Test Plan from Sample Document**
   ```
   Input: disr_ipv6_50.pdf
   Output: Generated_Test_Plan.docx
   ```

2. **Compare to Reference**
   ```
   Reference: ipv6v4_may09.pdf
   ```

3. **Evaluation Criteria**
   - **Structure Similarity**: Section organization matches reference
   - **Requirements Coverage**: All requirements extracted
   - **Test Procedure Quality**: Detailed, executable procedures
   - **Format Consistency**: Similar formatting and presentation
   - **Test Card Completeness**: Executable test cards included

4. **Metrics**
   - Section count match: ✓/✗
   - Requirement extraction rate: X%
   - Test procedure count: X procedures
   - Format similarity score: X/10

---

## Configuration Options

### Agent Set Configuration

Agent sets define the pipeline stages and agent IDs for each stage:

```json
{
  "stages": [
    {
      "stage_name": "actor",
      "agent_ids": [1, 1, 1],
      "execution_mode": "parallel",
      "description": "Three actor agents analyze sections"
    },
    {
      "stage_name": "critic",
      "agent_ids": [2],
      "execution_mode": "sequential",
      "description": "Critic synthesizes outputs"
    },
    {
      "stage_name": "qa",
      "agent_ids": [3, 4],
      "execution_mode": "parallel",
      "description": "QA agents check quality"
    }
  ]
}
```

### Sectioning Strategies

- **auto** (recommended): Tries metadata grouping, falls back to chunk-based
- **by_metadata**: Groups by section_title metadata from ChromaDB
- **by_chunks**: Creates sequential groups of N chunks
- **by_pages**: Groups by page numbers

---

## Troubleshooting

### Context Length Exceeded Error

**Error Message**: `"This model's maximum context length is 8192 tokens. However, you requested 8792 tokens..."`

**Cause**: Agents are configured with max_tokens values that are too high when combined with large inputs (especially the Critic agent receiving outputs from multiple Actor agents)

**Solution**:
1. **Apply the database migration fix** (Recommended):
   ```bash
   docker exec -it fastapi python3 -m db.init_db
   ```
   This will apply migration `002_fix_agent_max_tokens.sql` which reduces:
   - Actor agents: 4000 → 2500 tokens
   - Critic agent: 4000 → 2000 tokens
   - QA agents: 4000 → 2000 tokens

2. **The system now includes automatic token adjustment** that will dynamically reduce max_tokens based on input size to prevent this error

3. **Alternative: Use a larger context model**
   - Update agent configurations to use `gpt-4-turbo` (128K context)
   - Or use `gpt-4-32k` (32K context)
   - Go to Agent Manager → Edit agent → Change model_name

**Prevention**: The updated system automatically calculates safe token limits, but keeping agent max_tokens ≤ 2500 is recommended for `gpt-4` model.

### Connection Errors During Status Checks

**Error Message**: `Connection aborted`, `Remote end closed connection without response`

**Cause**: FastAPI server is very busy processing the generation and cannot respond to status check requests quickly

**What's Happening**: Your generation is still running in the background! The server is just too busy to respond to status API calls.

**Solution**:

1. **Use Manual Refresh** (Recommended):
   - In the UI, **disable auto-refresh checkbox**
   - Click "🔄 Refresh Status" button manually every few minutes
   - Server will respond when it has capacity

2. **Check Status Directly from Redis** (Bypasses API):
   ```bash
   # From your repository root
   ./scripts/check_pipeline_status.sh pipeline_YOUR_ID_HERE
   ```
   This shows you the status without hitting the busy API server.

3. **Wait and Come Back Later**:
   - Your `pipeline_id` is saved in your session
   - Generation continues in background
   - Come back in 30-60 minutes
   - Click refresh to check if completed

4. **Check Docker Logs**:
   ```bash
   docker logs -f fastapi | grep "pipeline_YOUR_ID"
   ```
   See real-time progress in server logs

**Important**:
- ✅ Generation is **NOT** stopped - it continues running!
- ✅ Your `pipeline_id` is safe - results stored for 7 days
- ✅ You can close browser - just return later with your `pipeline_id`

### "I Refreshed and Lost My Pipeline ID!"

**Don't worry!** Your pipeline is NOT lost. Here are multiple ways to find it:

**Option 1: Use the Resume Pipeline Feature (Easiest)**
1. Open Document Generator page in Streamlit
2. Click **"📋 Resume Existing Generation"** expander
3. See list of all your recent pipelines
4. Click **"Resume"** button next to your pipeline
5. Done! Status will show automatically

**Option 2: List All Pipelines via Script**
```bash
# Shows all active pipelines with status
./scripts/check_pipeline_status.sh

# Output shows:
# 1. ⏳ Pipeline ID: pipeline_1408be164480
#    Title: Generated_Test_Plan
#    Status: processing
#    Created: 2025-11-11T04:32:46
```

**Option 3: Use API Endpoint**
```bash
curl http://localhost:9020/api/doc_gen/list-pipelines
```

**Option 4: Check URL Parameter**
- If you bookmarked the page, pipeline_id is in URL
- Example: `http://localhost:8501/?pipeline_id=pipeline_1408be164480`
- Just open the bookmark!

**How to Prevent Losing Pipeline IDs**:
1. **Bookmark the page** after starting generation (pipeline_id in URL)
2. **Copy pipeline_id** to notepad when shown
3. **Use the Resume feature** - shows all your pipelines

### "agent_set_id is required" Error

**Cause**: No agent set specified in the request

**Solution**:
1. Select an agent set from the dropdown in Streamlit UI
2. Or use agent_set_id=1 (Standard Test Plan Pipeline) in API calls

### "No agent sets available" Error

**Cause**: Database not initialized or no active agent sets

**Solution**:
1. Run database initialization:
   ```bash
   docker exec -it fastapi python3 -m db.init_db
   ```
2. Or create a new agent set in the Agent Set Manager

### "Agent set X not found" Error

**Cause**: Invalid agent_set_id or agent set was deleted

**Solution**:
1. Check available agent sets in Agent Set Manager
2. Use default agent set (ID: 1)
3. Verify database has been initialized

### Request Timeout Error (20-minute limit)

**Error Message**: `HTTPConnectionPool(host='fastapi', port=9020): Read timed out. (read timeout=1200)`

**Cause**: Synchronous endpoint has 20-minute timeout - large documents exceed this

**Solution**:
1. **USE BACKGROUND GENERATION** (Recommended - No Timeout!):
   - UI: Click "Generate Documents (Background)" instead of regular button
   - API: Use `/generate_documents_async` endpoint
   - Generation continues indefinitely until complete
   - Can close browser - process continues on server

2. **Alternative: Use faster pipeline**:
   - Use "Quick Draft Pipeline" (agent_set_id=2) for faster results
   - Reduces quality but completes in ~5-10 minutes

3. **Optimize document processing**:
   - Split large documents into smaller sections
   - Adjust `chunks_per_section` to create fewer, larger sections

**How Background Generation Works**:
```bash
# Start generation (returns immediately with pipeline_id)
POST /api/doc_gen/generate_documents_async

# Poll for status (every 5-10 seconds)
GET /api/doc_gen/generation-status/{pipeline_id}

# Get result when completed
GET /api/doc_gen/generation-result/{pipeline_id}
```

**Benefits**:
- ✅ No timeout - runs as long as needed
- ✅ Can close browser - process continues
- ✅ Can check progress anytime
- ✅ Results stored for 7 days
- ✅ Resume from where you left off

### Empty or Incomplete Output

**Cause**: Section extraction failed or no requirements found

**Solution**:
1. Verify document was uploaded correctly to ChromaDB
2. Check document has readable text (not scanned images)
3. Try different `sectioning_strategy` (e.g., "by_metadata" → "auto")
4. Review logs for extraction errors

### Format Doesn't Match Reference

**Cause**: Default export format differs from reference

**Solution**:
1. Use **Professional (Pandoc)** export method
2. Enable "Include Table of Contents"
3. Enable "Number Sections Automatically"
4. Consider creating a custom Word template

---

## Advanced Usage

### Creating Custom Agent Sets

1. Navigate to **Agent Set Manager** in Streamlit
2. Click "Create New Agent Set"
3. Define stages and agent IDs
4. Set execution modes (parallel/sequential)
5. Save and use in Document Generator

### Comparison Mode (Coming Soon)

Automated comparison of generated test plans to reference documents:
- Structure similarity scoring
- Requirement coverage analysis
- Format consistency checks
- Side-by-side section comparison

### Template System (Planned)

Extract structure from reference documents as reusable templates:
- Parse `ipv6v4_may09.pdf` structure
- Apply template to new documents
- Ensure consistent formatting

---

## Current Limitations

1. **Large Documents**: Documents >100 pages may require optimization
2. **Processing Time**: 5-15 minutes for comprehensive test plans
3. **Image-based PDFs**: Scanned documents require OCR preprocessing
4. **Format Preservation**: Some formatting from source may be lost

---

## API Reference

### POST /doc_gen/generate_documents

Generate comprehensive test plan with multi-agent pipeline.

**Request**:
```json
{
  "source_collections": ["collection_name"],
  "source_doc_ids": ["document_id"],
  "doc_title": "Test Plan Title",
  "agent_set_id": 1,
  "use_rag": true,
  "top_k": 5,
  "sectioning_strategy": "auto",
  "chunks_per_section": 5
}
```

**Response**:
```json
{
  "documents": [
    {
      "title": "Test Plan Title",
      "content": "Markdown content...",
      "docx_b64": "base64_encoded_word_document",
      "total_sections": 42,
      "total_requirements": 156,
      "total_test_procedures": 89,
      "pipeline_id": "pipeline_abc123"
    }
  ]
}
```

### POST /doc_gen/generate_optimized_test_plan

Optimized endpoint with caching and performance improvements.

### POST /doc_gen/export-test-plan-with-cards

Export test plan with embedded test cards using Pandoc.

---

## Version History

- **v1.0** (2025-11-10): Initial implementation with multi-agent pipeline
- **v1.1** (2025-11-10): Added agent set validation, improved error handling, comprehensive documentation
- **v1.2** (2025-11-10): Fixed context length errors with dynamic token adjustment and reduced agent max_tokens
- **v1.3** (2025-11-10): Added background processing with progress tracking - eliminates timeout errors!
- **v1.4** (2025-11-10): Added pipeline management - can resume after refresh, list all pipelines, URL persistence
- **v1.5** (Current): Added pipeline cancellation - can stop running generations gracefully

---

## Quick Reference Commands

### List All Pipelines
```bash
# Shows all active pipelines with status and titles
./scripts/check_pipeline_status.sh
```

### Check Specific Pipeline
```bash
# Get detailed status of a specific pipeline
./scripts/check_pipeline_status.sh pipeline_1408be164480
```

### Cancel a Running Pipeline
```bash
# Cancel/stop a pipeline that's processing
./scripts/check_pipeline_status.sh cancel pipeline_1408be164480

# Or via API
curl -X POST http://localhost:9020/api/doc_gen/cancel-pipeline/pipeline_1408be164480

# Or via UI
# 1. Open Document Generator with your pipeline
# 2. Click "❌ Cancel" button
# 3. Pipeline stops at next checkpoint
```

**What Happens When You Cancel:**
- ✅ Pipeline stops gracefully at next checkpoint
- ✅ Partial results are saved (sections completed so far)
- ✅ Status changes to "cancelling" then "failed"
- ✅ No data is lost - partial work is preserved

**When to Cancel:**
- Wrong document selected
- Wrong agent set chosen
- Document too large (want to try smaller one first)
- Just want to stop and restart

### Get Result When Completed
```bash
# Via API
curl -o test_plan.json http://localhost:9020/api/doc_gen/generation-result/pipeline_1408be164480

# Via UI
# 1. Open Document Generator
# 2. Click "Resume Existing Generation"
# 3. Click "Resume" on your completed pipeline
# 4. Click "Download" button
```

### Monitor Continuous Progress
```bash
# Check every 30 seconds
watch -n 30 ./scripts/check_pipeline_status.sh pipeline_1408be164480

# Watch Docker logs
docker logs -f fastapi | grep "pipeline_1408be164480"
```

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. **List your pipelines**: `./scripts/check_pipeline_status.sh`
3. Review logs in Docker containers:
   ```bash
   docker logs fastapi
   docker logs streamlit
   ```
4. Verify database and Redis are running:
   ```bash
   docker ps
   ```
