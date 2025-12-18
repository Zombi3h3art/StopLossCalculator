@echo off
setlocal

rem ==================================================
echo ==================================================
echo [*] STOP LOSS CALCULATOR DASHBOARD
echo ==================================================
echo.
echo Starting dashboard...
echo.

cd /d "%~dp0"
if not exist "simple_dashboard.py" (
    echo [ERROR] Could not locate simple_dashboard.py
    echo         Make sure this .bat file is in the project folder.
    pause
    exit /b 1
)

echo [OK] Project directory: %CD%
echo.

rem Find Python
set "PYTHON_EXE="
where python.exe >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python.exe"
    goto :CheckStreamlit
)

where py.exe >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py.exe"
    goto :CheckStreamlit
)

echo [ERROR] Python not found on PATH.
echo         Install Python 3.11+ and try again.
pause
exit /b 1

:CheckStreamlit
echo [OK] Python found: %PYTHON_EXE%
echo.

%PYTHON_EXE% -m streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Streamlit is not installed.
    echo         Install with: %PYTHON_EXE% -m pip install streamlit
    pause
    exit /b 1
)

echo [OK] Streamlit is installed
echo.
echo [*] Launching Streamlit server in new window...
start "Stop Loss Calculator" cmd /k "%PYTHON_EXE% -m streamlit run simple_dashboard.py"

echo.
echo ==================================================
echo Dashboard should now be open in your browser!
echo Close the "Stop Loss Calculator" window to stop the server.
echo ==================================================
echo.
pause
