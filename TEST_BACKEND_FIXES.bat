@echo off
chcp 65001 >nul 2>&1
color 0B

echo ============================================================
echo  BACKEND ACCESS_VIOLATION FIX - TEST SCRIPT
echo ============================================================
echo.
echo This script will help diagnose and fix the backend crash
echo Exit code 3221225477 (0xC0000005 - ACCESS_VIOLATION)
echo.
echo ============================================================
echo.

pause

REM ============================================================
REM Step 1: Check Prerequisites
REM ============================================================
echo [STEP 1/5] Checking prerequisites...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python found:
python --version

pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller not found
    echo Installing PyInstaller...
    pip install pyinstaller
)
echo [OK] PyInstaller found

echo.
echo [IMPORTANT] Checking Visual C++ Redistributables...
echo If you're getting ACCESS_VIOLATION, you may need:
echo   Visual C++ Redistributables 2015-2022 (x64)
echo   Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
echo Press any key to continue (install VC++ Redist first if needed)...
pause >nul
echo.

REM ============================================================
REM Step 2: Clean Previous Builds
REM ============================================================
echo [STEP 2/5] Cleaning previous builds...
echo.

if exist "test-backend" rmdir /s /q "test-backend"
if exist "dist-backend" rmdir /s /q "dist-backend"
if exist "build" rmdir /s /q "build"

echo [OK] Clean complete
echo.

REM ============================================================
REM Step 3: Build Minimal Test Backend
REM ============================================================
echo [STEP 3/5] Building minimal test backend...
echo This tests if basic PyInstaller execution works
echo.

pyinstaller test_backend.spec --clean --noconfirm

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

if not exist "test-backend\test_backend.exe" (
    echo [ERROR] test_backend.exe not created
    pause
    exit /b 1
)

echo [OK] Minimal test backend built
echo.

REM ============================================================
REM Step 4: Test Minimal Backend
REM ============================================================
echo [STEP 4/5] Testing minimal backend...
echo.
echo ============================================================
echo  MINIMAL BACKEND TEST OUTPUT
echo ============================================================
echo.

cd test-backend
test_backend.exe

set TEST_EXIT_CODE=%errorlevel%
cd ..

echo.
echo ============================================================
echo  TEST RESULT
echo ============================================================
echo.

if %TEST_EXIT_CODE% EQU 0 (
    echo [SUCCESS] Minimal backend ran without crashes!
    echo.
    echo This means:
    echo   - PyInstaller bundling works
    echo   - Python execution works
    echo   - Basic modules can be imported
    echo   - No ACCESS_VIOLATION in basic execution
    echo.
    echo You can proceed to test the full backend.
    echo.
) else if %TEST_EXIT_CODE% EQU 3221225477 (
    echo [FAILED] ACCESS_VIOLATION still occurring!
    echo Exit code: %TEST_EXIT_CODE% (0xC0000005)
    echo.
    echo This means:
    echo   - PyInstaller executable crashes on startup
    echo   - Likely missing Visual C++ Redistributables
    echo   - Or antivirus blocking execution
    echo.
    echo SOLUTIONS:
    echo   1. Install Visual C++ Redistributables:
    echo      https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    echo   2. Disable antivirus temporarily and retry
    echo.
    echo   3. Run as Administrator
    echo.
    echo   4. Add exclusions for:
    echo      - %CD%\test-backend\
    echo      - %CD%\dist-backend\
    echo      - %TEMP%\_MEI*\
    echo.
    pause
    exit /b 1
) else (
    echo [WARNING] Unexpected exit code: %TEST_EXIT_CODE%
    echo Check the output above for errors
    echo.
    pause
)

REM ============================================================
REM Step 5: Build Full Backend
REM ============================================================
echo [STEP 5/5] Building full backend with fixes...
echo.

pyinstaller backend.spec --clean --noconfirm --distpath .

if errorlevel 1 (
    echo [ERROR] Backend build failed
    pause
    exit /b 1
)

if not exist "dist-backend\purchase_slips_backend.exe" (
    echo [ERROR] Backend executable not created
    pause
    exit /b 1
)

echo [OK] Full backend built
echo.

REM ============================================================
REM Final Test
REM ============================================================
echo ============================================================
echo  TESTING FULL BACKEND
echo ============================================================
echo.
echo The backend will start and should show detailed logs.
echo.
echo WHAT TO LOOK FOR:
echo   1. "MySQL Connector pure mode: 1" - MUST show this
echo   2. "Database initialized successfully" - Good!
echo   3. "Database initialization failed" - Check MySQL setup
echo   4. Flask starts on http://127.0.0.1:5000
echo.
echo The backend should NOT crash with ACCESS_VIOLATION.
echo.
echo Press any key to start the backend...
pause >nul
echo.

cd dist-backend
start /wait purchase_slips_backend.exe

cd ..

echo.
echo ============================================================
echo  ALL TESTS COMPLETE
echo ============================================================
echo.
echo If the backend ran without ACCESS_VIOLATION:
echo   - The fix is working!
echo   - You can now run BUILD_AND_TEST.bat to build the full app
echo.
echo If you still see ACCESS_VIOLATION:
echo   - Install Visual C++ Redistributables
echo   - Check antivirus
echo   - Run as Administrator
echo   - Review FIXING_ACCESS_VIOLATION.md for more details
echo.
echo Backend logs are at:
echo   %%APPDATA%%\smart-purchase-slip\logs\
echo.
pause
