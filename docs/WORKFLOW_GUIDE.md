# Complete Workflow Guide - InSite App

**Clear, Step-by-Step Instructions for Using the Application**

---

## 🎯 What Does This App Do?

**Simple Answer:** It takes your PDF/image files, reads the text (OCR), and automatically generates tags and descriptions using AI.

**The Magic:**
1. You point it at a folder of documents
2. It finds all PDFs and images
3. It reads the text from them (OCR with Tesseract)
4. It asks an AI (Ollama) to create 6 tags and a 2-sentence description
5. You review and approve the results
6. Everything is saved to a database
7. You can search and browse all your analyzed files

---

## 📋 Complete Workflow (From Start to Finish)

### STEP 1: First Time Setup (One-Time)

**Before you start, make sure:**
- ✅ Tesseract OCR is installed at `S:\Tesseract-OCR`
- ✅ Ollama is running with at least one model downloaded

**Configure the app:**

1. **Launch the application**
   ```powershell
   python main.py
   ```

2. **Open Settings** (File menu → Settings, or Ctrl+,)

3. **Configure OCR tab:**
   - Tesseract Path: `S:\Tesseract-OCR\tesseract.exe`
   - (Or click Browse to find it)

4. **Configure LLM tab:**
   - Model: Select `llama3.2` from dropdown
   - (Or choose another model you have)

5. **Click Save**

6. **Close Settings**

✅ **Setup complete!** You only do this once.

---

### STEP 2: Add a Folder to Watch

**This tells the app where your documents are.**

1. **Go to the "📁 Watch" tab**

2. **Click "Add Folder"**

3. **Browse to a folder with PDFs or images**
   - Example: `S:\Documents\Invoices`
   - Or: `S:\Scans\Receipts`

4. **Click "Select Folder"**

**What happens:**
- The app scans the folder
- Counts all PDFs and images
- Shows statistics:
  - Total Files: 47
  - By Type: PDF: 23, JPG: 15, PNG: 9
  - Unanalyzed: 47

✅ **Your folder is now being watched!**

---

### STEP 3: Add Files to Queue

**This creates a processing list.**

**Option A: Automatic (Recommended for first time)**
- Just go to Step 4 - files are auto-queued!

**Option B: Manual Selection**

1. **Go to "📋 Queue" tab**

2. **Click "Enqueue Files"**

3. **Select files from file picker**

4. **Files appear in queue table:**
   - File name
   - Type
   - Status: "Pending"
   - Priority: Normal

✅ **Files are queued and ready!**

---

### STEP 4: Start Processing

**This is where the magic happens!**

1. **Go to "⚙️ Processing" tab**

2. **Click "▶ Start Processing"**

**What happens now (automatically):**

```
For each file in queue:
├─ 1. OCR reads the text (Tesseract)
├─ 2. Review dialog pops up
│    ├─ Shows extracted OCR text
│    ├─ Shows AI-generated tags (6)
│    ├─ Shows AI-generated description (2 sentences)
│    └─ You click "✓ Approve" or "✗ Reject"
└─ 3. If approved: Saves to database
```

**You'll see:**
- Processing status: "RUNNING"
- Current file being processed
- Progress bar (2/47 files)
- Statistics updating

**For EACH file, a Review Dialog appears:**

---

### STEP 5: Review Each File (Important!)

**This dialog shows you what the AI found.**

**The Review Dialog has:**

```
┌─────────────────────────────────────────┐
│ Review: invoice_2025-10.pdf             │
├─────────────────────────────────────────┤
│ OCR Text:                               │
│ ┌─────────────────────────────────────┐ │
│ │ INVOICE                             │ │
│ │ ABC Corporation                     │ │
│ │ Invoice #12345                      │ │
│ │ Date: October 15, 2025              │ │
│ │ Total: $5,000                       │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Tags: (editable)                        │
│ invoice, financial, business,           │
│ entity:abc_corp, date:2025-10,          │
│ amount:5000                             │
│                                         │
│ Description: (editable)                 │
│ Invoice from ABC Corporation for        │
│ services rendered. Total amount $5,000. │
│                                         │
│        [✓ Approve]  [✗ Reject]         │
└─────────────────────────────────────────┘
```

