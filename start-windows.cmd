@echo off
cd /d "%~dp0"
if not exist ".venv-win\Scripts\python.exe" (
  echo Create the Windows environment first. See README.md.
  pause
  exit /b 1
)
".venv-win\Scripts\python.exe" run.py
