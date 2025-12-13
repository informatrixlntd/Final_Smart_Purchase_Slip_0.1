@echo off
chcp 65001 >nul 2>&1
color 0B

echo ============================================================
echo  REBUILD WITH ALL FIXES
echo ============================================================
echo.
echo FIXES APPLIED:
echo   1. Pure-Python MySQL (no ACCESS_VIOLATION crashes)
echo   2. Frontend files bundled (fixes "Not Found" error)
echo   3. Enhanced error handling and logging
echo.
echo This will rebuild:
echo   - Backend with frontend files
echo   - Full Electron desktop app
echo   - Installer
echo.
echo ============================================================
echo.

pause

echo [STEP 1/3] Cleaning previous builds...
if exist dist-backend rmdir /s /q dist-backend
if exist build rmdir /s /q build
if exist desktop\dist rmdir /s /q desktop\dist
if exist desktop\node_modules\.cache rmdir /s /q desktop\node_modules\.cache
echo [OK] Clean complete
echo.

echo [STEP 2/3] Rebuilding backend with frontend files...
echo.
echo Bundling:
echo   - Pure-Python MySQL connector
echo   - frontend/index.html
echo   - frontend/reports.html
echo   - frontend/static folder
echo.
pyinstaller backend.spec --clean --distpath .

if errorlevel 1 (
    echo [ERROR] Backend build failed!
    pause
    exit /b 1
)

echo [OK] Backend built
echo.

echo [STEP 3/3] Rebuilding Electron desktop app...
echo.
cd desktop
call npm install
call npm run build

if errorlevel 1 (
    echo [ERROR] Electron build failed!
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ============================================================
echo  BUILD COMPLETE!
echo ============================================================
echo.
echo Built files:
echo   Backend: dist-backend\purchase_slips_backend.exe
echo   App: desktop\dist\win-unpacked\Smart Purchase Slip.exe
echo   Installer: desktop\dist\Smart Purchase Slip Setup *.exe
echo.
echo TESTING:
echo   1. Run the installer OR
echo   2. Run: desktop\dist\win-unpacked\"Smart Purchase Slip.exe"
echo   3. Login and click "Create New Slip"
echo   4. Form should load without "Not Found" error
echo.
pause
