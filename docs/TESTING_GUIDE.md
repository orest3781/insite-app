# Testing Guide - InSite App

**Last Updated:** October 12, 2025  
**Status:** P1 Complete - Ready for Testing

---

## Prerequisites Checklist

Before testing, ensure all dependencies are installed:

### 1. Python Dependencies
```powershell
# Install from requirements.txt
cd S:\insite-app
pip install -r requirements.txt
```

**Expected packages:**
- PySide6 >= 6.6.0
- pytesseract >= 0.3.10
- Pillow >= 10.0.0
- pdf2image >= 1.16.0
- requests >= 2.31.0

### 2. Tesseract OCR
**Download:** https://github.com/UB-Mannheim/tesseract/wiki

**Installation:**
1. Download installer for Windows
2. Run installer (default location: `C:\Program Files\Tesseract-OCR`)
3. Add to PATH or note installation path for settings

**Verify installation:**
```powershell
tesseract --version
# Expected: tesseract 5.x.x
```

### 3. Poppler (for PDF support)
**Download:** https://github.com/oschwartz10612/poppler-windows/releases

**Installation:**
1. Download latest release (poppler-xx.xx.x-win64.zip)
2. Extract to a permanent location (e.g., `C:\Program Files\poppler-xx`)
3. Note the path to `bin` folder for settings

**Verify installation:**
```powershell
# Navigate to poppler bin directory
cd "C:\Program Files\poppler-xx\Library\bin"
.\pdftoppm.exe -v
# Expected: pdftoppm version x.xx.x
```

### 4. Ollama (Optional - for LLM features)
**Download:** https://ollama.ai

**Installation:**
1. Download and run installer
2. Ollama runs as a service on `localhost:11434`
3. Pull the model:
```powershell
ollama pull llama3.2
```

**Verify installation:**
```powershell
ollama list
# Expected: llama3.2 listed
```

---

## Test Plan

### Phase 1: Basic Functionality (No External Dependencies)

#### Test 1.1: Application Launch
```powershell
cd S:\insite-app
python main.py
```

**Expected:**
- ✅ Application window opens
- ✅ Dark theme applied
- ✅ Status bar shows "Ready"
- ✅ No error dialogs

**Pass Criteria:** Application launches without errors

---

#### Test 1.2: UI Navigation
**Steps:**
1. Click each tab: Watch, Queue, Processing
2. Check File menu → Settings
3. Check Tools menu → Diagnostics
4. Check Help menu → About

**Expected:**
- ✅ All tabs switch correctly
- ✅ Settings dialog opens
- ✅ Diagnostics dialog opens
- ✅ About dialog shows version info

**Pass Criteria:** All UI elements accessible

---

#### Test 1.3: Database Creation
**Steps:**
1. Launch application
2. Check for `app_data` folder in project root
3. Check for `insite.db` file

**Expected:**
- ✅ `app_data/` directory created
- ✅ `insite.db` file exists
- ✅ File size > 0 bytes

**Verify schema:**
```powershell
# Using SQLite command line or DB Browser
sqlite3 app_data/insite.db
.tables
# Expected: files, pages, classifications, descriptions, etc.
```

**Pass Criteria:** Database created with correct schema

---

### Phase 2: Settings & Configuration

#### Test 2.1: Configure Tesseract Path
**Steps:**
1. File → Settings
2. OCR tab → Tesseract Executable
3. Browse to: `C:\Program Files\Tesseract-OCR\tesseract.exe`
4. Click Apply → OK

**Expected:**
- ✅ Path saved
- ✅ Settings dialog closes
- ✅ Green status message: "Settings saved"

**Verify:**
```powershell
# Check config file
cat app_data/config.json | Select-String "tesseract"
# Expected: "tesseract_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

**Pass Criteria:** Tesseract path saved to config

---

#### Test 2.2: Configure Poppler Path
**Steps:**
1. File → Settings
2. OCR tab → Poppler Path
3. Browse to: `C:\Program Files\poppler-xx\Library\bin`
4. Click Apply → OK

**Expected:**
- ✅ Path saved
- ✅ Settings persisted

**Pass Criteria:** Poppler path configured

---

#### Test 2.3: Configure Ollama
**Steps:**
1. File → Settings
2. LLM tab → Ollama URL
3. Enter: `http://localhost:11434`
4. LLM tab → Model Name
5. Enter: `llama3.2`
6. Click Apply → OK

**Expected:**
- ✅ Settings saved
- ✅ No connection errors

**Pass Criteria:** Ollama configured

---

### Phase 3: Diagnostics

#### Test 3.1: Run Diagnostics
**Steps:**
1. Tools → Diagnostics
2. Review all sections:
   - Python Environment
   - Dependencies
   - Tesseract OCR
   - Ollama LLM
   - Database
   - File System

