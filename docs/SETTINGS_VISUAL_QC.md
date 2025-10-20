# Settings Dialog Visual QC Test
**Date:** 2025-10-12  
**Component:** Settings Dialog (Tools → Settings)  
**Theme:** Dark Theme  

---

## Quick Visual Tests

### Test 1: Settings Dialog Opening ✅
- [ ] Open application
- [ ] Click **Tools → Settings** (or press `Ctrl+,`)
- [ ] Dialog opens centered
- [ ] All 6 tabs visible at top
- [ ] Dialog size appropriate (600x500 minimum)

### Test 2: Tab Navigation ✅
- [ ] Click each tab: OCR, LLM, Interface, Batch Processing, Search, Paths
- [ ] Active tab clearly highlighted (white text, seamless connection to content)
- [ ] Inactive tabs visually recessed (gray text, darker background)
- [ ] Tab content changes when switching
- [ ] No layout shifts or glitches

### Test 3: OCR Tab Form Controls ✅
**Dropdown (QComboBox):**
- [ ] "Default Mode" dropdown has visible border
- [ ] Arrow icon visible on right
- [ ] Hover changes border to blue
- [ ] Click opens dropdown list
- [ ] List items have hover effect
- [ ] Selection closes dropdown

**Text Input (QLineEdit):**
- [ ] "Languages" field has visible border
- [ ] Placeholder text visible (if empty)
- [ ] Click focuses field (blue border, darker background)
- [ ] Text is readable
- [ ] Can type and edit

**Other Dropdowns:**
- [ ] "Page Segmentation" dropdown styled
- [ ] "OCR Engine Mode" dropdown styled
- [ ] "Preprocessing" dropdown styled

**Numeric Input (QSpinBox):**
- [ ] "Retry Count" spinner has visible border
- [ ] Up/down arrow buttons visible
- [ ] Arrows clickable
- [ ] Can type number directly

### Test 4: LLM Tab Form Controls ✅
**Group Boxes:**
- [ ] "Ollama Configuration" group has title
- [ ] "Cloud LLM (Optional)" group has title
- [ ] Group borders visible
- [ ] Titles positioned above border

**Text Inputs:**
- [ ] "Host URL" field styled
- [ ] "Default Model" field styled
- [ ] Can see placeholder text

**Numeric Inputs:**
- [ ] "Temperature" decimal spinner works
- [ ] "Max Tokens" integer spinner works
- [ ] "Top P" decimal spinner works
- [ ] "Timeout" integer spinner works

**Checkbox:**
- [ ] "Enable cloud LLM fallback" checkbox visible
- [ ] Box has border
- [ ] Clicking toggles checkmark
- [ ] Checkmark appears as blue box with ✓

**Password Field:**
- [ ] "API Key" field shows bullets when typing
- [ ] Field properly styled like other inputs

### Test 5: Interface Tab ✅
**Appearance Group:**
- [ ] "Theme" dropdown (dark/light)
- [ ] "Font Scale" decimal spinner
- [ ] Checkboxes aligned with labels
- [ ] Spacing consistent

**Behavior Group:**
- [ ] Three checkboxes stacked vertically
- [ ] Labels readable
- [ ] Checkboxes toggle independently

### Test 6: Batch Processing Tab ✅
- [ ] All spinboxes styled consistently
- [ ] "Stop on first error" checkbox works
- [ ] Labels aligned properly

### Test 7: Search Tab ✅
- [ ] Checkboxes for FTS options
- [ ] Tokenizer dropdown
- [ ] "Max Query Time" spinner with " ms" suffix

### Test 8: Paths Tab ✅
**Directory Inputs:**
- [ ] Four line edits for paths
- [ ] "Browse..." buttons next to each
- [ ] Buttons properly styled
- [ ] Note text at bottom readable (italic, gray)

**Browse Functionality:**
- [ ] Click "Browse..." opens folder dialog
- [ ] Selected path updates in line edit

