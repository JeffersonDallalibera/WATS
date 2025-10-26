@echo off
echo ==================================================
echo  WATS Application Rebuild Script [OPTIMIZED]
echo ==================================================
echo  - Includes .env file for database configuration
echo  - Performance optimizations applied
echo  - Deferred initialization for faster startup
echo ==================================================

cd /d "%~dp0"

echo.
echo [1/3] Stopping any running WATS_App processes...
powershell -Command "Get-Process -Name 'WATS_App' -ErrorAction SilentlyContinue | Stop-Process -Force"

echo.
echo [2/3] Rebuilding executable...
venv\Scripts\python.exe -m PyInstaller build_executable.spec --clean

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [3/3] Build completed successfully!
    echo.
    echo ✅ New executable: dist\WATS_App.exe
    echo.
    dir dist\WATS_App.exe
    echo.
    echo Build complete! Press any key to exit...
) else (
    echo.
    echo ❌ Build failed! Check the error messages above.
    echo.
    echo Press any key to exit...
)

pause >nul