# -*- mode: python ; coding: utf-8 -*-
#
# uninstaller.spec
# ────────────────
# PyInstaller spec for the ISO Manual Assistant uninstaller.
# Produces: dist/ISO_Manual_Assistant_Uninstall.exe  (single-file exe)
#
# During setup this exe is copied into:
#   %LOCALAPPDATA%\ISO Manual Assistant\ISO_Manual_Assistant_Uninstall.exe
#
# The Windows registry UninstallString points here so it appears
# in Settings → Apps → "Add or Remove Programs".

from pathlib import Path

ROOT = Path(SPECPATH).parent   # project root (parent of build/)

a = Analysis(
    [str(ROOT / 'setup_wizard' / 'uninstaller.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        '_tkinter',
        'winreg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'chromadb', 'webview', 'ollama', 'pdfplumber', 'pypdf',
        'docx', 'streamlit', 'numpy', 'pandas', 'torch',
        'urllib',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ISO_Manual_Assistant_Uninstall',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
    # icon='build/icon.ico',
)
