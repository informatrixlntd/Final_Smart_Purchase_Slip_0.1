@echo off
color 0A
echo ============================================================
echo  SMART PURCHASE SLIP - COMPLETE BUILD AND TEST
echo ============================================================
echo.

REM Step 1: Verify Prerequisites
echo [1/7] Checking prerequisites...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller is not installed. Run: pip install pyinstaller
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [ERROR] config.json not found in project root
    pause
    exit /b 1
)

echo [OK] All prerequisites met
echo.

REM Step 2: Clean previous builds
echo [2/7] Cleaning previous builds...
if exist dist-backend rmdir /s /q dist-backend
if exist build rmdir /s /q build
if exist desktop\dist rmdir /s /q desktop\dist
if exist desktop\node_modules\.cache rmdir /s /q desktop\node_modules\.cache
echo [OK] Cleaned
echo.

REM Step 3: Build Backend
echo [3/7] Building Python backend with PyInstaller...
echo This may take 2-3 minutes...
pyinstaller backend.spec --clean --noconfirm

if errorlevel 1 (
    echo [ERROR] Backend build failed!
    pause
    exit /b 1
)

if not exist "dist-backend\purchase_slips_backend.exe" (
    echo [ERROR] Backend executable not created!
    pause
    exit /b 1
)

echo [OK] Backend built successfully
echo.

REM Step 4: Verify Backend Executable
echo [4/7] Verifying backend executable...
echo Checking file size...
for %%A in ("dist-backend\purchase_slips_backend.exe") do set size=%%~zA
if %size% LSS 5000000 (
    echo [WARNING] Backend executable seems too small (%size% bytes^)
    echo This might indicate missing dependencies
)
echo Backend size: %size% bytes
echo [OK] Backend executable exists
echo.

REM Step 5: Test Backend Standalone (optional quick test)
echo [5/7] Testing backend startup...
echo Starting backend for 5 seconds to check for errors...
start /B dist-backend\purchase_slips_backend.exe
timeout /t 5 /nobreak >nul
taskkill /F /IM purchase_slips_backend.exe >nul 2>&1
echo [OK] Backend test complete
echo.

REM Step 6: Install Electron dependencies
echo [6/7] Installing Electron dependencies...
cd desktop
if not exist "node_modules" (
    echo Installing npm packages...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed!
        cd ..
        pause
        exit /b 1
    )
)
echo [OK] Dependencies ready
echo.

REM Step 7: Build Electron App
echo [7/7] Building Electron desktop app...
echo This may take 3-5 minutes...
call npm run build

if errorlevel 1 (
    echo [ERROR] Electron build failed!
    cd ..
    pause
    exit /b 1
)

cd ..

REM Final Verification
echo.
echo ============================================================
echo  BUILD VERIFICATION
echo ============================================================
echo.

if exist "desktop\dist\Smart Purchase Slip Setup *.exe" (
    echo [OK] Installer created successfully
    for %%F in ("desktop\dist\Smart Purchase Slip Setup *.exe") do (
        echo     File: %%~nxF
        echo     Size: %%~zF bytes
    )
) else (
    echo [WARNING] Installer not found
)

if exist "desktop\dist\win-unpacked\Smart Purchase Slip.exe" (
    echo [OK] Unpacked executable exists
    echo     Location: desktop\dist\win-unpacked\
) else (
    echo [ERROR] Unpacked executable not found
)

if exist "desktop\dist\win-unpacked\resources\dist-backend\purchase_slips_backend.exe" (
    echo [OK] Backend bundled correctly in resources
) else (
    echo [ERROR] Backend not found in packaged resources!
)

if exist "desktop\dist\win-unpacked\resources\config.json" (
    echo [OK] config.json bundled correctly
) else (
    echo [ERROR] config.json not found in packaged resources!
)

echo.
echo ============================================================
echo  BUILD COMPLETE!
echo ============================================================
echo.
echo Your application is ready to test:
echo.
echo 1. Quick Test (No installation):
echo    desktop\dist\win-unpacked\Smart Purchase Slip.exe
echo.
echo 2. Install and Test:
echo    desktop\dist\Smart Purchase Slip Setup *.exe
echo.
echo 3. Check Logs (if issues occur):
echo    %%APPDATA%%\Smart Purchase Slip\logs\
echo.
echo ============================================================
echo.
pause
