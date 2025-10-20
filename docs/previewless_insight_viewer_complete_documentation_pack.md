# Previewless Insight Viewer — Complete Documentation Pack

> Goal: See what an image/PDF is **without opening it**. Local-first, portable, single user. Python + PySide6 UI, Tesseract OCR, Ollama local LLMs, optional per-run cloud toggle.

---

## 0) Contents

### Core Specification (1-24)
1. Product Vision & Elevator Pitch
2. PRD (Product Requirements Document)
3. User Stories & Use Cases
4. Non‑Functional Requirements (NFRs)
5. Information Architecture & Navigation
6. UX Spec (Screens, States, and Interactions)
7. Style & Content Guidelines (Descriptions & Tags)
8. Presets Specification
9. Folder Watching, Inventory & Queue Specification
10. Processing Pipelines (OCR, Review, Classification)
11. AI & Model Adapters (Tesseract, Ollama, Cloud)
12. Settings & Configuration Schema (portable)
13. Data Model & Database Schema (SQLite)
14. Search & Indexing (FTS5)
15. Logging, Diagnostics & Error Handling
16. Security, Privacy & Portability
17. Build, Packaging & Environment
18. Test Plan & QA Strategy
19. Acceptance Criteria (Go/No‑Go)
20. Release Checklist
21. Maintenance, Updates & Versioning
22. Risks & Mitigations
23. Roadmap (Phased Delivery)
24. Seed Artifacts (Tag Dictionary, Presets, QA Poster)

### Additions & Amendments (A1-A15)
- A1: First-Run & Onboarding (amends §17)
- A2: Prompt Library & Invariants (amends §11)
- A3: Cloud Boundary & PII Policy (amends §16)
- A4: Error Code Catalog (amends §15)
- A5: Performance Budgets (amends §14)
- A6: Import/Export & Housekeeping (amends §12)
- A7: Backup & Restore (amends §16)
- A8: Windows Specifics & Edge Cases (amends §21)
- A9: Diagnostics Bundle (amends §15)
- A10: File Handling Matrix
- A11: Keyboard Shortcuts & Accessibility
- A12: I18N & Theming Stubs
- A13: Compliance Modes & API Surface
- A14: Schema Amendments (amends §13)
- A15: Acceptance & Edge Tests (amends §18)

### Extended Documentation (25-37)
25. Starter Pack (Files to ship in portable root)
26. API & Integration Specification
27. Advanced Features & Power User Tools
28. Performance Optimization Guide
29. Troubleshooting & FAQ
30. Glossary & Terminology
31. Development Guidelines
32. Migration & Upgrade Path
33. Licensing & Legal
34. Future Enhancements (Post-v1)
35. Acknowledgments & References
36. Changelog
37. QSS Styling Guide & Theme System

### Appendices
- **Appendix A:** Complete Settings Reference
- **Appendix B:** Error Code Quick Reference
- **Appendix C:** Sample Workflows

---

## 1) Product Vision & Elevator Pitch
**Vision:** Previewless insight. The app tells you what a file is—type, entities, and key facts—without opening it.

**Elevator pitch (10s):** A portable, single‑user desktop app that turns images/PDFs into clear tags and two‑sentence descriptions locally, using Tesseract for OCR and Ollama for on‑device AI; with an optional per‑run cloud toggle.

**Users:** You (single user). No collaboration or multi‑tenancy.

**Platforms:** Windows desktop (priority), portable install directory (no admin required).

---

## 2) PRD (Product Requirements Document)
**Problem:** Opening files to identify content is slow and risky. Need fast, reliable at‑a‑glance identification.

**Goals:**
- Produce concise, accurate tags and descriptions for files without opening them.
- Work fully offline by default; retain an explicit cloud option per run.
- Keep storage and configuration portable within a single directory.

**Key Features:**
- Watched folders with inventory by filetype, unanalysed count.
- Reorderable queue; manual Start per run.
- OCR (Fast baseline; High‑Accuracy option per page/file).
- Review → Classification → Results flow.
- Tags & Descriptions browser with search (FTS5 on descriptions by default).
- Human‑readable errors with actionable fixes.

**Out of Scope (v1):** Multi‑user sync, server DB, real‑time collaboration, editing files, in‑archive processing.

**Success Metrics:**
- ≥80% of files achieve High confidence on first pass (clean sources).
- <5s median time to first description for single files (fast path).
- <10% of files require manual edits after a month of use (stabilizing taxonomy).

---

## 3) User Stories & Use Cases
- **US‑01:** As a user, I add a folder and immediately see how many PDFs/images exist and how many are unanalysed.
- **US‑02:** As a user, I press **Start** to process the current queue; new files wait for the next run.
- **US‑03:** As a user, I want two‑sentence descriptions and ≤6 canonical tags per file.
- **US‑04:** As a user, I filter by tag/description keywords to find files without opening them.
- **US‑05:** As a user, I fix low‑confidence items via per‑page High‑Accuracy OCR and re‑classify.
- **US‑06:** As a user, I keep everything in a portable root and export results to CSV/JSON.
- **US‑07:** As a user, I want errors to explain the cause and provide one‑click next steps.

---

## 4) Non‑Functional Requirements (NFRs)
- **Portability:** All app state under one root; relative paths enforced.
- **Privacy:** Offline by default; no network unless cloud toggle is on.
- **Performance:** UI responsive during runs; incremental updates to lists and counts.
- **Reliability:** Crash‑safe queue state; resumable after restart.
- **Observability:** Live activity log with timings and model versions.
- **Accessibility:** Keyboard navigation for queue and table; legible fonts; high contrast option.

---

## 5) Information Architecture & Navigation
- **Main areas:** Home/Run · Files/Queue · Review · Classify · Results · Tags & Descriptions · Activity · Settings
- **Global elements:** Watched Folders sidebar, Status bar (folder, preset, filters, Unanalysed count), Search (FTS)

---

## 6) UX Spec (Screens, States, Interactions)
**Home/Run**
- Sidebar: Watched folders (toggle, preset badge, filters). Inventory pills show counts (matching filters by default; hover → in‑folder totals). Actions: Scan Now, Refresh Inventory, Edit.
- Center: Tabs → Files (read‑only list) and Queue (reorderable). Row actions: Enqueue/Remove, Skip, Retry.
- Right: Run config (Preset selector, OCR mode Fast/High‑Acc, Cloud toggle, Start button). Summary of items.
- Status bar: Folder, Preset, Filters · **Unanalysed N** + type counts (dot color: green/amber/red).

**Review**
- Split view: Page thumbnails + full view | Extracted text (editable). Accept → version the text.

**Classify**
- Tag suggestions (click to accept/edit), two‑sentence description; confidence badge; Save.

**Results**
- Final text, tags, description, metadata; Export CSV/JSON.

**Tags & Descriptions**
- Faceted table: File · Folder · Type · Tags · Description · Confidence · Last Run · Model.
- Left filters: Tag, Folder, Type, Confidence, Date range, Model. Global search (FTS5 on descriptions; optional on extracted text). Bulk actions: add/remove/merge tags, re‑classify, export.

**Activity**
- Live step log per item; timings; model versions; errors with suggested fixes.

**Settings**
- Paths/Portability · Watched Folders · Inventory · Presets · Models (Tesseract/Ollama/Cloud) · Batch · Search/Indexing · Diagnostics.

---

## 7) Style & Content Guidelines
**Descriptions**
- Exactly two sentences: (1) what it is; (2) what matters.
- ISO dates; mask sensitive tokens; no speculation.

**Tags**
- ≤6; required: `type:*`, `domain:*`; optional: `entity:*`, `date:YYYY-MM`, `status:*`, `sensitivity:*`.
- snake_case, singular; canonical dictionary with aliases.

**Confidence**
- High ≥0.66; Med 0.33–0.65; Low <0.33. File badge = min(type, domain).

(See QA Poster in §24.)

---

## 8) Presets Specification
**Fields**: name, description, version; OCR (mode, languages, psm, oem, retries, preproc_profile), LLM (model_name, params: temp, max_tokens, top_p, timeout_s), classification (label_set?, allow_freeform_labels), review_policy (force_review, thresholds), exports (formats, destination_relpath, append/one_file_per_run), run_behavior (stop_on_error, retry_failed_items).

**Behavior**: Watched folder links to a preset; run‑panel overrides per run. On preset edit, prompt to apply to queued items.

---

## 9) Folder Watching, Inventory & Queue
**Discovery**: Polling scan (interval), recurse on by default, ignore patterns, include_hidden off by default, debounce last‑write.
**Inventory**: Pills per type; counts for matching filters (hover shows in‑folder totals). Status bar shows Unanalysed + counts.
**Queue**: Auto‑enqueue (do not autostart). Start button snapshots current queue; new files wait. Reorder/skip/retry supported.
**Unanalysed**: matching − completed(content_hash) − queued/running; respects debounce.

---

## 10) Processing Pipelines
**OCR Pipeline**: page image → preprocessing (light/heavy) → Tesseract (lang packs, psm/oem) → text blocks → cleaning.
**Review**: user acceptance/versioning of text; per‑page targeted re‑runs.
**Classification**: prompts to Ollama → tags + description + confidence badge (simple); version pinned.

---

## 11) AI & Model Adapters
**Tesseract Runner**: detect presence/version; language packs under portable root; mode toggles fast/high‑accuracy; per‑page retry.
**Ollama Adapter**: localhost API; model select, params; pin `model_name@digest` per run; health checks on startup/run.
**Cloud Adapter (optional)**: identical interface; disabled globally; explicit per‑run toggle; clear data boundary note.

---

## 12) Settings & Configuration Schema (portable)
**Paths**: portable_root (locked), data/, logs/, models/, exports/.
**OCR**: default mode, languages, psm/oem, retries, preproc profile.
**Ollama**: host/port, default model, params, timeouts, catalog refresh.
**Cloud**: global enable (off), API key storage, per‑run toggle behavior text.
**Presets**: global list (see §8).
**Batch**: concurrency=1, retry count, behavior on error.
**Search**: FTS on descriptions (on), FTS on extracted text (off), tokenizer, max query time, maintenance.
**Diagnostics**: environment check buttons; versions and writable path tests.

---

