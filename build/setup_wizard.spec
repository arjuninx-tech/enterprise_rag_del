# -*- mode: python ; coding: utf-8 -*-
#
# setup_wizard.spec
# ─────────────────
# PyInstaller spec for the ISO Manual Assistant setup wizard.
# Produces: dist/ISO_Manual_Assistant_Setup.exe  (single-file exe)
#
# The setup wizard is distributed alongside the main app folder:
#
#   ISO_Manual_Assistant_Setup.exe   ← run this first
#   ISO_Manual_Assistant/            ← main app (PyInstaller folder bundle)
#   vector_db/                       ← pre-built knowledge base (if available)
#
# The wizard copies vector_db/ to %APPDATA%\ISO Manual Assistant\data\vector_db\,
# installs Ollama, pulls selected models, and creates a desktop shortcut.

from pathlib import Path

ROOT = Path(SPECPATH).parent   # project root (parent of build/)

a = Analysis(
    [str(ROOT / 'setup_wizard' / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        '_tkinter',
        'urllib.request',
        'urllib.error',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Keep this exe tiny — exclude everything not needed
        'chromadb', 'webview', 'ollama', 'pdfplumber', 'pypdf',
        'docx', 'streamlit', 'numpy', 'pandas', 'torch',
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
    name='ISO_Manual_Assistant_Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,               # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,                # single .exe for easy distribution
    # icon='build/icon.ico',
)
