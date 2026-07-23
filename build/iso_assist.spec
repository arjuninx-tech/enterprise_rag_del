# -*- mode: python ; coding: utf-8 -*-
#
# iso_assist.spec
# ───────────────
# PyInstaller specification for ISO Manual Assistant.
#
# Usage (run from the project root):
#   pyinstaller build/iso_assist.spec
#
# Output:  dist/ISO_Manual_Assistant/   (folder bundle)
#          The Inno Setup script then packages this folder into a .exe installer.
#
# What is bundled:
#   ✓ All Python code  (app/ package)
#   ✓ UI HTML/CSS/JS   (app/ui/index.html)
#   ✓ All Python dependencies (chromadb, pywebview, ollama, pdfplumber, …)
#
# What is NOT bundled (written to %APPDATA%\ISO Manual Assistant at runtime):
#   ✗ data/chats.db          (chat history — per-user, created on first run)
#   ✗ data/approved_documents/  (source ISO documents — user supplies these)
#
# The pre-built ChromaDB vector index is handled separately by the Inno Setup
# installer — it copies data/vector_db/ from the source tree into the user's
# %APPDATA%\ISO Manual Assistant\data\vector_db\ during installation.

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# ── Paths ─────────────────────────────────────────────────────────────────────
# SPECPATH is the directory containing this .spec file (i.e. build/)
ROOT = Path(SPECPATH).parent

# ── Collect tricky packages ───────────────────────────────────────────────────
# collect_all() grabs datas + binaries + hiddenimports for a package.
chroma_datas, chroma_bins, chroma_hidden = collect_all('chromadb')
webview_datas, webview_bins, webview_hidden = collect_all('webview')
pydantic_datas, pydantic_bins, pydantic_hidden = collect_all('pydantic')

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / 'iso_assist_main.py')],
    pathex=[str(ROOT / 'src')],

    binaries=chroma_bins + webview_bins + pydantic_bins,

    datas=[
        # UI — must be at app/ui/ inside the bundle so desktop.py can find it
        (str(ROOT / 'src' / 'iso_assist' / 'ui' / 'index.html'), 'iso_assist/ui'),

        # Pre-built ChromaDB knowledge base (bundled read-only seed).
        # On first launch desktop.py copies this to %APPDATA% so ChromaDB
        # can write to it. Only included if the directory exists at build time.
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

        # ── pywebview Windows-specific backends ───────────────────────────────
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'clr',

        # ── ChromaDB internals (belt-and-suspenders) ──────────────────────────
        'chromadb.api',
        'chromadb.api.types',
        'chromadb.api.client',
        'chromadb.config',
        'chromadb.db',
        'chromadb.db.base',
        'chromadb.db.impl',
        'chromadb.db.impl.sqlite',
        'chromadb.execution',
        'chromadb.execution.executor',
        'chromadb.execution.executor.local',
        'chromadb.segment',
        'chromadb.segment.impl',
        'chromadb.segment.impl.manager',
        'chromadb.segment.impl.manager.local',
        'chromadb.segment.impl.metadata',
        'chromadb.segment.impl.metadata.sqlite',
        'chromadb.segment.impl.vector',
        'chromadb.segment.impl.vector.local_persistent_hnsw',
        'chromadb.telemetry',
        'chromadb.telemetry.product',
        'chromadb.telemetry.product.posthog',

        # ── Misc ──────────────────────────────────────────────────────────────
        'dotenv',
        'httpx',
        'httpcore',
        'anyio',
        'anyio._backends._asyncio',
        'anyio._backends._trio',
        'sqlite3',

        *chroma_hidden,
        *webview_hidden,
        *pydantic_hidden,
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # Exclude heavy packages not needed at runtime
    # NOTE: numpy must NOT be excluded — chromadb.api.types imports numpy.typing
    excludes=[
        'streamlit', 'tornado', 'bokeh', 'matplotlib',
        'pandas', 'scipy', 'sklearn', 'torch', 'tensorflow',
        'jupyter', 'IPython', 'tkinter', 'wx',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'pytest', 'unittest', 'setuptools', 'pkg_resources._vendor',
    ],

    noarchive=False,
    optimize=1,
)

# ── PYZ archive ───────────────────────────────────────────────────────────────
pyz = PYZ(a.pure)

# ── EXE ───────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,       # folder mode (faster startup than onefile)
    name='ISO_Manual_Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,               # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='build/icon.ico',     # uncomment and add icon.ico to build/ if desired
)

# ── COLLECT (folder bundle) ───────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ISO_Manual_Assistant',  # → dist/ISO_Manual_Assistant/
)