## 13) Data Model & Database Schema (SQLite)
**Tables** (primary fields):
- settings(key, value_json)
- presets(id, name, version, data_json)
- watched_folders(id, rel_path, enabled, preset_id, filters_glob, recurse, include_hidden, debounce_s, ignore_json)
- folder_inventory(folder_id, scanned_at, counts_json, scan_duration_ms)
- queue_items(id, folder_id, source_rel_path, content_hash, status, enqueued_at, started_at, finished_at, last_error)
- jobs(id, queue_item_id, preset_id, preset_version, ocr_mode, cloud_enabled, started_at, finished_at, status)
- files(id, rel_path, content_hash, size_bytes, mtime)
- pages(id, job_id, page_index, status, notes)
- extractions(id, job_id, version, text, cleaned)
- classifications(id, job_id, labels_json, description, confidence_badge, model_name, model_digest, rationale)
- logs(id, job_id, level, message, ts)
- file_metadata(file_id, current_tags_json, current_description, current_confidence_badge, last_run_id, updated_at)
- metadata_history(id, file_id, run_id, edit_type, tags_json, description, confidence_badge, model_name, model_digest, ts)

**Indexes**: queue_items(status), jobs(status), files(rel_path), files(content_hash), extractions(job_id, version), classifications(job_id).

---

## 14) Search & Indexing (FTS5)
**Defaults**: FTS5 on descriptions = ON; on extracted text = OFF.
**Queries**: free text + chips (`tag:`, `folder:`, `type:`, `conf:`, `model:`, `has:description`, `is:untagged`, optional `in:text`).
**Ranking**: tag matches → FTS rank → filename → recency bonus.
**Maintenance**: rebuild/optimize buttons; index size & health in Settings.
**Fallback**: if FTS5 unavailable, degrade to substring search and offer bundled SQLite with FTS.

---

## 15) Logging, Diagnostics & Error Handling
**Logging**: session logs per run; step timings; model versions; stored under logs/ and linked from DB.
**Diagnostics**: one‑click Tesseract check (version, langs), Ollama health, permissions, disk space.
**Errors**: banner + plain‑English cause + 1–3 fixes; expandable raw log/traceback; per‑page retry and Hi‑Acc rerun.

---

## 16) Security, Privacy & Portability
**Local‑first**: no outbound network by default. Cloud requires explicit per‑run toggle.
**Secrets**: API keys stored in portable root; no OS keychain required.
**Relative paths**: enforce; show warnings on absolute paths; optional mirroring.
**Data boundary**: UI note when cloud enabled.

---

## 17) Build, Packaging & Environment
**Runtime**: Python 3.x; PySide6; Tesseract binary + language packs in portable `models/ocr`; Ollama installed locally.
**Packaging**: portable root with launcher; no registry writes; docs in README; QSS theme files.
**Env checks**: first‑run wizard validates Tesseract path/langs, Ollama server, writable dirs.

---

## 18) Test Plan & QA Strategy
**Unit**: hashing, debounce, inventory counts, status bar logic.
**Integration**: folder scanning → queue → run snapshot; per‑page retries; preset overrides.
**System**: golden file set for OCR/classification; offline mode; cloud toggle flow.
**Performance**: large directory scan; long queue processing; UI responsiveness.
**Regression**: seed set re‑run on releases; compare tags/description diffs.

---

## 19) Acceptance Criteria (Go/No‑Go)
- Add folder → inventory pills + Unanalysed count appear within 5s.
- Press Start → processes snapshot only; new files wait; UI stays responsive.
- Files table shows tags, two‑sentence description, confidence, model without opening file.
- Search finds items via description (FTS). Optional body search when enabled.
- Errors propose actionable next steps.
- All storage stays under portable root.

---

## 20) Release Checklist
- [ ] Diagnostics all green (Tesseract, languages, Ollama, permissions, disk).
- [ ] Preset defaults loaded; tag dictionary seeded.
- [ ] FTS5 description index built.
- [ ] Golden set passes confidence targets; manual review rate acceptable.
- [ ] README with setup steps; privacy note for cloud toggle.

---

## 21) Maintenance, Updates & Versioning
- **App**: manual updates; migration scripts minimal.
- **Models**: manual approval; versions pinned; changelog visible.
- **Lang packs**: add/remove under models/ocr; record versions per run.
- **Index**: rebuild on demand; routine optimize monthly for heavy use.

---

## 22) Risks & Mitigations
- **OCR quality variance** → High‑Acc path, per‑page retries, upscaling guidance.
- **Large folders** → incremental inventory, collapse subtypes, back‑pressure.
- **FTS not present** → bundle FTS SQLite; degrade gracefully.
- **User edits drift** → metadata history, tag dictionary governance, merges.

---

## 23) Roadmap (Phased)

### Phase P0 - Foundation (✅ COMPLETE)
**Objective:** Establish portable infrastructure, settings system, and diagnostic capabilities.

**Deliverables:**
- ✅ Portable root directory structure (19 directories)
- ✅ Settings system with ConfigManager and Settings Dialog UI
  - 6 tabs: OCR, LLM, Interface, Batch Processing, Search, Paths
  - 40+ configurable options with validation
  - Green status message feedback (non-intrusive UX)
- ✅ Database schema with SQLite + FTS5
  - 8 core tables + 2 FTS5 virtual tables
  - 15 performance indexes
  - Full-text search on descriptions
- ✅ Diagnostics service (9 health checks)
  - Python environment, Tesseract, Ollama connectivity
  - Database integrity, FTS5 availability
  - Disk space, permissions checks
- ✅ Dark theme system (580-line QSS)
  - VS Code Dark+ inspired color scheme
  - Comprehensive widget styling
  - SVG icon integration

**Status:** Complete as of 2025-10-12

---

### Phase P1 - Core Processing Pipeline (🎉 80% COMPLETE)
**Objective:** Implement Watch → Queue → Start → Review → Classify → Results workflow.

**Completed Deliverables:**
- ✅ **Folder watching system** (255 lines)
  - Monitor configured directories for new files
  - Inventory tracking by file type (30+ supported extensions)
  - Unanalyzed file count display
  - Real-time updates with QFileSystemWatcher
  
- ✅ **Queue management service** (330 lines)
  - Drag-and-drop reordering capability
  - Manual enqueue/dequeue operations
  - Batch operations (add/remove multiple)
  - Priority-based processing
  - Status tracking per item
  
- ✅ **OCR engine integration** (310 lines)
  - Tesseract adapter with Fast baseline mode
  - High-accuracy option with preprocessing
  - Multi-language support
  - PDF multi-page processing
  - Confidence scoring
  
- ✅ **LLM engine integration** (280 lines)
  - Ollama local LLM adapter
  - Model selection and validation
  - Classification prompt (generates 6 tags)
  - Description prompt (generates 2 sentences)
  - Response parsing and validation
  
- ✅ **Processing orchestrator** (450 lines)
  - Full pipeline coordination
  - Pause/Resume/Stop controls
  - Hash-based deduplication (SHA-256)
  - Retry logic for failed items
  - Confidence-based review triggers
  - Progress tracking and statistics
  
- ✅ **Review/Classification UI** (380 lines)
  - Split-panel layout (OCR text | Classification)
  - Multi-page PDF navigation
  - Tag editor with validation (6 required)
  - Description editor (exactly 2 sentences)
  - Live confidence indicators
  - Approve/Reject/Skip workflow

**Pending Deliverables:**
- ⏳ Main Window integration (add Watch/Queue/Processing tabs)
- ⏳ Results storage (database writes, FTS5 index updates)

**Total Code:** ~2,000 lines across 6 new files  
**Priority:** In Progress (6-10 hours remaining)

---

### Phase P2 - Search & Export
**Objective:** Tags & Descriptions browser, FTS descriptions, exports, bulk tag ops.

**Deliverables:**
- [ ] Tags & Descriptions browser
  - Searchable results grid
  - Tag filtering and facets
  - Description full-text search (FTS5)
- [ ] Export functionality
  - CSV, JSON, Excel formats
  - Filtered export options
  - Batch tag operations
- [ ] Search enhancements
  - Advanced query syntax
  - Search history
  - Saved searches

**Priority:** Post-P1

---

### Phase P3 - Polish & Refinement
**Objective:** High-Acc OCR path, per-page reruns, confidence tuning, error UX.

**Deliverables:**
- [ ] High-accuracy OCR pipeline
- [ ] Per-page retry mechanism
- [ ] Confidence score tuning
- [ ] Enhanced error UX with actionable fixes
- [ ] Performance optimizations

**Priority:** Post-P2

---

### Phase P4 - Optional Enhancements
**Objective:** Cloud adapter, model suggestions, enhanced inventory performance.

**Deliverables:**
- [ ] Cloud LLM adapter (OpenAI, Anthropic)
- [ ] Model recommendation system
- [ ] Inventory performance scaling (10k+ files)
- [ ] Advanced caching strategies

**Priority:** Optional, post-v1.0

---

## 24) Seed Artifacts
**Tag Dictionary (seed):**
- Types: invoice, receipt, contract, id_card, statement, letter, form, report, spec, resume
- Domains: finance, legal, ops, hr, sales, support, healthcare, engineering
- Status: draft, signed, unpaid, paid, rejected
- Sensitivity: pii, phi, confidential, public
- Aliases: bill→invoice, agreement→contract, cv→resume

**Preset (default):**
- OCR: fast, languages=["eng"], psm:auto, oem:auto, retries=1, preproc=light
- LLM: model_name: (your Ollama default), temp=0.2, max_tokens: fit for 2‑sentence output
- Review policy: force_review=always; thresholds 0.33/0.66
- Exports: csv+json to exports/
- Run: stop_on_error=false; retry_failed_items=1

**QA Poster:** included earlier; pin near workstation.


---

# Additions & Amendments (Post‑Review)

## A1) First‑Run & Onboarding (amends §17)
- **Wizard steps:**
  1) Verify writable **portable root** and subpaths.
  2) Locate **Tesseract** (path + version) and **language packs**; offer to install missing packs locally.
  3) Check **Ollama** reachability (`GET /api/tags`), show models; allow selecting a default.
  4) **FTS5** availability check; if missing, offer bundled SQLite with FTS.
  5) Create a **sample preset** and a **sample folder** (`samples/`) with 3 test files.
  6) Optional: process the sample folder end‑to‑end.
- **Success criteria:** no red banners; sample run completes; description index built.
- **Troubleshooting exits:** show error codes + one‑click fixes (see A4).

