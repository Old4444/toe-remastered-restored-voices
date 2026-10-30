@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python was not found. Install it from python.org and tick "Add python.exe to PATH".
  pause
  exit /b 1
)
python -c "import numpy, UnityPy, PIL" >nul 2>nul
if errorlevel 1 (
  echo First run: installing the title-logo libraries ^(numpy, UnityPy, pillow^) with pip...
  python -m pip install -q numpy UnityPy pillow
)
python toe_patcher.py %*
