# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('RECEITA_EVENTOS.csv', '.'), ('RECEITA_H.csv', '.'), ('RECEITA_BATALHA_090.csv', '.'), ('recipe_s00.csv', '.'), ('OPCOES_MUDOS.csv', '.'), ('RECEITA_VIDEOS_090.csv', '.'), ('edl_final.json', '.'), ('fonts', 'fonts'), ('tools', 'tools')]
binaries = []
hiddenimports = ['utf', 'afs2', 'afs2b', 'enc_vga', 'hcadec', 'seyfert', 'toe_extras', 'toe_videos', 'toe_abertura', 'usm_own', 'usm_templates', 'toe_voices090', 'toe_build', 'build090', 'toe_install', 'toe_logo', 'toe_psp', 'toe_audio', 'psx_decode']
tmp_ret = collect_all('UnityPy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('archspec')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('astc_encoder')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['toe_patcher.py'],
    pathex=['lib'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['fmod_toolkit', 'pyfmodex'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ToePatcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
