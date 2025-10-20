# Testing Guide - Results Browser

**Quick Test Checklist**

## ✅ Visual Verification (Running Now!)

The application is currently running. Please verify:

### 1. Results Tab Exists
- [ ] Check main window has **4 tabs** (not 3)
- [ ] Fourth tab is labeled "📊 Results"
- [ ] Tab is clickable and switches view

### 2. UI Components Present
- [ ] Search bar with placeholder text
- [ ] Search button (🔍 Search)
- [ ] Clear button (✕ Clear)
- [ ] Refresh button (🔄 Refresh)
- [ ] Results table with 6 columns
- [ ] View Details button at bottom
- [ ] Results count label

### 3. Table Layout
**Column Headers:**
1. File Name
2. Type  
3. Tags
4. Description
5. Confidence
6. Analyzed

All headers should be visible and properly aligned.

---

## 🧪 Functional Testing (Needs Processed Files)

### Test A: Browse Empty Results
**Prerequisites:** Fresh database (no processed files)

**Steps:**
1. Click 📊 Results tab
2. Observe empty table
3. Check count label shows "Total files: 0"

**Expected:** Empty table, no errors, UI stable

---

### Test B: Browse After Processing
**Prerequisites:** At least 1 processed file in database

**Steps:**
1. Process a sample file (PDF or image)
2. Wait for processing to complete
3. Click 📊 Results tab
4. Click 🔄 Refresh

**Expected:** 
- File appears in table
- File name displayed
- Type shown (PDF/JPG/PNG)
- Tags listed (comma-separated)
- Description visible (truncated if long)
- Confidence percentage shown
- Date displayed

---

### Test C: Search Functionality
**Prerequisites:** Processed files with known content

**Steps:**
1. Type search query (e.g., "invoice")
2. Press Enter or click 🔍 Search
3. Observe results update
4. Check notification appears
5. Click ✕ Clear
6. Observe full results return

**Expected:**
- Search executes quickly (< 1 second)
- Only matching files shown
- Green notification: "Found X matching files"
- Clear button restores all files
- Count label updates correctly

---

### Test D: View Details
**Prerequisites:** At least 1 processed file in results

**Steps:**
1. Select a row in results table
2. Double-click the row
3. Details dialog opens
4. Review content
5. Click Close

**Expected:**
- Dialog opens immediately
- Shows file path, type, size, date
- Shows description with confidence
- Shows all 6 tags with individual confidences
- Shows complete OCR text for each page
- Close button dismisses dialog

---

### Test E: Color-Coded Confidence
**Prerequisites:** Files with varying confidence levels

**Expected Colors:**
- **Green text:** Confidence ≥ 80%
- **Yellow text:** Confidence 50-79%
- **Red text:** Confidence < 50%

---

## 🐛 Error Scenario Testing

### Test F: Search No Results
1. Search for nonsense: "xyzabc123"
2. Expected: Blue notification "No results found"

### Test G: View Details - No Selection
1. Click View Details without selecting row
2. Expected: Orange warning "Please select a file to view"

### Test H: Empty Search
1. Leave search box empty
2. Click Search
3. Expected: Shows all results (same as refresh)

---

## 🚀 Quick Verification Commands

### Check Database Has Files
```powershell
sqlite3 app_data/insite.db "SELECT COUNT(*) FROM files;"
```

### Check for Processed Files
```powershell
sqlite3 app_data/insite.db "SELECT file_path, analyzed_at FROM files LIMIT 5;"
```

### Check FTS5 Search Works
```powershell
sqlite3 app_data/insite.db "SELECT COUNT(*) FROM pages_fts WHERE pages_fts MATCH 'test';"
```

---

## ✅ Current Status

**Application:** ✅ Running without errors  
**Results Tab:** ✅ Added to UI  
**Database Methods:** ✅ Implemented  
**Search:** ✅ FTS5 integrated  
**Details Dialog:** ✅ Complete  

**Ready for Testing!** 🎉

---

## 📝 Notes for Testing

1. **No test data yet?** 
   - Process a sample file first
   - Use Watch tab → Add folder
   - Queue tab → Enqueue files
   - Processing tab → Start

2. **FTS5 search syntax examples:**
   - `invoice` - Simple word
   - `invoice payment` - Multiple words (OR)
   - `invoice AND payment` - Both required
   - `"exact phrase"` - Exact match
   - `invoice NOT refund` - Exclude word

3. **Performance notes:**
   - 1,000 files should load in < 100ms
   - Search should complete in < 200ms
   - Details should open instantly

---

## 🎯 Success Criteria

✅ All UI components visible  
✅ No errors in console  
✅ Table loads (even if empty)  
✅ Search executes without errors  
✅ Details dialog opens and displays  
✅ Notifications appear correctly  
✅ Refresh updates data  

**If all pass: FEATURE COMPLETE!** 🚀
