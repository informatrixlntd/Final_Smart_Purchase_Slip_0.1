@echo off
chcp 65001 >nul 2>&1
color 0A

echo ============================================================
echo  SMART PURCHASE SLIP - BUILD SYSTEM
echo  Fixed Build Process for Backend Stability
echo ============================================================
echo.

REM ============================================================
REM Step 1: Prerequisites Check
REM ============================================================
echo [1/8] Checking prerequisites...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [OK] Python found
python --version

pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller not installed
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo [OK] PyInstaller found
pyinstaller --version

if not exist "config.json" (
    echo [ERROR] config.json not found in project root
    echo Please ensure config.json exists before building
    pause
    exit /b 1
)

echo [OK] config.json found
echo [OK] All prerequisites met
echo.

REM ============================================================
REM Step 2: Install/Verify Python Dependencies
REM ============================================================
echo [2/8] Verifying Python dependencies...

if exist "requirements.txt" (
    echo Installing/Updating Python packages...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [WARNING] Some packages failed to install
        echo Build will continue but may fail...
    ) else (
        echo [OK] All Python dependencies installed
    )
) else (
    echo [WARNING] requirements.txt not found
)
echo.

REM ============================================================
REM Step 3: Clean Previous Builds
REM ============================================================
echo [3/8] Cleaning previous builds...

if exist "dist-backend" (
    echo Removing old dist-backend...
    rmdir /s /q "dist-backend" 2>nul
)

if exist "build" (
    echo Removing old build folder...
    rmdir /s /q "build" 2>nul
)

if exist "desktop\dist" (
    echo Removing old Electron builds...
    rmdir /s /q "desktop\dist" 2>nul
)

if exist "desktop\node_modules\.cache" (
    rmdir /s /q "desktop\node_modules\.cache" 2>nul
)

REM Clean PyInstaller cache
if exist "%USERPROFILE%\.pyinstaller" (
    echo Cleaning PyInstaller cache...
    rmdir /s /q "%USERPROFILE%\.pyinstaller" 2>nul
)

echo [OK] Clean complete
echo.

REM ============================================================
REM Step 4: Build Python Backend with PyInstaller
REM ============================================================
echo [4/8] Building Python backend executable...
echo This may take 2-5 minutes depending on your system...
echo.

REM Set environment for better build
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

REM Build with PyInstaller
pyinstaller backend.spec --clean --noconfirm --distpath .

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    echo.
    echo Common solutions:
    echo 1. Check if all dependencies are installed: pip install -r requirements.txt
    echo 2. Verify backend.spec file is not corrupted
    echo 3. Check Python version compatibility
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] PyInstaller completed
echo.

REM ============================================================
REM Step 5: Verify Backend Executable
REM ============================================================
echo [5/8] Verifying backend executable...

if not exist "dist-backend\purchase_slips_backend.exe" (
    echo [ERROR] Backend executable was not created!
    echo Expected: dist-backend\purchase_slips_backend.exe
    echo.
    echo The build appeared to complete but the executable is missing.
    echo Check the PyInstaller output above for errors.
    pause
    exit /b 1
)

echo [OK] Backend executable found

REM Check file size
set backendSize=0
for %%A in ("dist-backend\purchase_slips_backend.exe") do set backendSize=%%~zA
set /a sizeMB=%backendSize% / 1048576

echo Backend size: %sizeMB% MB

if %sizeMB% LSS 10 (
    echo [WARNING] Backend executable seems small for Flask app
    echo This might indicate missing dependencies
    echo Recommended size: 15-30 MB
) else (
    echo [OK] Backend size looks reasonable
)

REM List bundled files
echo.
echo Checking bundled files in dist-backend:
if exist "dist-backend\templates" (
    echo [OK] templates folder found
) else (
    echo [WARNING] templates folder missing
)

if exist "dist-backend\config.json" (
    echo [OK] config.json found
) else (
    echo [WARNING] config.json missing
)

echo.

REM ============================================================
REM Step 6: Electron Dependencies
REM ============================================================
echo [6/8] Checking Electron dependencies...

pushd desktop

if not exist "node_modules" (
    echo Installing Node packages - this may take 3-5 minutes...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed!
        popd
        pause
        exit /b 1
    )
    echo [OK] Node packages installed
) else (
    echo [OK] Node modules already installed
)

echo.

REM ============================================================
REM Step 7: Build Electron Application
REM ============================================================
echo [7/8] Building Electron desktop application...
echo This will package the Python backend with Electron...
echo This may take 3-8 minutes...
echo.

call npm run build

if errorlevel 1 (
    echo.
    echo [ERROR] Electron build failed!
    echo Check the npm output above for details
    popd
    pause
    exit /b 1
)

popd

echo.
echo [OK] Electron build completed
echo.

REM ============================================================
REM Step 8: Final Verification
REM ============================================================
echo [8/8] Verifying complete build...
echo.
echo ============================================================
echo  BUILD VERIFICATION REPORT
echo ============================================================
echo.

set BUILD_OK=1

REM Check Electron executable
if exist "desktop\dist\win-unpacked\Smart Purchase Slip.exe" (
    echo [OK] Electron App: desktop\dist\win-unpacked\Smart Purchase Slip.exe
    for %%F in ("desktop\dist\win-unpacked\Smart Purchase Slip.exe") do (
        set /a appSizeMB=%%~zF / 1048576
    )
    echo     Size: %appSizeMB% MB
) else (
    echo [ERROR] Electron executable not found
    set BUILD_OK=0
)

REM Check bundled backend
if exist "desktop\dist\win-unpacked\resources\dist-backend\purchase_slips_backend.exe" (
    echo [OK] Backend bundled in resources
) else (
    echo [ERROR] Backend not bundled in Electron resources
    set BUILD_OK=0
)

REM Check config
if exist "desktop\dist\win-unpacked\resources\config.json" (
    echo [OK] config.json bundled
) else (
    echo [ERROR] config.json not bundled
    set BUILD_OK=0
)

REM Check installer
echo.
set INSTALLER_FOUND=0
for %%F in ("desktop\dist\Smart Purchase Slip Setup *.exe") do (
    if exist "%%F" (
        echo [OK] Installer: %%~nxF
        set /a instSizeMB=%%~zF / 1048576
        echo     Size: %instSizeMB% MB
        set INSTALLER_FOUND=1
    )
)

if %INSTALLER_FOUND%==0 (
    echo [WARNING] Installer not found in desktop\dist\
)

echo.
echo ============================================================

if %BUILD_OK%==1 (
    echo  BUILD SUCCESS!
    echo ============================================================
    echo.
    echo Your application is ready to test and distribute.
    echo.
    echo TESTING OPTIONS:
    echo.
    echo 1. Quick Test - No installation required:
    echo    desktop\dist\win-unpacked\Smart Purchase Slip.exe
    echo.
    echo 2. Install and Test:
    echo    Check desktop\dist\ for the installer exe
    echo.
    echo 3. Check logs if issues occur:
    echo    %%APPDATA%%\smart-purchase-slip\logs\
    echo.
    echo IMPORTANT NOTES:
    echo - Backend starts automatically when you launch the app
    echo - First launch may take 5-10 seconds to initialize
    echo - Check backend logs if connection issues occur
    echo - Ensure no other process is using port 5000
    echo.
) else (
    echo  BUILD COMPLETED WITH ERRORS
    echo ============================================================
    echo.
    echo Some files are missing. Please review the errors above.
    echo You may need to rebuild or check your configuration.
    echo.
)

echo ============================================================
echo.
pause
