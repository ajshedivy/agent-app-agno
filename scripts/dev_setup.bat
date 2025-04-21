@echo off
REM filepath: /C:/Users/AdamShedivy/Documents/sandox/agent-app-agno/scripts/dev_setup.bat
REM Windows Development Setup

echo ============================================================
echo -*- Development setup...
echo ============================================================

echo ============================================================
echo -*- Removing virtual env
echo ============================================================
echo INFO: rmdir /S /Q .venv
if exist .venv rmdir /S /Q .venv

echo ============================================================
echo -*- Creating virtual env
echo ============================================================
echo INFO: uv venv --python 3.12
set VIRTUAL_ENV=%CD%\.venv
uv venv --python 3.12

echo ============================================================
echo -*- Creating Windows-compatible requirements file
echo ============================================================
echo INFO: Removing uvloop and adding Windows-specific packages
type requirements.txt | findstr /v "uvloop" > requirements-windows-temp.txt

echo ============================================================
echo -*- Installing Windows-specific requirements
echo ============================================================
echo INFO: uv pip install -r requirements-windows-temp.txt
set VIRTUAL_ENV=%CD%\.venv
uv pip install -r requirements-windows-temp.txt
del requirements-windows-temp.txt

echo ============================================================
echo -*- Installing workspace in editable mode with dev dependencies
echo ============================================================
echo INFO: uv pip install -e .[dev]
set VIRTUAL_ENV=%CD%\.venv
uv pip install -e .[dev]

echo ============================================================
echo -*- Development setup complete
echo ============================================================
echo -*- Activate venv using: .venv\Scripts\activate (cmd) or .venv\Scripts\Activate.ps1 (PowerShell)