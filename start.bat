@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=py -3"
%PYTHON% -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
if errorlevel 1 set "PYTHON=python"
%PYTHON% -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
if errorlevel 1 (
    echo Python 3.10 or newer is required.
    pause
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    if errorlevel 1 (
        echo Could not create .env from .env.example.
        pause
        exit /b 1
    )
    start "" notepad.exe ".env"
    echo Configure .env, save it, then press Enter here to continue.
    pause
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv ".venv"
    if errorlevel 1 (
        echo Could not create the Python virtual environment.
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and try again.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" main.py
pause