**Expected:**
- ✅ Python version: 3.11.4
- ✅ PySide6 installed: Yes
- ✅ Tesseract path: Valid (if configured)
- ✅ Ollama connection: Success (if running)
- ✅ Database: Accessible
- ✅ Write permissions: OK

**Pass Criteria:** All critical checks pass (green)

---

### Phase 4: File Watching

#### Test 4.1: Add Watch Folder
**Preparation:**
Create test folder with sample files:
```powershell
mkdir S:\insite-app\test_files
# Add 3-5 PDF files and images
```

**Steps:**
1. Switch to Watch tab
2. Click "Add Folder"
3. Select `S:\insite-app\test_files`
4. Click Select Folder

**Expected:**
- ✅ Folder added to list
- ✅ Inventory stats update (e.g., "Total: 5 files")
- ✅ Breakdown by type shown (e.g., "PDF: 3, Images: 2")

**Pass Criteria:** Files detected and counted correctly

---

#### Test 4.2: Refresh Inventory
**Steps:**
1. Add more files to test folder externally
2. Click "Refresh" button (or press F5)

**Expected:**
- ✅ Inventory stats update
- ✅ New files counted

**Pass Criteria:** Inventory updates on refresh

---

### Phase 5: Queue Management

#### Test 5.1: Enqueue Files
**Steps:**
1. Switch to Queue tab
2. Click "Enqueue Selected Files"
3. Select 2-3 files from test folder
4. Click Open

**Expected:**
- ✅ Files added to queue table
- ✅ Status shows "Pending"
- ✅ File type detected correctly
- ✅ Priority shown

**Pass Criteria:** Files appear in queue

---

#### Test 5.2: Reorder Queue
**Steps:**
1. Select bottom item in queue
2. Click "↑ Move Up" button
3. Repeat to move to top

**Expected:**
- ✅ Item moves up one position per click
- ✅ Order persists

**Pass Criteria:** Queue reordering works

---

#### Test 5.3: Remove from Queue
**Steps:**
1. Select item in queue
2. Click "Remove Selected"

**Expected:**
- ✅ Item removed from queue
- ✅ Progress bar updates

**Pass Criteria:** Item removal works

---

### Phase 6: Processing (Requires All Dependencies)

#### Test 6.1: Start Processing
**Steps:**
1. Ensure queue has 1-2 files
2. Switch to Processing tab
3. Click "▶ Start Processing"

**Expected:**
- ✅ Status changes to "RUNNING"
- ✅ Current file shows file name
- ✅ Progress bar starts advancing
- ✅ Pause/Stop buttons enabled

**Pass Criteria:** Processing starts

---

#### Test 6.2: OCR Extraction
**Monitor console logs for:**
```
INFO - Starting OCR for: test_file.pdf
INFO - OCR completed: 1 pages, avg confidence 0.85
```

**Expected:**
- ✅ OCR completes without errors
- ✅ Confidence scores reasonable (>0.7)

**Pass Criteria:** OCR extracts text

---

#### Test 6.3: LLM Classification
**Monitor console logs for:**
```
INFO - Generating classification for: test_file.pdf
INFO - Classification generated: 6 tags
INFO - Generating description for: test_file.pdf
INFO - Description generated: 2 sentences
```

**Expected:**
- ✅ LLM generates 6 tags
- ✅ LLM generates 2-sentence description
- ✅ Confidence scores present

**Pass Criteria:** LLM classification works

---

#### Test 6.4: Review Dialog
**Expected:**
- ✅ ReviewDialog opens automatically
- ✅ OCR text displayed
- ✅ 6 tag fields populated
- ✅ Description field populated (2 sentences)
- ✅ Confidence indicators shown

**Steps:**
1. Review OCR text
2. Edit tags if needed
3. Edit description if needed
4. Click "✓ Approve"

**Expected:**
- ✅ Dialog closes
- ✅ Processing continues to next file

**Pass Criteria:** Review workflow functional

---

#### Test 6.5: Database Save
**Verify save occurred:**
```powershell
sqlite3 app_data/insite.db
SELECT COUNT(*) FROM files;
# Expected: 1 (or number of approved files)

SELECT file_path, file_hash FROM files;
# Expected: Shows processed file

SELECT COUNT(*) FROM pages;
# Expected: Number of pages processed

SELECT COUNT(*) FROM classifications;
# Expected: 6 per file (6 tags)
```

**Pass Criteria:** All data saved to database

---

#### Test 6.6: Pause Processing
**Steps:**
1. Start processing with multiple files
2. Click "⏸ Pause" button

**Expected:**
- ✅ Status changes to "PAUSED"
- ✅ Current file completes
- ✅ Resume button enabled

**Pass Criteria:** Pause functionality works

---

#### Test 6.7: Resume Processing
**Steps:**
1. From paused state, click "▶ Resume"

**Expected:**
- ✅ Status changes to "RUNNING"
- ✅ Next file starts processing

**Pass Criteria:** Resume functionality works

---

