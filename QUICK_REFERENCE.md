# Position-Aware Migration - Quick Reference Card

## 🚀 Getting Started

```bash
# 1. Run quick-start script
./start_migration.sh

# 2. Follow MIGRATION_PLAN.md
# 3. Track progress in MIGRATION_PROGRESS.md
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| **MIGRATION_PLAN.md** | Complete step-by-step migration guide (8 phases) |
| **MIGRATION_PROGRESS.md** | Progress tracking checklist |
| **SOLUTION_SUMMARY.md** | Overall solution overview |
| **POSITION_AWARE_INTEGRATION_GUIDE.md** | Detailed integration documentation |
| **migration_example.py** | Before/after code examples |
| **start_migration.sh** | Quick-start automation script |

---

## 🔧 New Modules Created

| Module | Location | Purpose |
|--------|----------|---------|
| **position_aware_extraction.py** | `src/fastapi/services/` | Extract images with positions |
| **position_aware_chunking.py** | `src/fastapi/services/` | Chunk documents preserving positions |
| **position_aware_reconstruction.py** | `src/fastapi/services/` | Rebuild docs with correct image placement |

---

## 📝 Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| **document_ingestion_service.py** | Add imports, extraction wrapper, chunking wrapper | ~32, ~589, ~1115, ~1190, ~1244 |
| **vectordb_api.py** | Add imports, reconstruction function, update endpoint | ~11, ~20, ~453 |
| **.env** | Add feature flags | New lines |

---

## 🎯 Migration Phases

| Phase | Time | Status |
|-------|------|--------|
| 1. Setup & Validation | 30 min | ⬜ |
| 2. Add New Modules | 1 hour | ⬜ |
| 3. Refactor Extraction | 1 hour | ⬜ |
| 4. Refactor Chunking | 1 hour | ⬜ |
| 5. Update Reconstruction | 1 hour | ⬜ |
| 6. End-to-End Testing | 1 hour | ⬜ |
| 7. Cleanup & Docs | 30 min | ⬜ |
| 8. Deploy & Monitor | 30 min | ⬜ |
| **TOTAL** | **4-6 hours** | |

---

## ✅ Key Changes

### Before (Current)
```python
# Extraction
pages_data = extract_and_store_images_from_file(content, fname, tmp_dir, fname)

# Chunking
chunks = []
for page in pages_data:
    chunks.append({"content": text, "images": [...]})

# Metadata
meta = {
    "image_filenames": json.dumps([...]),
    "image_storage_paths": json.dumps([...])
}

# Reconstruction
# Images dumped at end of chunks
```

### After (New)
```python
# Extraction with positions
pages_data = extract_images_with_positions(content, fname, tmp_dir, fname, IMAGES_DIR)
pages_data = add_text_anchors_to_images(pages_data)

# Chunking with positions
chunks = page_based_chunking_with_positions(pages_data, fname)

# Metadata with positions
meta = {
    "image_positions": json.dumps([{
        "filename": "img.png",
        "bbox": [x0, y0, x1, y1],
        "char_offset": 123,
        "text_before": "...",
        "placement_hint": "inline"
    }])
}

# Reconstruction with positions
content, images, meta = reconstruct_document_with_positions(chunks_data)
# Images inserted at correct positions
```

---

## 🧪 Testing Commands

### Test Upload
```bash
curl -X POST "http://localhost:8000/api/vectordb/documents/upload-and-process" \
  -F "files=@test.pdf" \
  -F "collection_name=test_collection" \
  -F "vision_models=enhanced_local"