## A2) Prompt Library & Invariants (amends §11)
- **Templates:** classification and two‑sentence description prompts under `config/prompts/`; versioned (e.g., `v1.0`).
- **Invariants:** exactly two sentences; no speculation; ISO dates; mask sensitive tokens; ≤6 tags including required `type:*` and `domain:*`.
- **Pinning:** record `prompts_version` with `model_name@digest` per run.
- **Governance:** edits require version bump; older versions remain for reproducibility.

## A3) Cloud Boundary & PII Policy (amends §16)
- **When cloud is ON**, the app may send: description/classification prompts and **extracted text snippets** necessary for classification. It never sends original binary files.
- **Masking rules:** account/ID numbers masked to last 4; emails/usernames left as is; SSNs fully masked unless required by preset (default: forbid).
- **PII‑aware mode (optional):** force masking, disable cloud, highlight sensitive tags.
- **Audit:** log a payload summary (sizes, fields) for each cloud call in the run log.

## A4) Error Code Catalog (amends §15)
Short codes mapped to human messages + suggested fixes:
- `OCR_NO_LANG` – Missing language pack → install pack or switch to English.
- `OLLAMA_UNREACHABLE` – Local LLM down → start Ollama or change host/port.
- `PDF_ENCRYPTED` – Password protected → mark skipped with reason.
- `DISK_RO` – Portable root not writable → choose a writable location.
- `HASH_FAIL` – File read/lock error → retry after debounce; skip if locked.
Each code links to one‑click actions where possible.

## A5) Performance Budgets (amends §14)
- Inventory update < **2s** for 5k files (cached, incremental).
- Description search median < **500ms** for 10k rows (FTS5 indexed).
- Initial description index build: ≤ **5 min** for 10k items on typical hardware; backgrounded.
- Table virtualization kicks in > **1k** rows; pagination > **10k** rows.

## A6) Import/Export & Housekeeping (amends §12)
- **Import/Export:** presets, watched folders, tag dictionary, search/index settings.
- **Housekeeping:** cache eviction (size/time), log rotation, artifact retention, index vacuum. `Clean now` button applies rules immediately.

## A7) Backup & Restore (amends §16)
- **Backup includes:** `data/app.db`, `config/`, `presets`, `tags.yml`, `logs/` (optional), `fts indexes` (optional).
- **Restore flow:** copy backup into new portable root → first‑run check updates relative paths → rebuild indexes on demand.

## A8) Windows Specifics & Edge Cases (amends §21)
- Long path support (enable if needed), antivirus exclusions for portable root, file locks during active scans, symlinks/junctions behavior, case sensitivity notes.

## A9) Diagnostics Bundle (amends §15)
- Generate a redacted **support bundle**: configs, versions, env checks, last N logs, failing job summaries, index health.

## A10) File Handling Matrix (Appendix)
| Type | Extensions | Parse Method | Limits | Special Cases | Fallback |
|---|---|---|---|---|---|
| PDF | .pdf | PDF render → images → Tesseract | Large page counts supported; per‑page retry | Encrypted → `PDF_ENCRYPTED` | Skip with reason |
| Images | .png .jpg .jpeg .tif .tiff .bmp .gif .webp .heic | Direct → Tesseract | HEIC requires codec; TIFF multipage | Low DPI → suggest upscale | Retry with High‑Acc |
| Office | .doc .docx .xls .xlsx .ppt .pptx .rtf .odt .ods .odp | (v1) metadata only or skip | N/A | Future adapter slot | Skip |
| Text | .txt .md .csv .tsv .json .xml .yaml .yml | Direct read (no OCR) | N/A | CSV/JSON summarized | Process inline |
| Archives | .zip .7z .rar .tar .gz .tar.gz | Count only | N/A | Not processed v1 | N/A |

*Notes:* “Open” = read bytes; never launch external apps.

## A11) Keyboard Shortcuts & Accessibility (Appendix)
- `/` focus search · `Enter` run search · `Esc` clear
- `Ctrl+N` add watched folder · `F5` refresh inventory
- `Space` enqueue/dequeue selection · `Ctrl+↑/↓` reorder queue
- `S` Start run · `P` pause · `R` retry
- High‑contrast theme toggle; focus outlines visible; minimum 44px hit targets.

## A12) I18N & Theming Stubs (Appendix)
- **I18N:** separate UI strings file; OCR languages independent from UI; font fallback for CJK.
- **Theming/DPI:** light/dark themes; base font scaling; DPI‑aware icons.

## A13) Compliance Modes & API Surface (Appendix)
- **PII‑aware mode:** force masking; disable cloud; warn on sensitive tags.
- **Local API (future, off by default):** minimal CLI/HTTP endpoints to enqueue files, list results, export.

## A14) Schema Amendments (amends §13)
- Add fields: `queue_items.error_code`, `jobs.error_code`, `jobs.prompts_version`, `files.file_capabilities_json`, `pages.error_code`, `classifications.pii_flag`, `classifications.redaction_summary`.

## A15) Acceptance & Edge Tests (amends §18)
- Encrypted PDF → `PDF_ENCRYPTED`; Unanalysed decremented only if ignored/handled.
- 5k files → Inventory <2s; description search <500ms; table virtualizes.
- Cloud ON → payload log shows masked fields; Cloud OFF → zero outbound.
- PII‑aware mode → masking enforced; confidence unchanged; rationale stored but hidden.
- Restore on new machine/path → identical results & search; indexes rebuild cleanly.



---

## 25) Starter Pack (Files to ship in the portable root)

> These are ready-to-edit seed artifacts so first-run works out of the box.

### 25.1 `config/tags.yml` (seed dictionary)
```yaml
# Canonical tags (expand as you go). Keep names snake_case and singular.
canonical:
  types: [invoice, receipt, contract, id_card, statement, letter, form, report, spec, resume]
  domains: [finance, legal, ops, hr, sales, support, healthcare, engineering]
  status: [draft, signed, unpaid, paid, rejected]
  sensitivity: [pii, phi, confidential, public]

# Common aliases mapped to canonical targets.
aliases:
  bill: invoice
  agreement: contract
  cv: resume
  statement_of_account: statement
  payslip: statement

# Optional descriptions for in-app help (shown on hover in Tag Dictionary UI)
descriptions:
  invoice: "Commercial request for payment; typically includes date, parties, line items, and totals."
  statement: "Periodic account summary; may include balances and transactions."
  id_card: "Government or company-issued identification containing PII."

# Deprecated tags are retained for history but hidden from suggestions.
deprecated: []
```

### 25.2 `config/presets/default_preset.json` (baseline)
```json
{
  "name": "Default",
  "description": "Fast OCR + concise descriptions; review always on.",
  "version": 1,
  "ocr": {
    "mode": "fast",
    "languages": ["eng"],
    "psm": "auto",
    "oem": "auto",
    "retries": 1,
    "preproc_profile": "light"
  },
  "llm": {
    "provider": "ollama",
    "model_name": "<set-your-default-model>",
    "params": {"temperature": 0.2, "max_tokens": 220, "top_p": 0.9},
    "timeout_s": 30
  },
  "classification": {
    "label_set": null,
    "allow_freeform_labels": true
  },
  "review_policy": {
    "force_review": "always",
    "confidence_thresholds": {"low": 0.33, "high": 0.66}
  },
  "exports": {
    "formats": ["csv", "json"],
    "destination_relpath": "exports/",
    "append_to_rolling": false,
    "one_file_per_run": true
  },
  "run_behavior": {
    "stop_on_error": false,
    "retry_failed_items": 1
  }
}
```

### 25.3 `samples/` folder (for first-run demo)
```
samples/
  invoices/
    2025-01_acme_invoice.pdf           # Clean invoice (3 pages)
  letters/
    2024-11_offer_letter.png           # Photo of a printed letter
  ids/
    sample_id_card.jpg                  # Simulated ID (blurred numbers)
```
**Expected outcomes (for QA):**
- **2025-01_acme_invoice.pdf** → tags: `invoice, finance, entity:acme_corp, date:2025-01` ; description: 2 sentences with amount + due date; **confidence: High**.
- **2024-11_offer_letter.png** → tags: `letter, hr` ; description: sender/recipient + offer date; **confidence: Med** if OCR slightly noisy.
- **sample_id_card.jpg** → tags: `id_card, sensitivity:pii` ; description mentions masked ID; **confidence: Med/High** depending on clarity; cloud toggle **off** by default.

**Preset link suggestion:** link `samples/` as a watched folder with `Default` preset; filters `*.pdf;*.png;*.jpg`.

### 25.4 `config/error_codes.yml` (seed)
```yaml
OCR_NO_LANG:
  message: "Required OCR language pack is missing."
  fixes: ["Install language pack", "Switch to English", "Re-run in High-Accuracy"]
OLLAMA_UNREACHABLE:
  message: "Local LLM not reachable at configured host/port."
  fixes: ["Start Ollama", "Check host/port", "Use cloud (if enabled)"]
PDF_ENCRYPTED:
  message: "PDF is password-protected and cannot be processed."
  fixes: ["Skip file", "Provide password (future)"]
DISK_RO:
  message: "Portable root is not writable."
  fixes: ["Choose writable location", "Check permissions/free space"]
HASH_FAIL:
  message: "File could not be hashed (locked or changing)."
  fixes: ["Retry after debounce", "Skip if locked"]
```

### 25.5 `config/onboarding.md` (script for the first-run wizard)
- Validate portable root is writable.
- Locate Tesseract; prompt to install/add language packs (store under `models/ocr/lang/`).
- Check Ollama health; list local models; let the user set default.
- Build **description FTS index**.
- Offer to process `samples/` end-to-end (Start button); show success checklist.

### 25.6 Backup/Restore notes (drop-in README block)
- **Backup:** zip `data/app.db`, `config/`, `presets/`, `tags.yml`, `logs/` (optional), `fts_indexes/` (optional).
- **Restore:** unzip into a new portable root; run app; accept path update prompts; rebuild indexes if prompted.

### 25.7 Housekeeping defaults (Settings → Maintenance)
- Cache eviction: 7 days or 1 GB, whichever first.
- Log rotation: 10 files × 5 MB.
- Artifact retention: keep finals; remove temp intermediates immediately.
- Monthly `VACUUM`/optimize toggle for heavy use.

---

## 26) API & Integration Specification

