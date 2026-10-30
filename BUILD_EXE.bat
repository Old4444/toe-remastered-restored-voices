@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Builds ToePatcher.exe on YOUR computer from the readable source in this folder.
rem   BUILD_EXE.bat        = full build (includes the title-logo option; large file)
rem   BUILD_EXE.bat lite   = without the logo option (small file)
where python >nul 2>nul
if errorlevel 1 (echo ERROR: Python not found. & pause & exit /b 1)
set EXTRA=--collect-all UnityPy --collect-all archspec --collect-all astc_encoder --exclude-module fmod_toolkit --exclude-module pyfmodex
set PKGS=pyinstaller numpy UnityPy pillow
if /i "%~1"=="lite" (
  set EXTRA=--exclude-module numpy --exclude-module PIL --exclude-module UnityPy
  set PKGS=pyinstaller
)
python -m pip install -q %PKGS%
if errorlevel 1 (echo pip failed & pause & exit /b 1)
python -m PyInstaller --noconfirm --clean --onefile --console --name ToePatcher --paths lib ^
 --hidden-import utf --hidden-import afs2 --hidden-import afs2b --hidden-import enc_vga --hidden-import hcadec --hidden-import seyfert ^
 --add-data "recipe_battle.csv;." --add-data "recipe_s00.csv;." --add-data "events_em0200.csv;." ^
 --add-data "fonts;fonts" --add-data "tools;tools" %EXTRA% toe_patcher.py
if errorlevel 1 (echo BUILD FAILED & pause & exit /b 1)
echo.
echo Built: dist\ToePatcher.exe
python hash_file.py dist\ToePatcher.exe
echo ^(publish this SHA-256 next to the download^)
pause