```

### Check Job Status
```bash
curl "http://localhost:8000/api/vectordb/jobs/{job_id}"
```

### Test Reconstruction
```bash
curl "http://localhost:8000/api/vectordb/documents/reconstruct/{doc_id}?collection_name=test_collection"
```

### View Logs
```bash
docker-compose logs -f fastapi | grep -i "position"
```

---

## 🔍 Verification Checklist

After each phase:

- [ ] No syntax errors
- [ ] Service restarts successfully
- [ ] Logs show expected messages
- [ ] Tests pass
- [ ] No errors in production

After complete migration:

- [ ] Upload succeeds
- [ ] `reconstruction_method` is `"position_aware"`
- [ ] Images appear inline (not at end)
- [ ] Metadata contains `image_positions`
- [ ] Performance acceptable (<15% overhead)
- [ ] Backward compatibility maintained

---

## 🆘 Quick Troubleshooting

### Import Errors
```bash
# Check files exist
ls -la src/fastapi/services/position_aware_*.py

# Restart service
docker-compose restart fastapi
```

### Images Still at End
```bash
# Check feature flags
grep "USE_POSITION_AWARE" .env

# Check logs
docker-compose logs fastapi | grep "position-aware"

# Verify metadata
# (See MIGRATION_PLAN.md Step 6.3)
```

### Reconstruction Fails
```bash
# Check reconstruction method
curl ".../reconstruct/{doc_id}?..." | jq '.metadata.reconstruction_method'

# Should be "position_aware", not "legacy"

# Check logs
docker-compose logs fastapi | grep "reconstruction"
```

---

## 🔄 Rollback Options

### Quick Rollback (Git)
```bash
git checkout pre-position-aware-migration
docker-compose build && docker-compose up -d
```

### Feature Flag Rollback
```bash
# In .env
USE_POSITION_AWARE_EXTRACTION=false
USE_POSITION_AWARE_RECONSTRUCTION=false

# Restart
docker-compose restart fastapi
```

---

## 📊 Expected Results

### Position Metadata Structure
```json
{
  "filename": "img1.png",
  "storage_path": "/path/to/img1.png",
  "page_number": 2,
  "page_sequence": 0,
  "bbox": [72.0, 500.0, 272.0, 700.0],
  "char_offset": 1234,
  "text_before": "The following diagram shows...",
  "text_after": "As illustrated above...",
  "placement_hint": "inline",
  "description": "Diagram showing architecture"
}
```

### Reconstruction Output
```markdown
# Document

## Section 1

Introduction text here.

![Image 1: Diagram](img1.png)
*Diagram showing architecture*

As shown in the diagram above, the system...
```

---

## 📞 Support Resources

1. **MIGRATION_PLAN.md** - Detailed step-by-step guide
2. **SOLUTION_SUMMARY.md** - High-level overview
3. **POSITION_AWARE_INTEGRATION_GUIDE.md** - Integration details
4. **migration_example.py** - Code examples
5. **Logs** - `docker-compose logs -f fastapi`

---

## ⚡ Quick Commands

```bash
# Start migration
./start_migration.sh

# View plan
less MIGRATION_PLAN.md

# Track progress
code MIGRATION_PROGRESS.md

# View logs
docker-compose logs -f fastapi

# Restart service
docker-compose restart fastapi

# Run tests
python test_position_modules.py

# Check git status
git status

# Commit changes
git add . && git commit -m "feat: position-aware images"

# Create PR
git push origin feature/position-aware-images
```

---

## 🎓 Learning Path

1. Read **SOLUTION_SUMMARY.md** (5 min)
2. Skim **MIGRATION_PLAN.md** (10 min)
3. Run **start_migration.sh** (5 min)
4. Follow **MIGRATION_PLAN.md** Phase 1 (30 min)
5. Continue through all phases (4-6 hours total)
6. Deploy and monitor (30 min)

---

## ✨ Success Indicators

- ✅ Images at correct positions in reconstructed docs
- ✅ `reconstruction_method: "position_aware"`
- ✅ Metadata contains `image_positions` JSON
- ✅ No errors in logs
- ✅ Performance overhead <15%
- ✅ Backward compatibility maintained
- ✅ All tests passing

---

**Estimated Total Time:** 4-6 hours
**Difficulty:** Medium
**Risk:** Low (backward compatible)

Ready to begin! 🚀
