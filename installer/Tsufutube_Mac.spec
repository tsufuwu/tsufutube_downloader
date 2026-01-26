# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for macOS
Builds a .app bundle with proper macOS integration
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
#  EXECUTABLE (macOS)
# =========================================================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Tsufutube Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX not recommended on macOS
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,  # Enable for macOS drag-drop URL support
    target_arch=None,  # Universal binary (or specify 'x86_64' / 'arm64')
    codesign_identity=None,  # Set to your Apple Developer ID for signing
    entitlements_file='entitlements.plist',  # Optional: for sandboxing
    icon='../assets/icon.icns',  # macOS uses .icns format
)

# =========================================================================
#  COLLECT (Folder mode, required for BUNDLE)
# =========================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Tsufutube Downloader',
)

# =========================================================================
#  BUNDLE (.app for macOS)
# =========================================================================

app = BUNDLE(
    coll,
    name='Tsufutube Downloader.app',
    icon='../assets/icon.icns',
    bundle_identifier='com.tsufutube.downloader',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'Tsufutube Downloader',
        'CFBundleDisplayName': 'Tsufutube Downloader',
        'CFBundleGetInfoString': 'Video Downloader for YouTube, Dailymotion, Bilibili and more',
        'CFBundleIdentifier': 'com.tsufutube.downloader',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleExecutable': 'Tsufutube Downloader',
        'NSHumanReadableCopyright': 'Copyright © 2024 Tsufutube',
        'NSHighResolutionCapable': True,
        'NSSupportsAutomaticGraphicsSwitching': True,
        # Permissions
        'NSAppleEventsUsageDescription': 'This app needs access to run scripts.',
        'NSDownloadsFolderUsageDescription': 'This app needs access to save downloaded videos.',
        # URL Scheme Handler
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'Tsufutube URL',
                'CFBundleURLSchemes': ['tsufutube'],
            }
        ],
        # Supported file types
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Video URL',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': ['public.url'],
            }
        ],
        # Required for Hardened Runtime (if code signing)
        'LSMinimumSystemVersion': '10.13.0',
    },
)