**What to do:**

✅ **If it looks good:** Click "✓ Approve"
- File is saved to database
- Next file starts processing

❌ **If it's wrong:** Click "✗ Reject"
- File is marked as failed
- Can retry later
- Next file starts processing

**You can also EDIT:**
- The tags (add/remove/change)
- The description (rewrite if needed)
- Then click Approve to save your changes

---

### STEP 6: Browse Results

**After processing, see all your analyzed files!**

1. **Go to "📊 Results" tab**

2. **See all processed files in a table:**

```
┌────────────────────────────────────────────────────────────┐
│ File Name        │Type│Tags          │Description    │Conf│
├────────────────────────────────────────────────────────────┤
│ invoice_oct.pdf  │PDF │invoice, fin..│ABC Corp inv...│87%│
│ receipt_001.jpg  │JPG │receipt, pur..│Purchase at ...│92%│
│ letter_2025.png  │PNG │letter, corr..│Business let...│78%│
└────────────────────────────────────────────────────────────┘
Total files: 47
```

3. **Click any row to see details**
   - Or double-click
   - Or select and click "View Details"

4. **Details dialog shows:**
   - Complete OCR text from all pages
   - All 6 tags with confidence scores
   - Full description
   - File metadata

✅ **You can now browse and validate everything!**

---

### STEP 7: Search Your Files

**Find documents instantly!**

1. **Stay in "📊 Results" tab**

2. **Type search query in search box:**
   - Example: `invoice`
   - Example: `ABC Company`
   - Example: `payment`

3. **Press Enter or click "🔍 Search"**

4. **See only matching files**
   - Green notification: "Found 12 matching files"

5. **Click "✕ Clear" to see all files again**

**Search Tips:**
- `invoice` - Find all invoices
- `invoice payment` - Either word
- `invoice AND payment` - Both words
- `"ABC Company"` - Exact phrase
- `financial NOT personal` - Exclude word

✅ **Full-text search across ALL your documents!**

---

## 🔄 Visual Workflow Diagram

```
START
  │
  ├─→ 1. SETUP (One-time)
  │    ├─ Configure Tesseract path
  │    ├─ Select Ollama model
  │    └─ Save settings
  │
  ├─→ 2. ADD FOLDER (Watch Tab)
  │    ├─ Click "Add Folder"
  │    ├─ Select folder with PDFs/images
  │    └─ App scans and counts files
  │
  ├─→ 3. QUEUE FILES (Optional - Queue Tab)
  │    ├─ Files auto-queue from watched folders
  │    └─ Or manually enqueue specific files
  │
  ├─→ 4. START PROCESSING (Processing Tab)
  │    ├─ Click "▶ Start Processing"
  │    └─ For each file:
  │         ├─ OCR extracts text (Tesseract)
  │         ├─ AI generates tags + description (Ollama)
  │         ├─ Review dialog appears
  │         ├─ You approve/reject
  │         └─ Saved to database if approved
  │
  ├─→ 5. BROWSE RESULTS (Results Tab)
  │    ├─ See all analyzed files
  │    ├─ View details
  │    └─ Validate analysis
  │
  └─→ 6. SEARCH (Results Tab)
       ├─ Type query
       ├─ FTS5 searches OCR text + tags
       └─ Find documents instantly

END - Your documents are analyzed, tagged, and searchable! 🎉
```

---

## 🎬 Real Example Walkthrough

Let me show you a real scenario:

### Scenario: Processing 20 Invoices

**Goal:** Analyze 20 PDF invoices, tag them, and be able to search them.

**Steps:**

