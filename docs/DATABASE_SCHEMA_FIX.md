# Database Schema Fix - P1 Compliance

**Date:** 2025-01-XX  
**Issue:** Critical database schema mismatch preventing application launch  
**Status:** ✅ RESOLVED

---

## Problem Summary

The application was failing on startup with the error:
```
Database transaction failed: no such table: files
Error updating inventory: no such table: files
```

**Root Cause:** `database.py` was using an old schema (projects, sessions, images, ocr_results, llm_analyses) instead of the P1 specification schema (files, pages, classifications, descriptions).

---

## Solution

### 1. Database Schema Rewrite

Completely rewrote `src/models/database.py` to implement the P1 schema as specified in `docs/P1_COMPLETE.md`:

**Old Schema (Pre-P1):**
- `projects` - Project organization
- `sessions` - Work session tracking
- `images` - Image metadata
- `ocr_results` - OCR extraction data
- `llm_analyses` - LLM analysis results
- `tags` - Tag definitions
- `image_tags` - Junction table for tags

**New Schema (P1 Compliant):**
- `files` - File metadata with hash-based deduplication
- `pages` - Per-page OCR results
- `classifications` - File tags/classifications
- `descriptions` - File descriptions

### 2. Files Table
```sql
CREATE TABLE files (
    file_id INTEGER PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,  -- SHA-256 for deduplication
    file_type TEXT,
    page_count INTEGER,
    file_size INTEGER,
    created_at TEXT,
    modified_at TEXT,
    analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_files_hash ON files(file_hash);
```

### 3. Pages Table + FTS5
```sql
CREATE TABLE pages (
    page_id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    ocr_text TEXT,
    ocr_confidence REAL,
    ocr_mode TEXT,
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE pages_fts USING fts5(
    ocr_text,
    content='pages',
    content_rowid='page_id'
);
```

### 4. Classifications Table + FTS5
```sql
CREATE TABLE classifications (
    classification_id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    tag_number INTEGER,
    tag_text TEXT,
    confidence REAL,
    model_used TEXT,
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE classifications_fts USING fts5(
    tag_text,
    content='classifications',
    content_rowid='classification_id'
);
```

### 5. Descriptions Table
```sql
CREATE TABLE descriptions (
    description_id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    description_text TEXT,
    confidence REAL,
    model_used TEXT,
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
);
```

---

## Service Updates

### File Watcher Fix

**Problem:** `file_watcher.py` was querying a non-existent `status` column:
```python
# OLD (BROKEN)
cursor.execute("SELECT file_hash FROM files WHERE status != 'pending'")
```

**Solution:** Updated to use P1 schema logic - a file is "analyzed" if it has descriptions or classifications:
```python
# NEW (P1 COMPLIANT)
cursor.execute("""
    SELECT DISTINCT f.file_hash 
    FROM files f
    WHERE EXISTS (
        SELECT 1 FROM descriptions d WHERE d.file_id = f.file_id
    ) OR EXISTS (
        SELECT 1 FROM classifications c WHERE c.file_id = f.file_id
    )
""")
```

---

## Changes Made

### Files Modified
1. **src/models/database.py** - Complete schema rewrite
   - Removed 8 old table methods
   - Added 4 new P1 table methods
   - Updated FTS5 tables for pages and classifications
   - Updated indexes for P1 schema
   - Fixed `search_full_text()` to query P1 tables
   - Updated `get_statistics()` for P1 tables

2. **src/services/file_watcher.py** - Fixed inventory query
   - Updated analyzed file detection logic
   - Now uses JOIN queries to check for descriptions/classifications

---

## Testing Results

### Before Fix
```
ERROR: no such table: files
ERROR: Database transaction failed
ERROR: File watcher error: INVENTORY_ERROR
APPLICATION: Could not launch
```

### After Fix
```
✅ Database schema initialized successfully
✅ Inventory updated: 0 total, 0 unanalyzed
✅ Application launches successfully
⚠️  Tesseract warning (expected - not installed yet)
```

---

## Key Learnings

1. **Schema Mismatch Detection:** The `get_database()` function now checks for the `files` table as a P1 schema marker
2. **Automatic Migration:** Old databases are detected and reinitialized with P1 schema
3. **Service Coupling:** Services must query the actual schema, not assume column existence
4. **FTS5 Integration:** Full-text search now correctly targets `pages_fts` and `classifications_fts`

---

## Next Steps

1. ✅ Database schema P1 compliant
2. ✅ Application launches successfully
3. ⏳ Install Tesseract OCR (user action required)
4. ⏳ End-to-end testing with real files
5. ⏳ Verify model dropdown works with live Ollama

---

## Migration Path

For users with old databases:
1. Old database is automatically detected (no `files` table)
2. Schema is reinitialized with P1 specification
3. **Note:** Old data is not migrated (fresh start with P1)

If data migration is needed in the future, implement conversion script to map:
- `images` → `files`
- `ocr_results` → `pages`
- `llm_analyses` → `classifications` + `descriptions`

---

## References

- **P1 Specification:** `docs/P1_COMPLETE.md` (lines 200-350)
- **Schema Documentation:** `previewless_insight_viewer_complete_documentation_pack.md` (section 13)
- **Database Module:** `src/models/database.py`
- **File Watcher:** `src/services/file_watcher.py`
