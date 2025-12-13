# Fixing ACCESS_VIOLATION (Exit Code 3221225477 / 0xC0000005)

## Problem Analysis

Your backend is crashing with **ACCESS_VIOLATION (0xC0000005)**, which is a **memory access error**, NOT an encoding error.

### Root Cause
The `mysql-connector-python` package includes **C extensions** that cause crashes when bundled with PyInstaller on Windows. This is a known issue.

## Solutions Implemented

### 1. Force Pure-Python MySQL Connector ✅
We've updated the code to force pure-Python mode (no C extensions):

**Files Modified:**
- `backend/database.py` - Sets `use_pure=True` on all connections
- `backend.spec` - Excludes C extensions and sets environment variable
- `pyi_rth_mysql_pure.py` - Runtime hook to force pure mode
- `backend/app.py` - Added comprehensive error handling and logging

### 2. Better Error Handling ✅
- Wrapped `init_db()` in try-catch to prevent crash
- Added detailed logging at each step
- Backend continues running even if DB init fails (so you can see errors)

### 3. Improved Error Dialogs ✅
- `main.js` now shows actual log contents in error dialogs
- Correctly identifies ACCESS_VIOLATION vs other errors
- Provides specific troubleshooting steps

## Build and Test Instructions

### Step 1: Clean Build
```batch
REM Clean everything first
rmdir /s /q dist-backend build desktop\dist desktop\node_modules\.cache

REM Run the fixed build
./BUILD_AND_TEST.bat
```

### Step 2: Test Minimal Backend (Isolate the Crash)
Before testing the full app, let's verify basic execution works:

```batch
REM Build the minimal test backend
pyinstaller test_backend.spec --clean --noconfirm

REM Test it
dist-test-backend\test_backend.exe
```

**Expected Output:**
- Should print "MINIMAL BACKEND TEST"
- Should show Python version, platform info
- Should import Flask and MySQL connector successfully
- Should run for 10 seconds without crashing
- Should show "TEST COMPLETED SUCCESSFULLY"

**If this crashes:**
- The issue is with PyInstaller setup or missing dependencies
- Install Visual C++ Redistributables: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Check antivirus isn't blocking the executable

**If this works:**
- The basic Python execution is fine
- Proceed to test the full backend

### Step 3: Test Full Backend
```batch
REM Test the full backend executable directly
cd dist-backend
purchase_slips_backend.exe
```

**Expected Output:**
- Should print "SMART PURCHASE SLIP BACKEND - STARTUP"
- Should show detailed startup logs
- Should attempt to connect to MySQL
- Should either:
  - Connect successfully: "Database initialized successfully"
  - Fail gracefully: "Database initialization failed" but keep running
- Should start Flask on http://127.0.0.1:5000

**Check the logs for:**
- MySQL Connector version
- "MySQL Connector pure mode: 1" ← **MUST show this**
- Any import errors
- Database connection errors

### Step 4: Test Full Electron App
```batch
REM Run from win-unpacked
desktop\dist\win-unpacked\"Smart Purchase Slip.exe"

REM Or install and run
desktop\dist\"Smart Purchase Slip Setup *.exe"
```

**Check logs at:**
```
%APPDATA%\smart-purchase-slip\logs\backend-*.log
```

## Troubleshooting

### If Still Crashing with ACCESS_VIOLATION:

#### Option A: Check Dependencies
```batch
REM Install Visual C++ Redistributables
REM Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

#### Option B: Check Antivirus
- Temporarily disable antivirus
- Add exclusion for:
  - `dist-backend\`
  - `desktop\dist\`
  - `%TEMP%\_MEI*\`

#### Option C: Verify Pure-Python Mode
Run the backend and check the logs:
```
[INFO] MySQL Connector pure mode: 1
```
If it shows "not set" or "0", the C extensions are still being used.

#### Option D: Check MySQL Installation
The pure-Python connector still needs MySQL client libraries:
```batch
REM Check if MySQL is accessible
mysql -u root -p -e "SELECT VERSION();"
```

#### Option E: Database Connection Issues
If MySQL is the problem, the backend should now **continue running** with an error message instead of crashing. Check the logs.

### If Backend Starts but Shows Database Errors:

This is progress! The ACCESS_VIOLATION is fixed. Now fix the database issue:

1. **Check config.json:**
   ```json
   {
     "database": {
       "host": "localhost",
       "port": 3306,
       "user": "root",
       "password": "your_password_here",
       "database": "purchase_slips_db"
     }
   }
   ```

2. **Verify MySQL is running:**
   ```batch
   mysql -u root -p -e "SHOW DATABASES;"
   ```

3. **Check MySQL service:**
   - Press `Win + R`, type `services.msc`
   - Find "MySQL" service
   - Ensure it's "Running"

4. **Test connection manually:**
   ```batch
   mysql -u root -p -h localhost -P 3306
   ```

## Expected Results After Fixes

### ✅ Minimal Test Backend:
- Prints startup info
- Imports all modules successfully
- Runs for 10 seconds
- Clean exit

### ✅ Full Backend:
- Prints extensive startup logs
- Shows "pure mode: 1"
- Either connects to DB OR fails gracefully
- Starts Flask on port 5000
- **Does NOT crash with ACCESS_VIOLATION**

### ✅ Electron App:
- Starts backend successfully
- Shows login screen
- Backend logs saved to AppData
- Error dialogs show actual log content (if errors occur)

## What Changed

### Before:
- MySQL connector used C extensions
- Crashed immediately with ACCESS_VIOLATION
- No error messages visible
- Error dialogs showed wrong info ("encoding error")

### After:
- MySQL connector forced to pure-Python mode
- Comprehensive logging at each step
- Graceful error handling
- Error dialogs show actual crash info and logs
- Backend continues running even if DB fails

## Still Having Issues?

1. **Run the minimal test first** - This isolates the problem
2. **Check the log files** - They now contain detailed info
3. **Look for the "pure mode" line** - Must show "1"
4. **Verify Visual C++ Redistributables installed**
5. **Check antivirus logs** - It may be blocking execution
6. **Try running as Administrator** - Some Windows security features block executables

## Additional Resources

- Visual C++ Redistributables: https://aka.ms/vs/17/release/vc_redist.x64.exe
- PyInstaller Windows issues: https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html
- MySQL Connector Pure Mode: https://dev.mysql.com/doc/connector-python/en/connector-python-cext.html