1. **Setup** (if not done)
   - Settings → OCR tab → Tesseract: `S:\Tesseract-OCR\tesseract.exe`
   - Settings → LLM tab → Model: `llama3.2`
   - Save

2. **Add Folder**
   - Watch tab → Add Folder
   - Select: `S:\Documents\Invoices`
   - App shows: "Total Files: 20, Unanalyzed: 20"

3. **Start Processing**
   - Processing tab → "▶ Start Processing"
   - Processing begins...

4. **First file: invoice_001.pdf**
   - OCR runs (2-3 seconds)
   - AI analyzes (3-5 seconds)
   - Review dialog appears:
     ```
     OCR Text:
     "INVOICE
      Acme Corp
      Invoice #A-001
      Date: October 1, 2025
      Amount: $1,250.00"
     
     Tags: invoice, financial, business, entity:acme_corp, 
           date:2025-10, amount:1250
     
     Description: Invoice from Acme Corp for $1,250 
     dated October 1, 2025.
     
     Confidence: High (87%)
     ```
   - Click "✓ Approve"
   - File saved!

5. **Processing continues automatically**
   - Invoice 2 → Review → Approve
   - Invoice 3 → Review → Approve
   - ...
   - Invoice 20 → Review → Approve

6. **Processing Complete!**
   - Green notification: "Processing completed - Processed: 20 | Failed: 0 | Skipped: 0"

7. **Browse Results**
   - Results tab opens
   - Table shows all 20 invoices
   - Each row shows: filename, tags, description, confidence

8. **Search Example**
   - Search: `Acme Corp`
   - Results: 5 invoices from Acme Corp
   - Double-click first one
   - Details dialog shows complete invoice analysis

**Total Time:** ~5-10 minutes for 20 files (including review)

✅ **Done!** All invoices are analyzed, tagged, and searchable!

---

## ❓ Common Confusions Explained

### "What's the difference between Watch tab and Queue tab?"

**Watch Tab:**
- Shows **folders** being monitored
- Displays **inventory** of files in those folders
- Used to ADD/REMOVE watch folders

**Queue Tab:**
- Shows **individual files** ready to process
- Files here are in line for processing
- Used to MANAGE what gets processed and in what order

**Think of it like:**
- Watch = Your bookshelf (all books you own)
- Queue = Books you plan to read this week (specific list)

---

### "Why do I need to approve each file?"

**Validation!** The AI isn't perfect:
- OCR might misread text (poor scan quality)
- AI might generate wrong tags
- You can catch errors before saving

**You can:**
- ✅ Approve good results → Saved
- ✗ Reject bad results → Not saved, can retry later
- ✏️ Edit tags/description → Save your version

**This ensures your database has accurate, human-verified data.**

---

### "What happens after I approve?"

1. File metadata → `files` table
2. OCR text for each page → `pages` table
3. All 6 tags → `classifications` table
4. Description → `descriptions` table
5. Full-text search indexes updated

**Now you can:**
- Browse in Results tab
- Search by any word in OCR text
- Search by tags
- Export to CSV/JSON (coming in P2)

---

### "Do I have to process files one by one?"

**No!** The processing is automatic:
- Click "Start Processing" ONCE
- Review dialog appears for EACH file automatically
- You just click Approve/Reject for each
- Processing continues until queue is empty

**You're just reviewing, not manually processing.**

---

### "What if I want to skip the review step?"

**Currently:** Every file requires review (by design for accuracy)

**Future (P2):** Batch approval feature
- Set confidence threshold (e.g., 90%)
- Auto-approve high-confidence results
- Only review low-confidence items

---

## 🎯 Quick Start for Absolute Beginners

**Never used the app before? Follow this:**

1. **Open app:** `python main.py`

2. **First time only - Settings:**
   - File menu → Settings
   - OCR tab → Browse → Find tesseract.exe
   - LLM tab → Model dropdown → Select llama3.2
   - Save

