@echo off
echo ========================================
echo REBUILDING DESKTOP APP WITH FIXES
echo ========================================
echo.

echo Step 1: Clean previous build...
if exist dist-backend rmdir /s /q dist-backend
if exist build rmdir /s /q build

echo.
echo Step 2: Rebuild backend executable...
pyinstaller backend.spec --clean --distpath .

if errorlevel 1 (
    echo ERROR: Failed to build backend!
    pause
    exit /b 1
)

echo.
echo Step 3: Rebuild Electron app...
cd desktop
call npm install
call npm run build

if errorlevel 1 (
    echo ERROR: Failed to build Electron app!
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Your app is ready in: desktop\dist\
echo.
echo Run the installer or the .exe to test!
echo.
pause
