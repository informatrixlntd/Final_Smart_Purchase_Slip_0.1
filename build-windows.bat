@echo off
echo ============================================================
echo   Smart Purchase Slip - Windows Installer Builder
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

echo.
echo ============================================================
echo   STEP 1: Installing Python Dependencies
echo ============================================================
echo.

pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

echo.
echo ============================================================
echo   STEP 2: Building Python Backend Executable
echo ============================================================
echo.

REM Clean previous build
if exist "dist-backend" rmdir /s /q "dist-backend"
if exist "build" rmdir /s /q "build"

REM Build using PyInstaller
pyinstaller backend.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] Failed to build backend executable
    pause
    exit /b 1
)

REM Move the executable to dist-backend folder
if not exist "dist-backend" mkdir "dist-backend"
move "dist\purchase_slips_backend.exe" "dist-backend\"
if errorlevel 1 (
    echo [ERROR] Failed to move backend executable
    pause
    exit /b 1
)

REM Copy templates to dist-backend
if not exist "dist-backend\templates" mkdir "dist-backend\templates"
xcopy /E /I /Y "backend\templates" "dist-backend\templates"

echo [OK] Backend executable created: dist-backend\purchase_slips_backend.exe

echo.
echo ============================================================
echo   STEP 3: Installing Node.js Dependencies
echo ============================================================
echo.

cd desktop
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies
    cd ..
    pause
    exit /b 1
)
echo [OK] Node.js dependencies installed

echo.
echo ============================================================
echo   STEP 4: Building Electron Installer
echo ============================================================
echo.

call npm run build-win
if errorlevel 1 (
    echo [ERROR] Failed to build Electron installer
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ============================================================
echo   BUILD COMPLETED SUCCESSFULLY!
echo ============================================================
echo.
echo Your installer is ready at:
echo   desktop\dist\Smart Purchase Slip Setup.exe
echo.
echo Installer size: ~150-200 MB
echo.
echo You can distribute this .exe file to client computers.
echo Each client will need MySQL server details to connect.
echo.
echo Press any key to open the dist folder...
pause >nul
explorer "desktop\dist"