### 26.1 Command-Line Interface (CLI)
The app supports minimal CLI operations for automation workflows when UI is not needed.

**Commands:**
```powershell
# Scan a folder and enqueue items
previewless-insight.exe scan --folder "S:\Documents" --preset "Default"

# Start processing current queue
previewless-insight.exe run --no-ui --preset "Default"

# Export results
previewless-insight.exe export --format csv --output "S:\exports\results.csv"

# Query results
previewless-insight.exe query --tag "invoice" --confidence high --format json

# Check diagnostics
previewless-insight.exe diagnose --output "diagnostics.txt"
```

**Behaviors:**
- `--no-ui` runs headless (logs to console + file)
- Exit codes: 0 = success, 1 = errors but completed, 2 = fatal error
- All paths relative to portable root unless absolute specified

### 26.2 Local HTTP API (Optional, Disabled by Default)
**Purpose:** Allow other local tools to integrate without sharing the DB directly.

**Endpoints:**
- `GET /api/health` → status, versions, queue count
- `POST /api/enqueue` → add files to queue (body: `{paths: [...], preset: "Default"}`)
- `GET /api/results?tag=invoice&limit=100` → query results
- `POST /api/export` → trigger export job
- `GET /api/tags` → list all tags with usage counts

**Security:**
- Localhost-only binding (127.0.0.1)
- API token required (generated in Settings)
- CORS disabled
- Rate limiting: 100 req/min
- Disabled by default; must be enabled in Settings → Advanced

### 26.3 Webhook Support (Future)
Trigger external workflows on events:
- `run.completed` → POST results summary to configured URL
- `file.classified` → real-time notification per file
- `error.occurred` → alerts for monitoring systems

---

## 27) Advanced Features & Power User Tools

### 27.1 Batch Operations
**Tags & Descriptions View → Bulk Actions:**
- **Merge tags:** Select multiple files → merge `entity:acme` + `entity:acme_corp` → `entity:acme_corp`
- **Split tags:** Separate overly broad tags into specific ones
- **Find & replace:** Regex-based tag/description editing with preview
- **Bulk re-classify:** Queue selected files with new preset
- **Cascade edits:** Update tag → prompt to update similar files

### 27.2 Custom Scripts & Hooks
**Hook points:**
- `pre_ocr.py` → modify image before Tesseract (e.g., custom deskew)
- `post_ocr.py` → clean/transform extracted text
- `pre_classify.py` → inject context or override prompts
- `post_classify.py` → validate/transform tags
- `on_complete.py` → custom exports, notifications

**Location:** `config/hooks/`; must follow defined signatures; errors logged but don't halt processing.

### 27.3 Tag Dictionary Governance
**Features:**
- **Approval workflow:** Proposed tags require approval before canonical
- **Usage analytics:** Show tag frequency, co-occurrence patterns
- **Deprecation:** Mark old tags, suggest replacements, auto-migrate on re-classify
- **Import/Export:** Share dictionaries across instances (YAML format)
- **Version control:** Track dictionary changes with timestamps and reasons

### 27.4 Advanced Search Operators
Beyond basic FTS:
- **Proximity:** `"invoice payment"~5` (words within 5 tokens)
- **Wildcards:** `cont*` matches contract, contractor, etc.
- **Boolean:** `invoice AND (unpaid OR overdue)`
- **Field-specific:** `description:urgent` vs `text:urgent`
- **Date ranges:** `date:[2024-01 TO 2024-12]`
- **Confidence ranges:** `confidence:[0.5 TO 1.0]`
- **Model version:** `model:llama3.2@abc123`
- **Negation:** `-tag:personal` (exclude files tagged personal)

### 27.5 Workspace Profiles
**Use case:** Separate work contexts (e.g., Finance, Legal, Personal) within one portable root.

**Features:**
- Each profile has isolated watched folders, presets, tag dictionaries
- Share or isolate the same files across profiles
- Quick profile switching in UI
- Profile-specific exports and search scopes

---

## 28) Performance Optimization Guide

### 28.1 Hardware Recommendations
**Minimum:**
- CPU: 4 cores (2.0+ GHz)
- RAM: 8 GB
- Storage: SSD with 10 GB free

**Recommended:**
- CPU: 8+ cores (3.0+ GHz) for concurrent processing
- RAM: 16 GB (allows larger batch sizes)
- Storage: NVMe SSD with 50+ GB free
- GPU: Optional; Tesseract and Ollama can leverage if available

### 28.2 Tuning Parameters
**OCR Performance:**
- Use `fast` mode for clean scans
- Enable `high_accuracy` only for problem pages
- Reduce `psm` (Page Segmentation Mode) for uniform layouts
- Limit concurrent threads to CPU core count

**LLM Performance:**
- Use smaller models for classification (3B–8B parameters sufficient)
- Increase `max_tokens` cautiously (impacts latency)
- Batch requests when Ollama supports it (future)
- Keep temperature low (0.2) for consistent outputs

**Database:**
- Run `VACUUM` monthly on databases >1 GB
- Enable WAL mode for concurrent reads
- Index pruning: remove indexes on rarely-queried fields

**File System:**
- Place portable root on fastest disk
- Exclude from antivirus real-time scanning (Windows Defender)
- Use junction points/symlinks for network folders (local cache)

### 28.3 Concurrency Strategy
- **OCR:** 1 file at a time (default); 2-4 for fast scans on multi-core
- **Classification:** Serial by default (LLM bottleneck)
- **Inventory scans:** Background thread, low priority
- **Index updates:** Deferred batch inserts every 50 items

### 28.4 Large-Scale Scenarios
**10k+ files:**
- Enable pagination (1k rows per page)
- Use filters to narrow working set
- Schedule overnight batch runs
- Monitor memory usage (set max batch size in Settings)

**100k+ files:**
- Consider folder sharding (multiple watched folders)
- Use external database (SQLite limits at ~1TB, but performance degrades)
- Enable aggressive caching
- Offload old/archived files to separate portable root

---

## 29) Troubleshooting & FAQ

### 29.1 Common Issues

**Q: Inventory shows 0 files despite folder containing PDFs**
- Check filters: ensure `*.pdf` included in glob pattern
- Verify `recurse` is enabled if files are in subdirectories
- Check `include_hidden` setting
- Look for error in Activity log (permissions issue)

**Q: "Ollama unreachable" error**
- Ensure Ollama is running: `ollama serve` in terminal
- Check host/port in Settings (default: `http://localhost:11434`)
- Verify firewall isn't blocking localhost connections
- Restart Ollama service

**Q: OCR produces gibberish**
- Try `high_accuracy` mode
- Check if correct language pack is installed
- Verify image DPI ≥300 (use upscaling if needed)
- Inspect image preprocessing (try `heavy` profile)

**Q: Descriptions are generic/unhelpful**
- Review extracted text quality (OCR issue?)
- Try different LLM model (larger = more nuanced)
- Adjust temperature (lower = more conservative)
- Check prompt version (update if stale)

**Q: Search returns no results**
- Verify FTS index is built (Settings → Search → Rebuild)
- Check search syntax (simple words work best initially)
- Try searching `in:text` if body search enabled
- Look for typos or exact matches when wildcard needed

**Q: App slow with large queues**
- Reduce batch size in Settings
- Close other apps to free RAM
- Check disk I/O (is antivirus scanning?)
- Process in smaller batches

**Q: Portable root not portable (absolute paths leaked)**
- Run path validation in Settings → Diagnostics
- Check legacy imports (may have absolute paths)
- Use `Fix Paths` tool to convert to relative
- Verify symlinks resolve within portable root

### 29.2 Debug Mode
Enable in Settings → Advanced → Debug Mode:
- Verbose logging (all SQL queries, API calls)
- Timing breakdowns per pipeline stage
- Memory usage tracking
- Raw LLM prompts/responses logged
- No output truncation

**Warning:** Debug logs can be large; disable after troubleshooting.

### 29.3 Support Bundle
Generate via Settings → Diagnostics → Create Support Bundle:
- Includes: configs (redacted secrets), versions, diagnostics output, last 50 log entries, failing job summaries, index health
- Excludes: actual files, extracted text, DB content
- Share this bundle when requesting help

---

## 30) Glossary & Terminology

| Term | Definition |
|------|------------|
| **Portable Root** | Top-level directory containing all app data; self-contained and movable |
| **Watched Folder** | Directory monitored for new/changed files; linked to a preset |
| **Inventory** | Cached count of files by type within a watched folder |
| **Queue** | Ordered list of files to process in next run |
| **Unanalysed** | Files in watched folders not yet processed (or changed since last run) |
| **Queue Snapshot** | Frozen list of files at the moment Start is pressed; new files wait for next run |
| **Preset** | Named configuration bundle (OCR + LLM + review + export settings) |
| **Content Hash** | SHA-256 of file bytes; used to detect changes |
| **Debounce** | Wait period after last file write before considering it ready to process |
| **Page** | Single image or PDF page; unit of OCR processing |
| **Extraction** | OCR-derived text; versioned (original, cleaned, user-edited) |
| **Classification** | AI-generated tags + description + confidence |
| **Confidence Badge** | High/Med/Low; minimum of type and domain confidence scores |
| **Tag** | Structured metadata label (e.g., `type:invoice`, `entity:acme`) |
| **Canonical Tag** | Approved tag in dictionary; others are aliases or freeform |
| **Description** | Two-sentence summary: (1) what it is, (2) what matters |
| **FTS** | Full-Text Search (SQLite FTS5); indexes descriptions and optionally extracted text |
| **Model Digest** | Hash of AI model weights; ensures reproducibility |
| **Prompts Version** | Versioned prompt templates for classification |
| **Cloud Toggle** | Per-run switch to allow network calls to cloud LLMs |
| **PII** | Personally Identifiable Information; triggers masking/warnings |
| **Review** | Human verification step; can edit extracted text before classification |
| **High-Accuracy OCR** | Slower, more thorough OCR mode; for problem pages |
| **Run** | Single processing session from Start to completion |
| **Job** | Processing of one file within a run |
| **Activity Log** | Real-time log of processing steps, timings, errors |
| **Metadata History** | Audit trail of tag/description changes per file |
| **Tag Dictionary** | Master list of canonical tags, aliases, descriptions |
| **Preset Override** | Temporary change to preset settings for one run only |
| **Portable** | All paths relative; no registry writes; movable between machines |

---

