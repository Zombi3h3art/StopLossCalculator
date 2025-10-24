@echo off
setlocal enableextensions

rem ==================================================
echo   ==================================================
echo   [*] STOP LOSS CALCULATOR DASHBOARD
echo   ==================================================
echo.
echo   Starting dashboard...

set "SCRIPT_DIR=%~dp0"
set "DEFAULT_PROJECT=%USERPROFILE%\Desktop\Python_Projects\projects\stop_loss_calculator\"
set "PROJECT_DIR="

rem First, check if the batch file lives inside the project directory
if exist "%SCRIPT_DIR%simple_dashboard.py" set "PROJECT_DIR=%SCRIPT_DIR%"

rem If not, fall back to the default Desktop project location
if not defined PROJECT_DIR if exist "%DEFAULT_PROJECT%simple_dashboard.py" set "PROJECT_DIR=%DEFAULT_PROJECT%"

if not defined PROJECT_DIR (
    echo   [ERROR] Could not locate the Stop Loss Calculator project.
    echo          Looked in:
    echo            1) %SCRIPT_DIR%
    echo            2) %DEFAULT_PROJECT%
    echo          Update this launcher with the correct path.
    goto :PAUSE_EXIT
)

pushd "%PROJECT_DIR%" >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Unable to change directory to:
    echo          %PROJECT_DIR%
    goto :PAUSE_EXIT
)

echo   [OK] Project directory: %CD%

set "PYTHON_EXE="
for %%P in (py.exe python.exe python3.exe) do (
    for /f "delims=" %%I in ('where %%P 2^>nul') do (
        set "PYTHON_EXE=%%~fI"
        goto :FOUND_PYTHON
    )
)

:FOUND_PYTHON
if not defined PYTHON_EXE (
    echo   [ERROR] Python was not found on PATH.
    echo          Install Python 3.11+ or update PATH, then rerun this launcher.
    goto :POP_AND_EXIT
)

echo   [OK] Python found at: %PYTHON_EXE%

"%PYTHON_EXE%" -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Streamlit is not installed in this environment.
    echo          Install it with: "%PYTHON_EXE%" -m pip install streamlit pydantic
    goto :POP_AND_EXIT
)

echo   [OK] Opening browser in 3 seconds...
for /l %%S in (3,-1,1) do (
    <nul set /p=      Launching in %%S...\r
    timeout /t 1 /nobreak >nul
)
<nul set /p=      Launching now...        \r

echo.
start "" "%PYTHON_EXE%" -m streamlit run simple_dashboard.py
if errorlevel 1 (
    echo   [ERROR] Failed to start Streamlit. Check the console above for errors.
    goto :POP_AND_EXIT
)

echo   [OK] Dashboard is running at http://localhost:8501

echo.
echo   TIPS:
echo   - Dashboard will auto-refresh as you change inputs
echo   - Close this window to stop the dashboard
echo   - Press Ctrl+C to force stop if needed

popd >nul

goto :PAUSE_EXIT

:POP_AND_EXIT
popd >nul

:PAUSE_EXIT
echo.
pause
endlocal