3. **Add documents:**
   - 📁 Watch tab
   - Add Folder
   - Pick a folder with some PDFs or images
   - Click Select Folder

4. **Process them:**
   - ⚙️ Processing tab
   - Click "▶ Start Processing"
   - Wait for dialog to appear
   - Read what the AI found
   - Click "✓ Approve"
   - Repeat for each file

5. **See results:**
   - 📊 Results tab
   - Browse your analyzed files!

**That's it!** You're done! 🎉

---

## 💡 Pro Tips

### Tip 1: Organize by folders
```
S:\Documents\
  ├─ Invoices\          ← Watch this
  ├─ Receipts\          ← Watch this
  ├─ Contracts\         ← Watch this
  └─ Personal\          ← Don't watch
```
Watch each folder separately for better organization.

### Tip 2: Use the search!
Once processed, search is INSTANT:
- Find all invoices: `invoice`
- Find specific company: `"Acme Corp"`
- Find by date: `2025-10`
- Find by amount: `$1,250`

### Tip 3: Check confidence scores
- Green (≥80%): Trust it
- Yellow (50-79%): Review carefully
- Red (<50%): Probably needs correction

### Tip 4: Edit before approving
You can modify tags and descriptions in the review dialog!
- Add missing tags
- Fix OCR errors in description
- Then approve to save YOUR version

---

## 🚨 Troubleshooting

### "Review dialog never appears"
**Check:**
- Is Tesseract configured? (Settings → OCR)
- Is Ollama running? (Check with `ollama list`)
- Check Processing tab for errors

### "OCR text is gibberish"
**Possible causes:**
- Poor image quality
- Handwritten text (OCR doesn't work well)
- Non-English text (configure language in settings)

**Solution:** Reject and use better scan

### "AI tags are wrong"
**This is normal!** AI isn't perfect.
**Solution:** 
- Edit tags in review dialog
- Or reject and retry with different model

### "Processing is slow"
**Normal speeds:**
- OCR: 2-5 seconds per page
- AI analysis: 3-10 seconds per file
- Review: As fast as you can click

**20 files = ~10-15 minutes** (including your review time)

---

## 📚 Tab-by-Tab Reference

### 📁 Watch Tab
**Purpose:** Manage folders to monitor
**Actions:**
- Add Folder - Browse for folder
- Remove Folder - Delete from watch list
- Refresh - Rescan folders
**Shows:** Total files, by type, unanalyzed count

### 📋 Queue Tab
**Purpose:** Manage processing queue
**Actions:**
- Enqueue Files - Add files to queue
- Remove - Delete from queue
- Clear Queue - Empty entire queue
- Reorder (↑/↓) - Change priority
**Shows:** File list, status, priority

### ⚙️ Processing Tab
**Purpose:** Monitor and control processing
**Actions:**
- ▶ Start - Begin processing queue
- ⏸ Pause - Pause processing
- ⏹ Stop - Stop completely
- 🔄 Retry Failed - Reprocess failed files
**Shows:** Status, current file, progress, statistics

### 📊 Results Tab ✨ NEW!
**Purpose:** Browse and search analyzed files
**Actions:**
- 🔄 Refresh - Reload results
- 🔍 Search - Full-text search
- ✕ Clear - Clear search
- View Details - Show complete analysis
**Shows:** All analyzed files, search results

---

## 🎊 You're Ready!

**You now understand:**
✅ What the app does  
✅ The complete workflow  
✅ How each tab works  
✅ How to process files  
✅ How to search results  
✅ Common issues and solutions  

**Go ahead and process your first document!** 🚀

**Questions?** Check the other docs:
- `RESULTS_BROWSER_IMPLEMENTATION.md` - Search features
- `TESSERACT_INTEGRATION.md` - OCR setup
- `OLLAMA_MODELS.md` - Model information

---

**Remember:** The workflow is simple:
1. Add folder
2. Start processing
3. Approve each file
4. Browse/search results

**That's it!** Everything else is automatic! ✨
