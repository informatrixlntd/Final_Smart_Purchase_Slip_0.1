# Print Fix - Quick Reference Card

## ✅ What Was Fixed

**Problem:** Print button showed "This app doesn't support print preview" or printed blank pages

**Solution:** Changed from `window.print()` (wrong) → `webContents.print()` via IPC (correct)

## 🔧 Changes Made

| File | Lines | Change |
|------|-------|--------|
| `desktop/main.js` | 206-277 | ✅ Added `print-slip-html` IPC handler |
| `desktop/main.js` | 426 | ✅ Added `ipcRenderer` import |
| `desktop/main.js` | 436-441 | ✅ Fixed `printPDF()` to use IPC |
| `desktop/main.js` | 512-518 | ✅ Fixed Ctrl+P handler |

## 📋 Testing Checklist

```bash
# 1. Restart the app
cd desktop && npm start

# 2. Open a slip and click Print icon
# 3. In the PDF viewer window:
```

- [ ] Click "🖨️ Print" button
- [ ] System print dialog appears (not blank)
- [ ] Preview shows the actual slip content
- [ ] Press Ctrl+P - same result
- [ ] Download PDF still works
- [ ] WhatsApp share still works

## 🔍 Expected Console Logs

**When Print Button Clicked:**
```
🖨️  Print button clicked - sending IPC to print HTML
============================================================
🖨️  PRINTING SLIP HTML - ID: 123
============================================================
📄 Loading slip HTML from: http://localhost:5000/print/123
✅ HTML loaded successfully, initiating print...
✅ Print job sent successfully
🧹 Print window closed
```

## ❌ Troubleshooting

| Issue | Solution |
|-------|----------|
| No print dialog | Check Flask is running on port 5000 |
| Blank preview | Test `http://localhost:5000/print/123` in browser |
| IPC error | Check DevTools console for errors |
| Colors missing | Enable "Background graphics" in print dialog |

## 🎯 Key Points

✅ **DO:** Use `ipcRenderer.send('print-slip-html', slipId)`
❌ **DON'T:** Use `window.print()` from PDF viewer

✅ **DO:** Print the HTML from Flask server
❌ **DON'T:** Try to print from PDF iframe

✅ **DO:** Use `webContents.print()` in main process
❌ **DON'T:** Print from renderer process

## 📞 Quick Test Command

```javascript
// In viewer window DevTools console:
ipcRenderer.send('print-slip-html', 1); // Test with slip ID 1
```

Should immediately show the print dialog with slip preview.

## 🔄 Architecture Flow

```
User clicks Print
    ↓
ipcRenderer.send('print-slip-html', slipId)
    ↓
Main process creates hidden window
    ↓
Loads http://localhost:5000/print/<slipId>
    ↓
webContents.print() with options
    ↓
✅ System print dialog with preview
```

## ✨ Result

**Before:** ❌ Error or blank page
**After:** ✅ Perfect slip printing

---

For detailed documentation, see `PRINT_FIX_COMPLETE.md`