## 31) Development Guidelines

### 31.1 Code Organization
```
src/
  main.py                  # Entry point, app initialization
  ui/
    main_window.py         # PySide6 main window
    screens/               # Individual screen modules
      home.py, queue.py, review.py, classify.py, results.py, tags.py, activity.py, settings.py
    components/            # Reusable widgets
      folder_sidebar.py, inventory_pills.py, status_bar.py, search_bar.py, error_banner.py
  core/
    config.py              # Settings management, portable paths
    database.py            # SQLite wrapper, schema migrations
    queue_manager.py       # Queue operations, snapshot logic
    inventory.py           # Folder scanning, file discovery
  engines/
    ocr/
      tesseract_runner.py  # OCR pipeline
      preprocessing.py     # Image cleanup
    llm/
      ollama_adapter.py    # Local LLM
      cloud_adapter.py     # Cloud LLM (optional)
      prompt_manager.py    # Template loading, versioning
    classifier.py          # Tag extraction, confidence scoring
  services/
    search.py              # FTS indexing, query parsing
    export.py              # CSV/JSON generation
    diagnostics.py         # Health checks
  models/
    file.py, page.py, extraction.py, classification.py, job.py, preset.py
  utils/
    hashing.py, debounce.py, path_utils.py, logging_utils.py
  tests/
    unit/, integration/, system/
config/
  tags.yml, error_codes.yml, onboarding.md
  presets/, prompts/
data/
  app.db
logs/
models/
  ocr/lang/                # Tesseract language packs
exports/
samples/
```

### 31.2 Coding Standards
- **Python:** PEP 8 style; type hints for public functions
- **Imports:** Group stdlib, third-party, local; sorted alphabetically
- **Docstrings:** Google style for modules, classes, public methods
- **Error handling:** Catch specific exceptions; log with context; user-facing errors via error codes
- **Tests:** Minimum 70% coverage; golden file tests for OCR/classification

### 31.3 Git Workflow
- **Branches:** `main` (stable), `develop` (integration), `feature/*`, `bugfix/*`, `hotfix/*`
- **Commits:** Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.)
- **PRs:** Require review, passing tests, no merge conflicts
- **Tags:** Semantic versioning (`v1.0.0`, `v1.1.0-beta.1`)

### 31.4 Dependency Management
- **Requirements:**
  - `requirements.txt` (production)
  - `requirements-dev.txt` (testing, linting)
- **Pinning:** Major.minor pinned; patch flexible
- **Updates:** Monthly security audit; quarterly feature updates
- **Bundled:** Include wheels for Windows-specific binaries if needed

### 31.5 UI/UX Principles
- **Responsiveness:** Never block UI >100ms; show progress for >1s operations
- **Feedback:** Immediate visual confirmation for all actions
- **Reversibility:** Support undo for destructive operations
- **Progressive disclosure:** Hide advanced options by default
- **Consistency:** Same patterns for similar operations across screens

### 31.6 Security Practices
- **Input validation:** Sanitize all user inputs (paths, queries, prompts)
- **SQL injection:** Use parameterized queries exclusively
- **Path traversal:** Validate all paths resolve within portable root
- **Secrets:** Never log API keys; redact in debug output
- **Dependencies:** Regular CVE scans

---

## 32) Migration & Upgrade Path

### 32.1 Version Migration Strategy
**Database Schema Changes:**
- Migrations stored in `migrations/` with sequential numbering
- Each migration: `up.sql` (apply) and `down.sql` (rollback)
- Applied automatically on app start; version tracked in `settings` table
- User prompted before breaking changes

**Preset Format Changes:**
- Old presets remain readable
- New fields added with defaults
- Deprecated fields shown with warnings
- Manual upgrade wizard for major changes

**Tag Dictionary Evolution:**
- Additive changes (new canonical tags) are automatic
- Aliases can be bulk-converted to canonical
- Deprecated tags highlighted; suggest replacements
- Export old dictionary before upgrades

### 32.2 Backward Compatibility
**Supported:**
- Read files processed by previous versions
- Search historical results
- Export legacy data

**Not Supported:**
- Downgrade (newer DB schema → older app version)
- Mixing portable roots from different major versions

### 32.3 Upgrade Checklist
- [ ] Backup portable root before upgrade
- [ ] Review changelog for breaking changes
- [ ] Run `diagnose` in old version; save report
- [ ] Install new version in separate folder (test first)
- [ ] Copy portable root to test location
- [ ] Run new version against test root
- [ ] Verify: inventory counts match, searches work, sample file reprocesses identically
- [ ] If satisfied, run new version against production root
- [ ] Rebuild FTS indexes if prompted
- [ ] Check for deprecated settings/presets

---

## 33) Licensing & Legal

### 33.1 App License
- **License:** MIT License (permissive open source)
- **Copyright:** © 2025 [Your Name/Organization]
- **Grants:** Use, copy, modify, merge, publish, distribute, sublicense, sell
- **Conditions:** Include copyright notice and license in distributions
- **Warranty:** Provided "as is" without warranty

### 33.2 Third-Party Dependencies
**Key Components:**
- **PySide6:** LGPL 3.0 (UI framework)
- **Tesseract OCR:** Apache 2.0 (OCR engine)
- **SQLite:** Public domain (database)
- **Ollama:** MIT License (LLM runtime)
- Language packs: Apache 2.0 (Tesseract trained data)

**Compliance:**
- Maintain `THIRD_PARTY_LICENSES.txt` in portable root
- Display license info in Settings → About
- Include source links where required

### 33.3 Data & Privacy Terms
**User Data:**
- All data stored locally by default
- No telemetry without explicit opt-in
- Cloud mode requires user acknowledgment of data transmission
- User owns all generated tags, descriptions, metadata

**Disclaimer:**
- App is a tool; accuracy depends on source quality and model capabilities
- Users responsible for validating AI-generated outputs
- Not intended for life-critical, legal, or medical decision-making without human review

---

## 34) Future Enhancements (Post-v1)

### 34.1 Short-Term (v1.1–v1.3)
- **Enhanced file support:** Basic Office doc text extraction (no OCR)
- **Batch export scheduling:** Automatic daily/weekly exports
- **Template presets:** Industry-specific tag sets (medical, legal, finance)
- **Improved error recovery:** Auto-retry with exponential backoff
- **Multi-language UI:** Spanish, French, German translations

### 34.2 Mid-Term (v2.0)
- **Archive processing:** Extract and process files within ZIP/7Z/TAR
- **OCR quality prediction:** Pre-scan to recommend fast vs high-accuracy
- **Smart folder suggestions:** AI recommends new watched folders based on patterns
- **Collaboration prep:** Export/import share format (sans binaries)
- **Plugin system:** Third-party OCR/LLM/classification engines

### 34.3 Long-Term (v3.0+)
- **Multi-user sync:** Optional server-based DB with conflict resolution
- **Mobile companion:** View results on phone; queue files for processing
- **Advanced analytics:** Trend analysis, entity relationship graphs
- **Custom model training:** Fine-tune classification on user's data
- **Blockchain verification:** Immutable audit trail for compliance (opt-in)

### 34.4 Community Requests
*(Track in GitHub Issues)*
- Bulk file renaming based on tags
- Email attachment auto-ingestion
- Integration with cloud storage (Dropbox, OneDrive)
- Voice dictation for manual tagging
- Augmented reality preview (webcam → instant classification)

---

## 35) Acknowledgments & References

### 35.1 Inspirations
- **Paperless-ngx:** Document management workflows
- **TagSpaces:** Local-first tagging paradigm
- **Obsidian:** Portable, user-owned data
- **DevonThink:** AI-assisted organization
- **Calibre:** Metadata management UX patterns

### 35.2 Technical References
- **Tesseract OCR Documentation:** https://tesseract-ocr.github.io/
- **Ollama API Docs:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **SQLite FTS5:** https://www.sqlite.org/fts5.html
- **PySide6 Docs:** https://doc.qt.io/qtforpython-6/
- **Conventional Commits:** https://www.conventionalcommits.org/

### 35.3 Contributors
*(To be populated)*
- Lead Developer: [Name]
- UX Design: [Name]
- QA: [Name]
- Documentation: [Name]

### 35.4 Feedback & Contact
- **Issues:** [GitHub repo URL]/issues
- **Discussions:** [GitHub repo URL]/discussions
- **Email:** support@example.com
- **Discord/Forum:** [Community link]

---

## 36) Changelog

### v1.0.0 (Initial Release) - [Target Date]
**Features:**
- Portable root with full offline operation
- Watched folders with inventory and unanalysed tracking
- Queue management with manual start, reordering, skip/retry
- Fast and high-accuracy OCR modes (Tesseract)
- Local LLM classification via Ollama
- Tag dictionary with canonical tags and aliases
- Two-sentence descriptions with confidence scoring
- FTS5 search on descriptions
- Tags & Descriptions browser with filters
- CSV/JSON exports
- Activity log with error codes and suggested fixes
- Diagnostics and first-run wizard
- Sample files and presets

**Known Issues:**
- Archive files (.zip, .7z) counted but not processed
- Office docs (.docx, .xlsx) metadata-only
- Cloud adapter interface present but requires manual API key setup
- Large queues (>5k items) may impact UI responsiveness

### v0.9.0 (Beta) - [Date]
- Core pipeline functional
- UI mockups implemented
- Testing on golden file set
- Performance tuning ongoing

### v0.5.0 (Alpha) - [Date]
- Proof of concept
- Basic OCR + classification
- SQLite schema finalized

---

## Appendix A: Complete Settings Reference

*(Detailed expansion of §12 with every setting, default value, constraints, and UI location)*

**Paths & Portability**
- `portable_root`: (locked after init; shown read-only)
- `data_dir`: `data/` (relative, not editable)
- `logs_dir`: `logs/` (relative, not editable)
- `models_dir`: `models/` (relative, not editable)
- `exports_dir`: `exports/` (editable, relative)

**OCR Defaults**
- `default_mode`: `fast` | `high_accuracy` (default: `fast`)
- `languages`: array (default: `["eng"]`)
- `psm`: `auto` | 0–13 (default: `auto`)
- `oem`: `auto` | 0–3 (default: `auto`)
- `retries`: 0–5 (default: 1)
- `preproc_profile`: `light` | `heavy` (default: `light`)

