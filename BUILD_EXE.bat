@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Builds ToePatcher.exe on YOUR computer from the readable source in this folder.
rem   One single program: voices, title-logo change, cutscene movie audio, mute of the new skits, optional restored opening.
where python >nul 2>nul
if errorlevel 1 (echo ERROR: Python not found. & pause & exit /b 1)
set EXTRA=--collect-all UnityPy --collect-all archspec --collect-all astc_encoder --exclude-module fmod_toolkit --exclude-module pyfmodex
set PKGS=pyinstaller numpy UnityPy pillow
python -m pip install -q %PKGS%
if errorlevel 1 (echo pip failed & pause & exit /b 1)
python -m PyInstaller --noconfirm --clean --onefile --console --name ToePatcher --paths lib ^
 --hidden-import utf --hidden-import afs2 --hidden-import afs2b --hidden-import enc_vga --hidden-import hcadec --hidden-import seyfert ^
 --hidden-import toe_extras --hidden-import toe_videos --hidden-import toe_abertura --hidden-import usm_own --hidden-import usm_templates ^
 --hidden-import toe_voices090 --hidden-import toe_build --hidden-import build090 --hidden-import toe_install --hidden-import toe_logo ^
 --hidden-import toe_psp --hidden-import toe_audio --hidden-import psx_decode ^
 --add-data "RECEITA_EVENTOS.csv;." --add-data "RECEITA_H.csv;." --add-data "RECEITA_BATALHA_090.csv;." --add-data "recipe_s00.csv;." ^
 --add-data "RECEITA_VIDEOS_090.csv;." --add-data "edl_final.json;." ^
 --add-data "fonts;fonts" --add-data "tools;tools" %EXTRA% toe_patcher.py
if errorlevel 1 (echo BUILD FAILED & pause & exit /b 1)
echo.
echo Built: dist\ToePatcher.exe
python hash_file.py dist\ToePatcher.exe
echo.
echo Writing the license texts of the libraries included in the .exe ^(dist\THIRD_PARTY_LICENSES.txt^)...
python -m pip install -q pip-licenses
python -m piplicenses --from=mixed --format=plain-vertical --with-license-file --no-license-path --packages UnityPy archspec astc-encoder-py attrs brotli etcpak lz4 numpy pillow texture2ddecoder tpk_ar fsspec packaging requests urllib3 certifi charset-normalizer idna pyinstaller pyinstaller-hooks-contrib --output-file dist\THIRD_PARTY_LICENSES.txt
if errorlevel 1 (echo WARNING: could not generate THIRD_PARTY_LICENSES.txt) else (echo Attach dist\THIRD_PARTY_LICENSES.txt to the Release next to ToePatcher.exe.)
echo ^(publish this SHA-256 next to the download^)
pause
