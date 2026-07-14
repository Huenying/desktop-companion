@echo off
REM Start Desktop Companion Character (no console window)
cd /d "%~dp0"
start "" /B "%~dp0venv\Scripts\pythonw" character.py