**Ollama**
- `host`: URL (default: `http://localhost:11434`)
- `default_model`: string (user must set or select from catalog)
- `temperature`: 0.0–2.0 (default: 0.2)
- `max_tokens`: 50–2000 (default: 220)
- `top_p`: 0.0–1.0 (default: 0.9)
- `timeout_s`: 10–120 (default: 30)
- `catalog_refresh_interval`: minutes (default: 60)

**Cloud (Optional)**
- `enabled_globally`: boolean (default: `false`)
- `api_key`: string (stored in `config/secrets.json`, not in main settings)
- `provider`: `openai` | `anthropic` | `custom` (default: none)
- `per_run_toggle_text`: string (default: "Send extracted text to cloud for classification?")

**Presets**
- `presets`: array of preset objects (see §8, §25.2)

**Batch**
- `concurrency`: 1–8 (default: 1)
- `max_retry_count`: 0–5 (default: 1)
- `stop_on_error`: boolean (default: `false`)

**Search & Indexing**
- `fts_descriptions_enabled`: boolean (default: `true`)
- `fts_text_enabled`: boolean (default: `false`)
- `fts_tokenizer`: `unicode61` | `porter` (default: `unicode61`)
- `max_query_time_ms`: 1000–10000 (default: 3000)
- `auto_optimize_interval`: `never` | `daily` | `weekly` | `monthly` (default: `monthly`)

**Diagnostics**
- `debug_mode`: boolean (default: `false`)
- `verbose_logging`: boolean (default: `false`)
- `log_rotation_files`: 1–50 (default: 10)
- `log_rotation_size_mb`: 1–50 (default: 5)

**UI/UX**
- `theme`: `light` | `dark` | `auto` (default: `auto`)
- `font_scale`: 0.8–2.0 (default: 1.0)
- `high_contrast`: boolean (default: `false`)
- `table_page_size`: 100–10000 (default: 1000)

**Housekeeping**
- `cache_eviction_days`: 1–30 (default: 7)
- `cache_eviction_size_gb`: 0.1–10 (default: 1)
- `artifact_retention`: `finals_only` | `all` (default: `finals_only`)
- `vacuum_auto`: boolean (default: `false`)

---

## Appendix B: Error Code Quick Reference

*(Expansion of A4 and §25.4)*

| Code | Category | Severity | Message | Primary Fix | Secondary Fix |
|------|----------|----------|---------|-------------|---------------|
| `OCR_NO_LANG` | OCR | Error | Required language pack missing | Install pack | Use English |
| `OCR_TIMEOUT` | OCR | Error | OCR took too long | Increase timeout | Split large file |
| `OLLAMA_UNREACHABLE` | LLM | Error | Cannot connect to Ollama | Start Ollama | Check host/port |
| `OLLAMA_MODEL_404` | LLM | Error | Model not found | Pull model | Select different |
| `CLOUD_API_KEY` | Cloud | Error | API key missing/invalid | Enter key in Settings | Disable cloud |
| `CLOUD_RATE_LIMIT` | Cloud | Warning | Rate limit hit | Wait and retry | Use local LLM |
| `PDF_ENCRYPTED` | File | Warning | Password-protected PDF | Skip file | (Future: enter password) |
| `PDF_CORRUPT` | File | Error | PDF structure invalid | Skip file | Try repair tool |
| `IMG_UNREADABLE` | File | Error | Image codec missing | Install codec | Convert format |
| `DISK_RO` | System | Error | Portable root read-only | Choose writable location | Check permissions |
| `DISK_FULL` | System | Error | Out of disk space | Free space | Change exports path |
| `HASH_FAIL` | File | Warning | File locked or changing | Wait and retry | Skip if persistent |
| `DB_LOCKED` | Database | Error | SQLite locked | Wait and retry | Close other instances |
| `DB_CORRUPT` | Database | Critical | Database integrity check failed | Restore from backup | Rebuild (data loss) |
| `FTS_UNAVAIL` | Search | Warning | FTS5 not available | Use bundled SQLite | Degrade to substring |
| `PRESET_INVALID` | Config | Error | Preset schema validation failed | Fix preset JSON | Use Default preset |

---

## Appendix C: Sample Workflows

### C.1 First-Time Setup (Step-by-Step)
1. Download portable package; extract to `S:\PreviewlessInsight`
2. Run `previewless-insight.exe`
3. First-run wizard:
   - Confirm portable root writable ✓
   - Detect Tesseract at `C:\Program Files\Tesseract-OCR\tesseract.exe` ✓
   - Check language packs: English ✓, Spanish ✗ → "Install Spanish?" → Yes
   - Check Ollama: running ✓, models: `llama3.2:3b` → set as default ✓
   - Build description FTS index ✓
   - Process sample files? → Yes → 3 files processed, 3 High confidence ✓
4. Main window opens → Samples folder listed → Ready!

### C.2 Daily Workflow: Process New Invoices
1. Open app → Home screen
2. "Finance/Invoices" folder → **Unanalysed: 12** (status bar)
3. Click "Scan Now" → inventory updates → Files tab shows 12 new PDFs
4. All 12 auto-enqueued → Queue tab shows order
5. Run config: Preset = "Finance", OCR = Fast, Cloud = OFF
6. Click **Start** → Progress bar → Activity log updates
7. 8/12 High confidence, 3 Med, 1 Low
8. Review Low item → page 2 blurry → switch to High-Accuracy → re-run → now Med
9. Accept all → Results tab shows final tags/descriptions
10. Tags & Descriptions browser → search `unpaid` → find 2 invoices
11. Export → CSV to `exports/invoices_2025-10-12.csv`

### C.3 Maintenance: Monthly Cleanup
1. Settings → Maintenance
2. Click "Clean Now" → evicts cache >7 days old, rotates logs
3. Search → Rebuild FTS Index → takes 30s for 5k files
4. Database → VACUUM → shrinks DB by 200 MB
5. Diagnostics → Run All Checks → all green ✓
6. Backup → zip `data/`, `config/`, `presets/` to external drive

### C.4 Advanced: Bulk Tag Merge
1. Tags & Descriptions → filter `tag:entity:acme`
2. Notice tags: `entity:acme`, `entity:acme_corp`, `entity:acme_inc`
3. Select all 45 files with these tags
4. Bulk Actions → Merge Tags → source: `acme, acme_corp, acme_inc` → target: `acme_corp`
5. Preview: 45 files affected → Confirm
6. Tags updated → re-index automatically
7. Tag Dictionary → add aliases: `acme` → `acme_corp`, `acme_inc` → `acme_corp`
8. Future files auto-map to canonical tag

---

## 37) QSS Styling Guide & Theme System

### 37.1 Overview & Philosophy

**Design Principles:**
- **Dark-First Design:** Primary theme is dark with high contrast and reduced eye strain
- **Semantic Colors:** Use meaningful names (`--accent`, `--danger`) not just hex values
- **Consistent Spacing:** 4px base unit (4, 8, 12, 16, 24, 32px)
- **Accessibility:** WCAG 2.1 AA compliant contrast ratios (4.5:1 minimum for text)
- **Performance:** Single consolidated QSS file; avoid per-widget setStyleSheet() where possible
- **Maintainability:** CSS custom properties pattern; organized by component

**Theme Architecture:**
```
config/themes/
  dark.qss           # Primary dark theme (default)
  light.qss          # Light theme variant
  high_contrast.qss  # Accessibility variant
  _variables.qss     # Shared color/size definitions (imported)
```

### 37.2 Color Palette (Dark Theme)

**Foundation Colors:**
```css
/* Background Hierarchy */
--bg-primary: #1E1E1E;        /* Main window background */
--bg-secondary: #252526;      /* Panels, sidebars */
--bg-tertiary: #2D2D30;       /* Input fields, elevated surfaces */
--bg-elevated: #323233;       /* Hover states, cards */
--bg-overlay: #3E3E42;        /* Modals, dialogs */

/* Text Colors */
--text-primary: #CCCCCC;      /* Main text (contrast 11.7:1) */
--text-secondary: #9E9E9E;    /* Labels, secondary info */
--text-tertiary: #6E6E6E;     /* Disabled, hints */
--text-inverse: #1E1E1E;      /* Text on accent backgrounds */

/* Accent & Semantic Colors */
--accent-primary: #007ACC;    /* Primary actions, links (VS Code blue) */
--accent-hover: #1C97EA;      /* Accent hover state */
--accent-pressed: #005A9E;    /* Accent pressed state */

--success: #89D185;           /* High confidence, success states */
--warning: #D7BA7D;           /* Medium confidence, warnings */
--danger: #F48771;            /* Low confidence, errors */
--info: #75BEFF;              /* Info badges, neutral highlights */

/* Borders & Separators */
--border-primary: #3E3E42;    /* Panel dividers */
--border-secondary: #2D2D30;  /* Subtle separators */
--border-focus: #007ACC;      /* Focus indicators */
--border-error: #F48771;      /* Error states */

/* Status Colors (for inventory pills) */
--status-green: #89D185;      /* All files processed */
--status-amber: #D7BA7D;      /* Some unprocessed */
--status-red: #F48771;        /* Many unprocessed */

/* Shadows & Overlays */
--shadow-sm: rgba(0, 0, 0, 0.2);
--shadow-md: rgba(0, 0, 0, 0.3);
--shadow-lg: rgba(0, 0, 0, 0.5);
--overlay-dim: rgba(0, 0, 0, 0.6);
```

**Color Usage Guidelines:**
- **High Contrast Required:** Text on `--bg-primary` must use `--text-primary` (never `--text-secondary`)
- **Semantic Consistency:** Always use `--success` for High confidence, `--warning` for Med, `--danger` for Low
- **Focus Indicators:** 2px solid `--border-focus` with 2px transparent outline for keyboard navigation
- **Hover Feedback:** Lighten background by one step in hierarchy (e.g., `--bg-secondary` → `--bg-tertiary`)

### 37.3 Typography System

```css
/* Font Stack */
--font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
--font-mono: "Cascadia Code", "Consolas", "Monaco", "Courier New", monospace;

/* Font Sizes (base 10pt = 1rem) */
--font-xs: 9pt;      /* Metadata, timestamps */
--font-sm: 10pt;     /* Body text, table cells */
--font-base: 11pt;   /* Default UI text */
--font-lg: 13pt;     /* Subheadings, emphasis */
--font-xl: 16pt;     /* Section titles */
--font-xxl: 20pt;    /* Screen titles */

/* Font Weights */
--font-regular: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--line-tight: 1.2;   /* Headings */
--line-normal: 1.5;  /* Body text */
--line-relaxed: 1.7; /* Long-form content */
```

