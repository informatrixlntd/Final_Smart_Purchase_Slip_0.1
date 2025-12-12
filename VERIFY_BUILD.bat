@echo off
color 0B
echo ============================================================
echo  BUILD VERIFICATION TOOL
echo ============================================================
echo.

echo Checking required files for packaging...
echo.

set "ALL_OK=1"

REM Check 1: Backend executable
echo [1/5] Checking backend executable...
if exist "dist-backend\purchase_slips_backend.exe" (
    echo     [OK] Backend executable found
    for %%A in ("dist-backend\purchase_slips_backend.exe") do (
        echo     Size: %%~zA bytes
    )
) else (
    echo     [MISSING] dist-backend\purchase_slips_backend.exe not found
    echo     Run: pyinstaller backend.spec --clean --distpath .
    set "ALL_OK=0"
)
echo.

REM Check 2: Config file
echo [2/5] Checking config.json...
if exist "config.json" (
    echo     [OK] config.json found
) else (
    echo     [MISSING] config.json not found in project root
    set "ALL_OK=0"
)
echo.

REM Check 3: Desktop folder
echo [3/5] Checking desktop files...
if exist "desktop\main.js" (
    echo     [OK] desktop\main.js found
) else (
    echo     [MISSING] desktop\main.js not found
    set "ALL_OK=0"
)

if exist "desktop\package.json" (
    echo     [OK] desktop\package.json found
) else (
    echo     [MISSING] desktop\package.json not found
    set "ALL_OK=0"
)
echo.

REM Check 4: Node modules
echo [4/5] Checking desktop dependencies...
if exist "desktop\node_modules" (
    echo     [OK] node_modules found
) else (
    echo     [MISSING] node_modules not found
    echo     Run: cd desktop ^&^& npm install
    set "ALL_OK=0"
)
echo.

REM Check 5: Electron builder
echo [5/5] Checking electron-builder...
cd desktop
call npm list electron-builder >nul 2>&1
if errorlevel 1 (
    echo     [MISSING] electron-builder not installed
    echo     Run: cd desktop ^&^& npm install
    set "ALL_OK=0"
) else (
    echo     [OK] electron-builder installed
)
cd ..
echo.

echo ============================================================
echo  VERIFICATION RESULT
echo ============================================================
echo.

if "%ALL_OK%"=="1" (
    echo [OK] All files present - Ready to build!
    echo.
    echo Next steps:
    echo   1. Run: BUILD_AND_TEST.bat
    echo   2. Or run: cd desktop ^&^& npm run build
    echo.
) else (
    echo [ERROR] Some files are missing!
    echo.
    echo Fix the issues above, then try again.
    echo.
)

echo ============================================================
echo.

REM Additional diagnostics
echo ADDITIONAL INFORMATION:
echo.
echo Project Root: %CD%
echo.
echo dist-backend contents:
if exist "dist-backend" (
    dir /b "dist-backend" 2>nul
    if errorlevel 1 (
        echo     (folder exists but is empty)
    )
) else (
    echo     (folder does not exist)
)
echo.

pause
