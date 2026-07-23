# -*- mode: python ; coding: utf-8 -*-
#
# iso_assist_mac.spec
# ───────────────────
# PyInstaller specification for ISO Manual Assistant on macOS.
#
# Usage (run from the project root on a Mac):
#   pyinstaller build/iso_assist_mac.spec
#
# Output:
#   dist/ISO Manual Assistant.app   (macOS application bundle)
#
# What is bundled:
#   ✓ All Python code  (app/ package)
#   ✓ UI HTML/CSS/JS   (app/ui/index.html)
#   ✓ All Python dependencies (chromadb, pywebview, ollama, pdfplumber, …)
#   ✓ Pre-built ChromaDB vector index (if data/vector_db/ exists at build time)
#
# What is NOT bundled (written to user data dir at runtime):
#   ✗ data/chats.db                  (created on first run)
#   ✗ data/approved_documents/       (user supplies these)
#
# User data is stored at:
#   ~/Library/Application Support/ISO Manual Assistant/

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parent   # project root (parent of build/)

# ── Collect tricky packages ───────────────────────────────────────────────────
chroma_datas,  chroma_bins,  chroma_hidden  = collect_all('chromadb')
webview_datas, webview_bins, webview_hidden = collect_all('webview')
pydantic_datas,pydantic_bins,pydantic_hidden= collect_all('pydantic')

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / 'iso_assist_main.py')],
    pathex=[str(ROOT / 'src')],

    binaries=chroma_bins + webview_bins + pydantic_bins,

    datas=[
        # UI — must be at app/ui/ inside the bundle so desktop.py can find it
        (str(ROOT / 'src' / 'iso_assist' / 'ui' / 'index.html'), 'iso_assist/ui'),

        # Pre-built ChromaDB knowledge base (bundled read-only seed).
        # On first launch desktop.py copies this to ~/Library/... so
        # ChromaDB can write to it normally.
        *( [(str(ROOT / 'data' / 'vector_db'), 'data/vector_db')]
           if (ROOT / 'data' / 'vector_db').exists() else [] ),

        # Collected package data
        *chroma_datas,
        *webview_datas,
        *pydantic_datas,
    ],

    hiddenimports=[
        # ── App package ───────────────────────────────────────────────────────
        'iso_assist',
        'iso_assist.config',
        'iso_assist.desktop',
        'iso_assist.models.chat_store',
        'iso_assist.models.doc_memory',
        'iso_assist.services.document_loader',
        'iso_assist.services.ingest',
        'iso_assist.services.ollama_manager',
        'iso_assist.services.prompts',
        'iso_assist.services.rag_engine',
        'iso_assist.utils.logger',

        # ── Ollama client ─────────────────────────────────────────────────────
        'ollama',
        'ollama._client',
        'ollama._types',

        # ── Document parsing ──────────────────────────────────────────────────
        'pdfplumber',
        'pdfminer',
        'pdfminer.high_level',
        'pdfminer.layout',
        'pypdf',
        'docx',
        'docx.oxml',

        # ── pywebview macOS backend ───────────────────────────────────────────
        'webview.platforms.cocoa',
        'webview.platforms.gtk',       # fallback

        # ── ChromaDB internals ────────────────────────────────────────────────
        'chromadb.api',
        'chromadb.api.types',
        'chromadb.api.client',
        'chromadb.config',
        'chromadb.db.base',
        'chromadb.db.impl',
        'chromadb.db.impl.sqlite',
        'chromadb.execution.executor.local',
        'chromadb.segment.impl.manager.local',
        'chromadb.segment.impl.metadata.sqlite',
        'chromadb.segment.impl.vector.local_persistent_hnsw',
        'chromadb.telemetry.product.posthog',

        # ── Misc ──────────────────────────────────────────────────────────────
        'dotenv',
        'httpx',
        'httpcore',
        'anyio',
        'anyio._backends._asyncio',
        'sqlite3',

        *chroma_hidden,
        *webview_hidden,
        *pydantic_hidden,
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    excludes=[
        'streamlit', 'tornado', 'bokeh', 'matplotlib',
        'pandas', 'scipy', 'sklearn', 'torch', 'tensorflow',
        'jupyter', 'IPython', 'tkinter', 'wx',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'pytest', 'unittest',
        # Windows-only — not present on macOS
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
    ],

    noarchive=False,
    optimize=1,
)

# ── PYZ archive ───────────────────────────────────────────────────────────────
pyz = PYZ(a.pure)

# ── EXE (the Unix binary inside the .app) ────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ISO Manual Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,         # UPX not recommended on macOS (codesigning issues)
    console=False,     # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # set to 'x86_64' or 'arm64' for single-arch; None = host arch
    codesign_identity=None,
    entitlements_file=None,
    # icon='build/icon.icns',   # uncomment and add icon.icns to build/
)

# ── COLLECT ───────────────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='ISO Manual Assistant',
)

# ── BUNDLE (.app) ─────────────────────────────────────────────────────────────
app = BUNDLE(
    coll,
    name='ISO Manual Assistant.app',
    # icon='build/icon.icns',     # uncomment to add app icon
    bundle_identifier='com.yourorg.iso-manual-assistant',
    info_plist={
        'CFBundleName':               'ISO Manual Assistant',
        'CFBundleDisplayName':        'ISO Manual Assistant',
        'CFBundleVersion':            '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable':    True,
        'NSRequiresAquaSystemAppearance': False,   # supports dark mode
        # Microphone access for voice-to-text input
        'NSMicrophoneUsageDescription': 'ISO Manual Assistant uses the microphone for voice input so you can speak your questions instead of typing.',
        # Allow the app to load local HTML files
        'NSAppTransportSecurity': {
            'NSAllowsLocalNetworking': True,
        },
    },
)
