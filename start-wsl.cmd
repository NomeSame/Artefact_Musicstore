@echo off
wsl.exe -d Ubuntu --cd "%~dp0" ./.venv/bin/python run.py
if errorlevel 1 pause