#### Test 6.8: Stop Processing
**Steps:**
1. Start processing
2. Click "⏹ Stop" button

**Expected:**
- ✅ Status changes to "STOPPED"
- ✅ Processing ends
- ✅ Partial progress saved

**Pass Criteria:** Stop functionality works

---

### Phase 7: Search & Retrieval

#### Test 7.1: Full-Text Search (OCR)
```sql
sqlite3 app_data/insite.db

-- Search OCR text
SELECT * FROM pages_fts WHERE pages_fts MATCH 'invoice';

-- Expected: Rows containing "invoice" in OCR text
```

**Pass Criteria:** FTS5 search returns correct results

---

#### Test 7.2: Tag Search
```sql
-- Search classifications
SELECT f.file_path, c.tag_text 
FROM classifications c
JOIN files f ON c.file_id = f.file_id
WHERE c.tag_text LIKE '%financial%';

-- Or using FTS5:
SELECT * FROM classifications_fts WHERE tag_text MATCH 'financial';
```

**Pass Criteria:** Tag search works

---

#### Test 7.3: Description Search
```sql
-- Search descriptions
SELECT f.file_path, d.description_text
FROM descriptions d
JOIN files f ON d.file_id = f.file_id
WHERE d.description_text LIKE '%contract%';
```

**Pass Criteria:** Description search works

---

### Phase 8: Error Handling

#### Test 8.1: Missing Tesseract
**Steps:**
1. File → Settings → Clear Tesseract path
2. Try to start processing

**Expected:**
- ✅ Clear error message: "Tesseract not found"
- ✅ Suggested action shown
- ✅ Processing doesn't start

**Pass Criteria:** Graceful error handling

---

#### Test 8.2: Ollama Not Running
**Steps:**
1. Stop Ollama service
2. Try to start processing

**Expected:**
- ✅ Error message: "Cannot connect to Ollama"
- ✅ Falls back to OCR-only mode (if configured)
- ✅ User notified

**Pass Criteria:** Graceful degradation

---

#### Test 8.3: Corrupted File
**Steps:**
1. Create empty file with .pdf extension
2. Add to queue
3. Start processing

**Expected:**
- ✅ Error logged
- ✅ Status shows "FAILED"
- ✅ Skipped count increments
- ✅ Processing continues to next file

**Pass Criteria:** Error doesn't crash app

---

### Phase 9: Performance

#### Test 9.1: Processing Speed
**Measure time for:**
- 1-page PDF (Fast mode): ~5 seconds
- 1-page PDF (High Accuracy): ~11 seconds
- 10-page PDF (Fast mode): ~50 seconds

**Pass Criteria:** Within expected performance ranges

---

#### Test 9.2: Memory Usage
**Monitor Task Manager during processing:**

**Expected:**
- Idle: ~150-200 MB
- Processing (1 file): ~250-300 MB
- Processing (10 files): <500 MB

**Pass Criteria:** No memory leaks

---

### Phase 10: Portability

#### Test 10.1: Move Installation
**Steps:**
1. Close application
2. Move entire `S:\insite-app` folder to `D:\test-insite`
3. Launch from new location

**Expected:**
- ✅ Application starts
- ✅ Database accessible
- ✅ Settings preserved
- ✅ Watch folders still work (if paths still valid)

**Pass Criteria:** Fully portable

---

## Bug Reporting Template

If you find issues, report with:

```markdown
**Bug:** [Short description]

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. ...

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Environment:**
- OS: Windows 10/11
- Python: 3.11.4
- Tesseract: 5.x.x
- Ollama: x.x.x

**Logs:**
[Paste relevant log entries from console]

**Database State:**
[If applicable, SQL query results]
```

---

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ Application launches without errors
- ✅ Settings can be configured
- ✅ Files can be watched and enqueued
- ✅ OCR extracts text from images/PDFs
- ✅ LLM generates classifications and descriptions
- ✅ Review dialog shows results
- ✅ Results saved to database
- ✅ Search functionality works
- ✅ Error handling prevents crashes

### Ready for v1.0 Release
- ✅ All Phase 1-10 tests pass
- ✅ No critical bugs
- ✅ Performance within expected ranges
- ✅ Documentation complete
- ✅ User can complete end-to-end workflow

---

## Test Results Tracking

| Phase | Tests | Passed | Failed | Notes |
|-------|-------|--------|--------|-------|
| 1. Basic Functionality | 3 | - | - | |
| 2. Settings | 3 | - | - | |
| 3. Diagnostics | 1 | - | - | |
| 4. File Watching | 2 | - | - | |
| 5. Queue Management | 3 | - | - | |
| 6. Processing | 8 | - | - | |
| 7. Search | 3 | - | - | |
| 8. Error Handling | 3 | - | - | |
| 9. Performance | 2 | - | - | |
| 10. Portability | 1 | - | - | |
| **TOTAL** | **29** | **-** | **-** | |

---

**Next Step:** Run through all test phases and document results!