**Scaling:**
- User-configurable font scale: 0.8–2.0× (Settings → UI/UX → `font_scale`)
- All sizes multiply by scale factor
- Maintain minimum 44px touch targets regardless of scale

### 37.4 Spacing & Layout

```css
/* Spacing Scale (4px base unit) */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 12px;
--space-lg: 16px;
--space-xl: 24px;
--space-xxl: 32px;
--space-xxxl: 48px;

/* Component Dimensions */
--input-height: 32px;
--button-height: 32px;
--toolbar-height: 40px;
--statusbar-height: 24px;
--sidebar-width: 240px;
--panel-min-width: 200px;

/* Border Radius */
--radius-sm: 3px;   /* Buttons, inputs */
--radius-md: 4px;   /* Cards, panels */
--radius-lg: 8px;   /* Modals, images */
--radius-full: 9999px; /* Pills, badges */
```

### 37.5 Master QSS File (dark.qss)

```css
/* =================================================================
   PREVIEWLESS INSIGHT VIEWER - DARK THEME
   Version: 1.0.0
   Based on: VS Code Dark+ theme
   ================================================================= */

/* -----------------------------------------------------------------
   GLOBAL DEFAULTS
   ----------------------------------------------------------------- */
* {
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt;
    selection-background-color: #264F78;
    selection-color: #CCCCCC;
}

QWidget {
    background-color: #1E1E1E;
    color: #CCCCCC;
    border: none;
    outline: none;
}

/* -----------------------------------------------------------------
   MAIN WINDOW & CONTAINERS
   ----------------------------------------------------------------- */
QMainWindow {
    background-color: #1E1E1E;
}

QMainWindow::separator {
    background-color: #2D2D30;
    width: 1px;
    height: 1px;
}

QMainWindow::separator:hover {
    background-color: #3E3E42;
}

/* -----------------------------------------------------------------
   BUTTONS
   ----------------------------------------------------------------- */
QPushButton {
    background-color: #2D2D30;
    color: #CCCCCC;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    padding: 6px 16px;
    min-height: 20px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #323233;
    border-color: #3E3E42;
}

QPushButton:pressed {
    background-color: #252526;
}

QPushButton:disabled {
    background-color: #252526;
    color: #6E6E6E;
    border-color: #2D2D30;
}

QPushButton:focus {
    border: 2px solid #007ACC;
    outline: 2px solid transparent;
}

/* Primary Action Button (Start, Save, etc.) */
QPushButton[primary="true"] {
    background-color: #007ACC;
    color: #FFFFFF;
    border-color: #007ACC;
    font-weight: 600;
}

QPushButton[primary="true"]:hover {
    background-color: #1C97EA;
}

QPushButton[primary="true"]:pressed {
    background-color: #005A9E;
}

/* Danger Button (Delete, Remove, etc.) */
QPushButton[danger="true"] {
    background-color: #2D2D30;
    color: #F48771;
    border-color: #F48771;
}

QPushButton[danger="true"]:hover {
    background-color: #F48771;
    color: #1E1E1E;
}

/* Flat/Ghost Buttons */
QPushButton[flat="true"] {
    background-color: transparent;
    border: none;
    padding: 4px 8px;
}

QPushButton[flat="true"]:hover {
    background-color: #2D2D30;
}

/* -----------------------------------------------------------------
   INPUT FIELDS
   ----------------------------------------------------------------- */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2D2D30;
    color: #CCCCCC;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    padding: 6px 8px;
    selection-background-color: #264F78;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #007ACC;
    padding: 5px 7px; /* Compensate for thicker border */
}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background-color: #252526;
    color: #6E6E6E;
}

QLineEdit[error="true"], QTextEdit[error="true"] {
    border-color: #F48771;
}

/* -----------------------------------------------------------------
   COMBO BOXES & DROPDOWNS
   ----------------------------------------------------------------- */
QComboBox {
    background-color: #2D2D30;
    color: #CCCCCC;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    padding: 5px 8px;
    min-height: 20px;
}

QComboBox:hover {
    background-color: #323233;
}

QComboBox:focus {
    border: 2px solid #007ACC;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(:/icons/chevron-down.svg);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #2D2D30;
    border: 1px solid #3E3E42;
    selection-background-color: #264F78;
    selection-color: #FFFFFF;
    outline: none;
}

/* -----------------------------------------------------------------
   LISTS & TABLES
   ----------------------------------------------------------------- */
QListWidget, QTreeWidget, QTableWidget {
    background-color: #1E1E1E;
    color: #CCCCCC;
    border: 1px solid #2D2D30;
    border-radius: 3px;
    outline: none;
}

QListWidget::item, QTreeWidget::item, QTableWidget::item {
    padding: 8px;
    border: none;
}

QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover {
    background-color: #2D2D30;
}

QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {
    background-color: #264F78;
    color: #FFFFFF;
}

QListWidget::item:selected:!active, QTreeWidget::item:selected:!active, 
QTableWidget::item:selected:!active {
    background-color: #323233;
}

/* Table Headers */
QHeaderView::section {
    background-color: #252526;
    color: #9E9E9E;
    border: none;
    border-right: 1px solid #2D2D30;
    border-bottom: 1px solid #2D2D30;
    padding: 8px;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 9pt;
}

QHeaderView::section:hover {
    background-color: #2D2D30;
}

/* -----------------------------------------------------------------
   TABS
   ----------------------------------------------------------------- */
QTabWidget::pane {
    border: 1px solid #2D2D30;
    background-color: #1E1E1E;
    border-radius: 3px;
    top: -1px; /* Overlap with tab bar */
}

QTabBar::tab {
    background-color: #252526;
    color: #9E9E9E;
    border: 1px solid #2D2D30;
    border-bottom: none;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    padding: 8px 16px;
    min-width: 80px;
    margin-right: 2px;
}

QTabBar::tab:hover {
    background-color: #2D2D30;
    color: #CCCCCC;
}

QTabBar::tab:selected {
    background-color: #1E1E1E;
    color: #FFFFFF;
    font-weight: 600;
    border-bottom: 2px solid #007ACC;
}

QTabBar::tab:!selected {
    margin-top: 2px; /* Makes unselected tabs look recessed */
}

/* -----------------------------------------------------------------
   SCROLLBARS
   ----------------------------------------------------------------- */
QScrollBar:vertical {
    background-color: #1E1E1E;
    width: 14px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #3E3E42;
    border-radius: 7px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4E4E52;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #1E1E1E;
    height: 14px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #3E3E42;
    border-radius: 7px;
    min-width: 30px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4E4E52;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
}

/* -----------------------------------------------------------------
   PROGRESS BARS
   ----------------------------------------------------------------- */
QProgressBar {
    background-color: #252526;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    text-align: center;
    color: #CCCCCC;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #007ACC;
    border-radius: 2px;
}

/* -----------------------------------------------------------------
   CHECK BOXES & RADIO BUTTONS
   ----------------------------------------------------------------- */
QCheckBox, QRadioButton {
    color: #CCCCCC;
    spacing: 8px;
}

QCheckBox:disabled, QRadioButton:disabled {
    color: #6E6E6E;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3E3E42;
    background-color: #2D2D30;
    border-radius: 3px;
}

QRadioButton::indicator {
    border-radius: 9px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #007ACC;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #007ACC;
    border-color: #007ACC;
    image: url(:/icons/check.svg);
}

QRadioButton::indicator:checked {
    image: url(:/icons/radio-dot.svg);
}

QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {
    background-color: #252526;
    border-color: #2D2D30;
}

/* -----------------------------------------------------------------
   SLIDERS
   ----------------------------------------------------------------- */
QSlider::groove:horizontal {
    background-color: #2D2D30;
    height: 4px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background-color: #007ACC;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #1C97EA;
}

/* -----------------------------------------------------------------
   SPIN BOXES
   ----------------------------------------------------------------- */
QSpinBox, QDoubleSpinBox {
    background-color: #2D2D30;
    color: #CCCCCC;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    padding: 4px 8px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: transparent;
    border: none;
    width: 16px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #323233;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: url(:/icons/chevron-up.svg);
    width: 10px;
    height: 10px;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: transparent;
    border: none;
    width: 16px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #323233;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: url(:/icons/chevron-down.svg);
    width: 10px;
    height: 10px;
}

/* -----------------------------------------------------------------
   TOOL TIPS
   ----------------------------------------------------------------- */
QToolTip {
    background-color: #252526;
    color: #CCCCCC;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    padding: 6px 8px;
    font-size: 10pt;
}

/* -----------------------------------------------------------------
   MENU BAR & MENUS
   ----------------------------------------------------------------- */
QMenuBar {
    background-color: #252526;
    color: #CCCCCC;
    border-bottom: 1px solid #2D2D30;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 3px;
}

QMenuBar::item:selected {
    background-color: #2D2D30;
}

QMenuBar::item:pressed {
    background-color: #323233;
}

QMenu {
    background-color: #252526;
    color: #CCCCCC;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    padding: 4px;
}

QMenu::item {
    background-color: transparent;
    padding: 8px 24px 8px 12px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #264F78;
}

QMenu::separator {
    height: 1px;
    background-color: #2D2D30;
    margin: 4px 0;
}

QMenu::indicator {
    width: 18px;
    height: 18px;
    margin-left: 6px;
}

/* -----------------------------------------------------------------
   STATUS BAR
   ----------------------------------------------------------------- */
QStatusBar {
    background-color: #007ACC;
    color: #FFFFFF;
    border-top: 1px solid #005A9E;
    font-size: 10pt;
    padding: 2px 8px;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    background-color: transparent;
    color: #FFFFFF;
}

/* -----------------------------------------------------------------
   DOCK WIDGETS & PANELS
   ----------------------------------------------------------------- */
QDockWidget {
    titlebar-close-icon: url(:/icons/close.svg);
    titlebar-normal-icon: url(:/icons/float.svg);
    color: #CCCCCC;
}

QDockWidget::title {
    background-color: #252526;
    padding: 8px;
    border-bottom: 1px solid #2D2D30;
    text-align: left;
    font-weight: 600;
}

QDockWidget::close-button, QDockWidget::float-button {
    background-color: transparent;
    border: none;
    padding: 2px;
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background-color: #3E3E42;
    border-radius: 3px;
}

/* -----------------------------------------------------------------
   SPLITTERS
   ----------------------------------------------------------------- */
QSplitter::handle {
    background-color: #2D2D30;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

QSplitter::handle:hover {
    background-color: #007ACC;
}

/* -----------------------------------------------------------------
   DIALOGS & MESSAGE BOXES
   ----------------------------------------------------------------- */
QDialog {
    background-color: #252526;
    border: 1px solid #3E3E42;
}

QMessageBox {
    background-color: #252526;
}

QMessageBox QLabel {
    color: #CCCCCC;
}

/* -----------------------------------------------------------------
   GROUP BOXES
   ----------------------------------------------------------------- */
QGroupBox {
    color: #CCCCCC;
    border: 1px solid #3E3E42;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #1E1E1E;
    left: 8px;
}

/* -----------------------------------------------------------------
   CUSTOM COMPONENTS (App-Specific)
   ----------------------------------------------------------------- */

/* Inventory Pills */
QPushButton[inventory-pill="true"] {
    background-color: #2D2D30;
    border: 1px solid #3E3E42;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 10pt;
    font-weight: 600;
    min-width: 60px;
}

QPushButton[inventory-pill="true"][status="green"] {
    border-color: #89D185;
    color: #89D185;
}

QPushButton[inventory-pill="true"][status="amber"] {
    border-color: #D7BA7D;
    color: #D7BA7D;
}

QPushButton[inventory-pill="true"][status="red"] {
    border-color: #F48771;
    color: #F48771;
}

/* Confidence Badges */
QLabel[confidence-badge="true"] {
    border-radius: 3px;
    padding: 2px 8px;
    font-size: 9pt;
    font-weight: 600;
    background-color: #2D2D30;
}

QLabel[confidence="high"] {
    background-color: rgba(137, 209, 133, 0.2);
    color: #89D185;
    border: 1px solid #89D185;
}

QLabel[confidence="med"] {
    background-color: rgba(215, 186, 125, 0.2);
    color: #D7BA7D;
    border: 1px solid #D7BA7D;
}

QLabel[confidence="low"] {
    background-color: rgba(244, 135, 113, 0.2);
    color: #F48771;
    border: 1px solid #F48771;
}

/* Tag Chips */
QPushButton[tag-chip="true"] {
    background-color: #264F78;
    color: #75BEFF;
    border: 1px solid #75BEFF;
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 9pt;
    font-weight: 500;
}

QPushButton[tag-chip="true"]:hover {
    background-color: #2D5A8E;
}

/* Error Banners */
QFrame[error-banner="true"] {
    background-color: rgba(244, 135, 113, 0.15);
    border-left: 4px solid #F48771;
    border-radius: 3px;
    padding: 12px;
}

QFrame[warning-banner="true"] {
    background-color: rgba(215, 186, 125, 0.15);
    border-left: 4px solid #D7BA7D;
    border-radius: 3px;
    padding: 12px;
}

QFrame[info-banner="true"] {
    background-color: rgba(117, 190, 255, 0.15);
    border-left: 4px solid #75BEFF;
    border-radius: 3px;
    padding: 12px;
}

/* Activity Log */
QTextEdit[activity-log="true"] {
    background-color: #1E1E1E;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 10pt;
    line-height: 1.5;
}

/* Sidebar */
QFrame[sidebar="true"] {
    background-color: #252526;
    border-right: 1px solid #2D2D30;
}

/* Search Bar */
QLineEdit[search-bar="true"] {
    padding-left: 32px; /* Space for search icon */
    background-image: url(:/icons/search.svg);
    background-repeat: no-repeat;
    background-position: 8px center;
}
```

