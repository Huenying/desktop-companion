@echo off
chcp 65001 >nul
title Desktop Companion — Auto-Start Setup

echo ============================================
echo  Desktop Companion Character — Setup
echo ============================================
echo.

set VENV_PYTHON=%~dp0venv\Scripts\python.exe
set VENV_PYTHONW=%~dp0venv\Scripts\pythonw.exe

REM ── 1. Check character.png exists ──
if not exist "%~dp0character.png" (
    echo [STEP 1/4] Extracting character from confirmed.jpeg...
    "%VENV_PYTHON%" "%~dp0extract_character.py"
    if errorlevel 1 (
        echo [ERROR] Failed to extract character. Make sure confirmed.jpeg exists.
        pause
        exit /b 1
    )
    echo [OK] Character extracted!
) else (
    echo [STEP 1/4] character.png found — skipping extraction.
)

REM ── 2. Check venv has dependencies ──
echo [STEP 2/4] Checking virtual environment...
"%VENV_PYTHON%" -c "import PyQt5" 2>nul
if errorlevel 1 (
    echo Installing dependencies in venv...
    "%~dp0venv\Scripts\pip" install PyQt5 Pillow numpy
)
echo [OK] Dependencies ready!

REM ── 3. Add to Startup folder ──
echo [STEP 3/4] Adding to Windows Startup...

REM Create startup shortcut pointing to venv pythonw
powershell -Command "& {$ws = New-Object -ComObject WScript.Shell; $startup = [Environment]::GetFolderPath('Startup'); $s = $ws.CreateShortcut(\"$startup\Desktop Companion.lnk\"); $s.TargetPath = '%VENV_PYTHONW:\=\\%'; $s.Arguments = 'character.py'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Desktop Companion Character'; $s.Save(); Write-Host '[OK] Shortcut created in: ' $startup}"

if errorlevel 1 (
    echo [WARNING] Could not create startup shortcut.
    echo   Create shortcut manually to: %VENV_PYTHONW%
    echo   Arguments: character.py
    echo   Working dir: % ~dp0
) else (
    echo [OK] Auto-start installed! Character will appear when you log in.
)

REM ── 4. Launch ──
echo [STEP 4/4] Launching Desktop Companion...
start "" "%VENV_PYTHONW%" "%~dp0character.py"

echo.
echo ============================================
echo  Setup complete! The character is now running.
echo  Right-click on the character for options.
echo  It will start automatically next time you boot.
echo ============================================
echo.
pause
