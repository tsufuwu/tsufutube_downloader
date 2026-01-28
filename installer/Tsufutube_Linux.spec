# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Linux
Builds a single executable binary
"""
from PyInstaller.utils.hooks import collect_all
import os

# =========================================================================
#  DATA FILES & HIDDEN IMPORTS
# =========================================================================

datas = [
    ('../assets', 'assets'), 
    ('../modules', 'modules'),
    ('../ffmpeg', 'ffmpeg'),
    # Include .desktop file for Linux integration
    ('../assets/tsufutube.desktop', 'assets'),
]

binaries = []

hiddenimports = [
    'PIL._tkinter_finder', 
    'yt_dlp', 
    'yt_dlp.extractor', 
    'yt_dlp.downloader', 
    'yt_dlp.postprocessor', 
    'yt_dlp.utils',
    'tkinter',
    'customtkinter',
    # Linux-specific
    'gi',  # For GTK integration if available
]

# Collect all yt_dlp modules
tmp_ret = collect_all('yt_dlp')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# =========================================================================
#  ANALYSIS
# =========================================================================

a = Analysis(
    ['../tsufutube_downloader.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'selenium'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# =========================================================================
#  OPTION 1: SINGLE FILE EXECUTABLE (Recommended for distribution)
# =========================================================================

exe_onefile = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tsufutube-downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols for smaller size
    upx=True,    # UPX compression (install upx first: apt install upx)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/icon.png',  # Linux uses PNG for icons
)

# =========================================================================
#  OPTION 2: FOLDER MODE (Faster startup, easier debugging)
#  Uncomment below and comment out exe_onefile above if preferred
# =========================================================================

# exe_folder = EXE(
#     pyz,
#     a.scripts,
#     [],
#     exclude_binaries=True,
#     name='tsufutube-downloader',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=True,
#     upx=True,
#     console=False,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     icon='assets/icon.png',
# )
# 
# coll = COLLECT(
#     exe_folder,
#     a.binaries,
#     a.datas,
#     strip=True,
#     upx=True,
#     upx_exclude=[],
#     name='tsufutube-downloader',
# )