### 37.6 Implementation Guide

**Loading Themes:**
```python
# main.py or ui/main_window.py
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
import sys

def load_theme(app: QApplication, theme_name: str = "dark") -> bool:
    """Load and apply QSS theme to application.
    
    Args:
        app: QApplication instance
        theme_name: Theme file name without extension (default: "dark")
        
    Returns:
        True if theme loaded successfully, False otherwise
    """
    theme_path = f"config/themes/{theme_name}.qss"
    
    try:
        file = QFile(theme_path)
        if not file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            print(f"Failed to open theme file: {theme_path}")
            return False
            
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        
        app.setStyleSheet(stylesheet)
        return True
        
    except Exception as e:
        print(f"Error loading theme: {e}")
        return False

# Usage
app = QApplication(sys.argv)
load_theme(app, "dark")
```

**Using Custom Properties:**
```python
# Setting properties on widgets for conditional styling
button = QPushButton("Start Processing")
button.setProperty("primary", True)  # Matches QPushButton[primary="true"]

badge = QLabel("High")
badge.setProperty("confidence-badge", True)
badge.setProperty("confidence", "high")

# IMPORTANT: Re-polish widget after setting properties
button.style().unpolish(button)
button.style().polish(button)
```

**Dynamic Theme Switching:**
```python
# settings_frame.py
class SettingsFrame(QWidget):
    def __init__(self):
        super().__init__()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "high_contrast"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
    
    def on_theme_changed(self, theme_name: str):
        app = QApplication.instance()
        if load_theme(app, theme_name):
            # Save to settings
            config = load_config()
            config["ui"]["theme"] = theme_name
            save_config(config)
```

### 37.7 Accessibility Considerations

**High Contrast Variant (high_contrast.qss):**
```css
/* Enhanced contrast for accessibility */
* {
    font-size: 12pt; /* Larger base font */
}

QWidget {
    background-color: #000000; /* Pure black */
    color: #FFFFFF; /* Pure white text */
}

QPushButton {
    border-width: 2px; /* Thicker borders */
}

QPushButton:focus, QLineEdit:focus, QComboBox:focus {
    border: 3px solid #FFFF00; /* Yellow focus indicator */
}

/* Maintain WCAG AAA contrast (7:1) for all text */
```

**Keyboard Navigation:**
- All interactive elements receive visible focus indicators (2px+ border)
- Tab order follows logical reading flow
- Focus rings use high-contrast colors (#FFFF00 in high-contrast mode)
- Minimum 44×44px touch targets for all buttons

**Screen Reader Support:**
- Use semantic HTML-like widget names
- Set `setAccessibleName()` and `setAccessibleDescription()` on custom widgets
- Ensure status changes announced (use `QAccessible.updateAccessibility()`)

### 37.8 Best Practices & Anti-Patterns

**DO:**
✅ Use property selectors for variants (`QPushButton[primary="true"]`)
✅ Group related styles with comments
✅ Test theme with font scaling at 0.8× and 2.0×
✅ Validate contrast ratios with accessibility tools
✅ Keep QSS in external files (not inline with Python)
✅ Use relative units where possible
✅ Test hover/focus/pressed states for all interactive elements
✅ Provide visual feedback within 100ms of interaction

**DON'T:**
❌ Use `!important` (not supported in QSS)
❌ Set styles via `widget.setStyleSheet()` repeatedly (performance hit)
❌ Use absolute pixel values for fonts (use pt for scalability)
❌ Forget disabled states for interactive elements
❌ Use low-contrast colors (<4.5:1 for text)
❌ Rely solely on color to convey information (use icons/text too)
❌ Make clickable elements smaller than 44×44px

### 37.9 Testing & Validation

**Visual Regression Testing:**
```python
# tests/ui/test_themes.py
import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance() or QApplication([])
    load_theme(test_app, "dark")
    return test_app

def test_button_states(app, qtbot):
    """Verify button appearance in all states."""
    button = QPushButton("Test")
    button.setProperty("primary", True)
    button.style().polish(button)
    
    # Capture screenshots in different states
    qtbot.addWidget(button)
    # ... screenshot logic ...
    
def test_contrast_ratios(app):
    """Validate WCAG AA compliance."""
    # Parse QSS, extract color pairs, verify contrast
    # Use: https://github.com/gsnedders/wcag-contrast-ratio
    pass
```

**Manual Checklist:**
- [ ] All screens tested in dark/light/high-contrast themes
- [ ] Hover states visible on all interactive elements
- [ ] Focus indicators visible with keyboard navigation
- [ ] Disabled states visually distinct
- [ ] Text readable at 0.8× and 2.0× font scale
- [ ] No color-bleeding or clipping at panel edges
- [ ] Scrollbars styled and functional
- [ ] Tooltips readable with adequate contrast

### 37.10 Icon System

**Icon Requirements:**
- Format: SVG (scalable, theme-able)
- Colors: Use currentColor for theme compatibility
- Sizes: 16×16 (small), 24×24 (default), 32×32 (large)
- Storage: `config/themes/icons/`

**Icon Naming Convention:**
```
icons/
  chevron-up.svg
  chevron-down.svg
  check.svg
  radio-dot.svg
  search.svg
  close.svg
  float.svg
  error.svg
  warning.svg
  info.svg
  success.svg
```

**SVG Template (theme-aware):**
```xml
<!-- check.svg -->
<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>
```

### 37.11 Performance Optimization

**Lazy Loading:**
- Load theme once at app startup
- Cache parsed QSS in memory
- Avoid per-widget `setStyleSheet()` calls

**Minimize Repaints:**
```python
# Batch property changes
widget.setUpdatesEnabled(False)
widget.setProperty("status", "green")
widget.setProperty("count", 42)
widget.style().unpolish(widget)
widget.style().polish(widget)
widget.setUpdatesEnabled(True)
```

**Avoid Complex Selectors:**
```css
/* SLOW: Deep hierarchy */
QMainWindow > QWidget > QFrame > QPushButton { }

/* FAST: Use properties */
QPushButton[context="sidebar"] { }
```

### 37.12 Theme Maintenance Workflow

**Adding New Colors:**
1. Add to color palette section with semantic name
2. Document use case in comments
3. Update light/high-contrast variants
4. Test contrast ratios
5. Update this documentation

**Modifying Components:**
1. Test in isolation first
2. Verify all states (normal, hover, pressed, disabled, focus)
3. Check keyboard navigation
4. Take before/after screenshots
5. Update changelog

**Version Control:**
- Tag theme versions with app versions
- Document breaking changes in CHANGELOG.md
- Maintain backward compatibility where possible

---

**END OF DOCUMENTATION**


