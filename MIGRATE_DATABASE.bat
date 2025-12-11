@echo off
echo ========================================
echo Database Migration Tool
echo ========================================
echo.
echo This will add new fields to your database:
echo - moisture_percent
echo - moisture_kg
echo - company_gst_no
echo - company_mobile_no
echo.
pause

echo.
echo Running migration...
python backend\database.py

echo.
echo ========================================
echo Migration Complete!
echo ========================================
echo.
echo Please restart the application for changes to take effect.
echo.
pause