### Test 9: Button Box ✅
- [ ] Three buttons at bottom: OK, Cancel, Apply
- [ ] Buttons same size (min 80px width)
- [ ] Proper spacing between buttons
- [ ] Hover effect on buttons
- [ ] Click effects visible

### Test 10: Interaction States ✅
**Hover States:**
- [ ] Input fields border turns blue on hover
- [ ] Buttons lighten on hover
- [ ] Dropdown arrows stay visible on hover
- [ ] Checkboxes border turns blue on hover

**Focus States:**
- [ ] Tab key navigates through controls
- [ ] Focused element has blue 2px border
- [ ] Focus visible from keyboard navigation
- [ ] Enter/Space activates focused button

**Disabled States (if implemented):**
- [ ] Disabled controls grayed out
- [ ] Disabled controls non-interactive

### Test 11: Text Readability ✅
- [ ] All labels readable (light gray on dark)
- [ ] Group box titles stand out (white)
- [ ] Input text readable (light gray)
- [ ] Placeholder text visible but distinct (darker gray)
- [ ] No text overflow or truncation
- [ ] No overlapping text

### Test 12: Visual Consistency ✅
- [ ] All input fields same height
- [ ] Consistent border radius (3px)
- [ ] Consistent spacing (8px)
- [ ] Color scheme matches main window
- [ ] No jarring color transitions

### Test 13: Functionality ✅
**Apply Button:**
- [ ] Click "Apply" saves settings
- [ ] Dialog remains open
- [ ] Success message appears
- [ ] Theme reloads if changed

**OK Button:**
- [ ] Click "OK" saves settings
- [ ] Dialog closes
- [ ] Changes persist

**Cancel Button:**
- [ ] Click "Cancel" discards changes
- [ ] Dialog closes
- [ ] Original values restored

### Test 14: Scroll Behavior ✅
- [ ] If content exceeds dialog height, scroll bars appear
- [ ] Scroll bars styled (dark with rounded handles)
- [ ] Scrolling smooth
- [ ] Mouse wheel works

---

## Expected Visual Results

### Perfect State (All Checks Pass)
```
✓ Dialog opens smoothly
✓ All tabs clearly visible and distinguishable
✓ All input fields have visible borders
✓ Text is crisp and readable
✓ Hover effects work on all interactive elements
✓ Focus states clearly visible
✓ No visual glitches or artifacts
✓ Consistent spacing throughout
✓ Professional, polished appearance
```

### Common Issues to Watch For
- ❌ Text appearing cut off or overlapping
- ❌ Input fields invisible (no borders)
- ❌ Tabs all looking the same (no active state)
- ❌ Arrows missing from dropdowns/spinners
- ❌ Checkboxes using native OS style
- ❌ Group box titles overlapping borders
- ❌ Inconsistent padding/spacing
- ❌ Poor contrast making text hard to read

---

## Screenshot Checklist

Recommended screenshots to capture:

1. **Settings Dialog - OCR Tab**
   - Shows default state with all form controls
   
2. **Settings Dialog - LLM Tab**
   - Shows group boxes and varied input types
   
3. **Settings Dialog - Interface Tab**
   - Shows checkboxes and grouped controls
   
4. **Hover State Example**
   - Input field with blue border on hover
   
5. **Focus State Example**
   - Input field with 2px blue border when focused
   
6. **Dropdown Open**
   - Combo box showing dropdown list
   
7. **Tab Bar**
   - All 6 tabs showing active/inactive states

---

## Sign-Off

**Visual QC Status:** ⏳ **AWAITING USER VERIFICATION**

All automated checks passed. Please verify visually that:
1. Settings dialog text is clear and not distorted
2. All form controls are properly styled
3. Tab navigation works smoothly
4. Colors match the design intent

**Tester:** _________________  
**Date:** _________________  
**Result:** [ ] PASS  [ ] FAIL  
**Notes:** _______________________________________

---

**End of Visual QC Test**
