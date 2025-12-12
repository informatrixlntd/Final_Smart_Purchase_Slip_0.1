# ⚡ Quick Build Reference Card

## 🚀 ONE-COMMAND BUILD

```cmd
BUILD_AND_TEST.bat
```

**This does everything:**
- ✅ Checks prerequisites
- ✅ Cleans old builds
- ✅ Builds Python backend → `dist-backend/purchase_slips_backend.exe`
- ✅ Builds Electron app → `desktop/dist/Smart Purchase Slip Setup.exe`
- ✅ Verifies all files included
- ✅ Shows build report

## 📋 What Was Fixed

| File | Issue | Status |
|------|-------|--------|
| `backend/app.py` | Module imports failed in .exe | ✅ FIXED |
| `backend/database.py` | config.json not found | ✅ FIXED |
| `backend.spec` | Missing modules/data | ✅ FIXED |
| `desktop/main.js` | No error logging | ✅ FIXED |
| `desktop/package.json` | Backend not bundled | ✅ FIXED |

## 🎯 Testing Your Build

### Test 1: Without Installing
```cmd
desktop\dist\win-unpacked\Smart Purchase Slip.exe
```

### Test 2: Full Installation
```cmd
desktop\dist\Smart Purchase Slip Setup *.exe
```

### Test 3: Check Logs (if issues)
```cmd
%APPDATA%\Smart Purchase Slip\logs\
```

## 🐛 Common Issues - Quick Fixes

### "ModuleNotFoundError"
❌ **Old backend.spec** didn't include modules
✅ **NOW FIXED** - All modules in hiddenimports

### "Cannot connect to backend"
🔍 Check: `%APPDATA%\Smart Purchase Slip\logs\backend-*.log`
- If empty → Backend not starting
- If MySQL error → Start XAMPP
- If port error → Close other apps on port 5000

### "Config not found"
✅ **NOW FIXED** - Checks 3 locations:
1. Inside .exe bundle (sys._MEIPASS)
2. Next to .exe (resources/)
3. Defaults

## 📂 Where Everything Is

```
After BUILD_AND_TEST.bat:

dist-backend/
└── purchase_slips_backend.exe  ← Backend (standalone)

desktop/dist/
├── Smart Purchase Slip Setup.exe  ← Installer
└── win-unpacked/
    ├── Smart Purchase Slip.exe  ← Main app
    └── resources/
        ├── dist-backend/
        │   └── purchase_slips_backend.exe  ← Bundled
        └── config.json  ← Bundled
```

## ✅ Build Checklist

Before distributing:

- [ ] Run `BUILD_AND_TEST.bat` → No errors
- [ ] Test without installing → Works
- [ ] Install on test machine → Works
- [ ] Login page appears → No "Cannot connect" error
- [ ] Can login → Backend responding
- [ ] Check logs → No errors

## 🎯 Key Files (All Fixed!)

**backend/app.py** - Lines 7-10
```python
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)
```

**backend/database.py** - Lines 12-17
```python
if getattr(sys, 'frozen', False):
    config_paths.append(os.path.join(sys._MEIPASS, 'config.json'))
```

**backend.spec** - Lines 7, 22-25
```python
pathex=['backend'],
hiddenimports=[..., 'database', 'routes', 'routes.slips', 'routes.auth'],
```

**desktop/main.js** - Lines 268-276
```javascript
const logDir = path.join(app.getPath('userData'), 'logs');
const logStream = fs.createWriteStream(logFile);
```

## 📞 Support

**If backend crashes:**
1. Open: `%APPDATA%\Smart Purchase Slip\logs\backend-*.log`
2. Look for `[STDERR]` lines
3. Common fixes:
   - MySQL not running → Start XAMPP
   - Wrong credentials → Edit config.json
   - Port in use → Close other apps

**If build fails:**
1. Check Python installed: `python --version`
2. Check PyInstaller: `pip install pyinstaller`
3. Check Node.js: `npm --version`
4. Clean rebuild: `REBUILD_FIXED.bat`

---

## 🎉 Ready to Build!

Just run: **`BUILD_AND_TEST.bat`**

Everything is fixed and ready to go! 🚀
