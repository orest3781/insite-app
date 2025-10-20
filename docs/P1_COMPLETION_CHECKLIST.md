# Phase P1 - Completion Checklist

**Target:** Complete P1 Core Processing Pipeline  
**Estimated Time:** 6-10 hours  
**Priority:** High

---

## Pre-Work: Dependencies Installation

### Python Packages
```powershell
# Install OCR and image processing dependencies
pip install pytesseract Pillow pdf2image
```

### External Tools
- [ ] **Tesseract OCR** - Download from https://github.com/UB-Mannheim/tesseract/wiki
  - Install to: `C:\Program Files\Tesseract-OCR\`
  - Add to PATH or configure in settings
  - Verify: `tesseract --version`

- [ ] **Poppler (for pdf2image)** - Download from https://github.com/oschwartz10612/poppler-windows/releases
  - Extract to: `C:\Program Files\poppler-xx\`
  - Add `bin` folder to PATH
  - Verify: `pdftoppm -v`

- [ ] **Ollama (optional, for LLM)** - Download from https://ollama.ai
  - Install and start service
  - Pull model: `ollama pull llama2`
  - Verify: `ollama list`

---

## Phase 1: Testing Individual Services (2 hours)

### File Watcher Tests
- [ ] Create test directory: `S:\insite-app\test_data\`
- [ ] Add sample files (PDF, images, text)
- [ ] Start file watcher
- [ ] Verify files detected
- [ ] Check inventory counts
- [ ] Test add/remove watch paths
- [ ] Verify signals emitted

### Queue Manager Tests
- [ ] Create queue instance
- [ ] Add items manually
- [ ] Test reordering (move up/down)
- [ ] Test priority handling
- [ ] Test batch add/remove
- [ ] Verify status updates
- [ ] Check statistics calculation

### OCR Adapter Tests
- [ ] Test with sample image
  - [ ] Fast mode
  - [ ] High-accuracy mode
  - [ ] Verify text extraction
  - [ ] Check confidence scores
- [ ] Test with sample PDF
  - [ ] Multi-page processing
  - [ ] Page navigation
  - [ ] Error handling (encrypted PDF)

### LLM Adapter Tests
- [ ] Verify Ollama connection
- [ ] List available models
- [ ] Test classification prompt
  - [ ] Verify 6 tags generated
  - [ ] Check tag format (category:value)
- [ ] Test description prompt
  - [ ] Verify 2 sentences
  - [ ] Check factual content
  - [ ] Verify no speculation

### Processing Orchestrator Tests
- [ ] Start/stop processing
- [ ] Test pause/resume
- [ ] Verify hash calculation
- [ ] Test deduplication
- [ ] Check confidence triggers
- [ ] Verify error handling
- [ ] Test retry logic

### Review Dialog Tests
- [ ] Load mock ProcessingResult
- [ ] Navigate multi-page OCR
- [ ] Edit tags
- [ ] Edit description
- [ ] Test validation
  - [ ] Tag count (min 6)
  - [ ] Sentence count (exactly 2)
- [ ] Approve results
- [ ] Reject results

---

## Phase 2: Main Window Integration (4-6 hours)

### Watch Tab
- [ ] Create QWidget for Watch tab
- [ ] Add folder list (QListWidget)
- [ ] Add "Add Folder" button
- [ ] Add "Remove Folder" button
- [ ] Add "Refresh" button
- [ ] Show inventory stats
  - [ ] Total files
  - [ ] By type (PDF, images, etc.)
  - [ ] Unanalyzed count
- [ ] Connect file_watcher signals
  - [ ] inventory_updated → update UI
  - [ ] file_added → increment count
  - [ ] file_removed → decrement count
  - [ ] error_occurred → show error

**Layout:**
```
┌─────────────────────────────────────┐
│ Watched Folders                     │
│ ┌─────────────────────────────────┐ │
│ │ S:\Documents\                   │ │
│ │ S:\Downloads\                   │ │
│ │ S:\Desktop\Scans\               │ │
│ └─────────────────────────────────┘ │
│ [Add Folder] [Remove] [Refresh]    │
│                                     │
│ Inventory:                          │
│ - Total Files: 1,234                │
│ - PDFs: 456                         │
│ - Images: 678                       │
│ - Unanalyzed: 123                   │
└─────────────────────────────────────┘
```

### Queue Tab
- [ ] Create QWidget for Queue tab
- [ ] Add queue table (QTableWidget)
  - [ ] Columns: File, Type, Status, Priority
  - [ ] Enable drag-drop reordering
- [ ] Add "Enqueue Selected" button
- [ ] Add "Remove Selected" button
- [ ] Add "Clear Queue" button
- [ ] Add priority controls (↑ ↓)
- [ ] Connect queue_manager signals
  - [ ] item_added → add row
  - [ ] item_removed → remove row
  - [ ] item_updated → update status
  - [ ] queue_reordered → refresh table
  - [ ] progress_changed → update progress bar

**Layout:**
```
┌─────────────────────────────────────┐
│ Processing Queue                    │
│ ┌─────────────────────────────────┐ │
│ │ File      │Type│Status │Priority││
│ ├─────────────────────────────────┤ │
│ │doc1.pdf   │PDF │Pending│ 5      ││
│ │scan2.jpg  │IMG │Pending│ 3      ││
│ │form3.pdf  │PDF │Process│ 8      ││
│ └─────────────────────────────────┘ │
│ [↑] [↓] [Remove] [Clear]           │
│ Progress: ████████░░ 45/100         │
└─────────────────────────────────────┘
```

### Processing Tab
- [ ] Create QWidget for Processing tab
- [ ] Add status label (IDLE/RUNNING/PAUSED)
- [ ] Add progress bar (overall)
- [ ] Add current file label
- [ ] Add statistics panel
  - [ ] Processed count
  - [ ] Failed count
  - [ ] Skipped count
  - [ ] Processing time
- [ ] Add control buttons
  - [ ] Start Processing
  - [ ] Pause
  - [ ] Stop
  - [ ] Retry Failed
- [ ] Connect orchestrator signals
  - [ ] processing_started → update status
  - [ ] processing_paused → update status
  - [ ] processing_stopped → update status
  - [ ] processing_completed → show summary
  - [ ] item_processing_started → update current file
  - [ ] item_processing_completed → increment count
  - [ ] item_processing_failed → increment failed
  - [ ] progress_updated → update progress bar
  - [ ] state_changed → update UI state
  - [ ] review_required → open review dialog

**Layout:**
```
┌─────────────────────────────────────┐
│ Processing Status: RUNNING          │
│                                     │
│ Current File: document_123.pdf      │
│ Progress: ████████████░ 78/100      │
│                                     │
│ Statistics:                         │
│ - Processed: 78                     │
│ - Failed: 2                         │
│ - Skipped: 5                        │
│ - Time Elapsed: 00:05:23            │
│                                     │
│ [Start] [Pause] [Stop] [Retry]     │
└─────────────────────────────────────┘
```

### Main Window Wiring
- [ ] Add Watch tab to main window
- [ ] Add Queue tab to main window
- [ ] Add Processing tab to main window
- [ ] Initialize services in main window
  - [ ] file_watcher
  - [ ] queue_manager
  - [ ] ocr_adapter
  - [ ] llm_adapter
  - [ ] processing_orchestrator
- [ ] Connect review dialog to orchestrator
  - [ ] review_required signal → show dialog
  - [ ] approved signal → save to database
  - [ ] rejected signal → mark as failed

---

## Phase 3: Database Storage (2-4 hours)

### Implement Save Logic
- [ ] Complete `_save_results()` in processing_orchestrator.py
  - [ ] Insert into `files` table
  - [ ] Insert into `pages` table (for each OCR page)
  - [ ] Insert into `classifications` table
  - [ ] Insert into `descriptions` table
  - [ ] Update FTS5 indexes
- [ ] Add transaction support (commit/rollback)
- [ ] Add error handling for DB writes
- [ ] Test with sample results

### FTS5 Integration
- [ ] Verify FTS5 tables exist
- [ ] Insert description text into `descriptions_fts`
- [ ] Test full-text search
- [ ] Verify ranking and relevance

### Statistics
- [ ] Calculate total processed files
- [ ] Group by file type
- [ ] Group by status
- [ ] Average processing time
- [ ] Top tags (frequency)
- [ ] Add statistics query methods to Database class

---

## Phase 4: End-to-End Testing (2 hours)

### Happy Path Test
- [ ] Add watch folder
- [ ] Detect new files
- [ ] Enqueue files
- [ ] Start processing
- [ ] Verify OCR extraction
- [ ] Verify LLM classification
- [ ] Verify review dialog appears
- [ ] Approve results
- [ ] Verify database save
- [ ] Search for description
- [ ] Find saved result

### Error Scenarios
- [ ] Missing Tesseract → Show error
- [ ] Ollama down → Show error
- [ ] Encrypted PDF → Skip with reason
- [ ] Low OCR confidence → Force review
- [ ] Invalid file type → Skip
- [ ] Duplicate file → Skip (dedup works)
- [ ] Database locked → Retry
- [ ] Disk full → Show error

### Performance Test
- [ ] Process 10 files → Time it
- [ ] Process 100-page PDF → Monitor memory
- [ ] Queue 100 files → Check UI responsiveness
- [ ] Pause/Resume mid-processing
- [ ] Stop processing → Verify cleanup

---

## Phase 5: Polish & Documentation (1 hour)

### Code Cleanup
- [ ] Remove debug print statements
- [ ] Add missing docstrings
- [ ] Update type hints
- [ ] Fix lint warnings
- [ ] Format code (black/autopep8)

### Configuration
- [ ] Add default settings for OCR/LLM
- [ ] Document all settings in settings.json
- [ ] Create sample watched folders list
- [ ] Add example prompts

### Documentation
- [ ] Update README with setup instructions
- [ ] Document OCR/LLM requirements
- [ ] Add troubleshooting section
- [ ] Create quick start guide
- [ ] Update roadmap (mark P1 complete)

---

## Acceptance Criteria

### Must Have (Blocking)
- [ ] File watching detects new files
- [ ] Queue can be reordered
- [ ] OCR extracts text from images
- [ ] OCR extracts text from PDFs
- [ ] LLM generates 6 tags
- [ ] LLM generates 2-sentence description
- [ ] Review dialog validates input
- [ ] Approved results save to database
- [ ] FTS5 search finds descriptions
- [ ] End-to-end test passes

### Should Have (Important)
- [ ] Pause/Resume works reliably
- [ ] Error messages are clear
- [ ] Progress indicators update smoothly
- [ ] Statistics are accurate
- [ ] Deduplication prevents re-processing

### Nice to Have (Polish)
- [ ] Keyboard shortcuts work
- [ ] Drag-drop files to enqueue
- [ ] Export queue to CSV
- [ ] Batch approval mode
- [ ] Processing time estimates

---

## Known Issues to Address

1. **pdf2image dependency** - Need to install Poppler
2. **Tesseract path** - Need to configure in settings or detect automatically
3. **Ollama connection** - Need to handle when service is down
4. **Large files** - Need progress indicator for slow OCR
5. **Memory usage** - Monitor with large PDFs

---

## Definition of Done

P1 is complete when:
1. ✅ All 6 core services implemented
2. ⏳ Main window has Watch/Queue/Processing tabs
3. ⏳ Services connected via signals
4. ⏳ Review dialog integrated
5. ⏳ Database saves working
6. ⏳ FTS5 search functional
7. ⏳ End-to-end test passes
8. ⏳ Documentation updated

**Current:** 6/8 (75%)  
**Target:** 8/8 (100%)

---

## Estimated Timeline

| Task | Hours | Dependencies |
|------|-------|--------------|
| Pre-work (dependencies) | 0.5 | None |
| Testing services | 2 | Dependencies installed |
| Watch tab | 1.5 | None |
| Queue tab | 1.5 | None |
| Processing tab | 1.5 | None |
| Main window wiring | 1 | All tabs complete |
| Database storage | 3 | None |
| End-to-end testing | 2 | All complete |
| Polish | 1 | All complete |
| **TOTAL** | **14 hours** | - |

**Conservative estimate:** 14 hours  
**Optimistic estimate:** 10 hours  
**Realistic:** 12 hours (1.5 work days)

---

## Next Session Checklist

Before starting next session:
1. [ ] Read this checklist
2. [ ] Install dependencies (pip install)
3. [ ] Install external tools (Tesseract, Poppler)
4. [ ] Test individual services
5. [ ] Begin Watch tab implementation

**Goal:** Complete P1 and have working end-to-end pipeline!
