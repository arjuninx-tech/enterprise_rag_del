# -*- mode: python ; coding: utf-8 -*-
#
# iso_assist_linux.spec
# ─────────────────────
# PyInstaller specification for ISO Manual Assistant on Linux.
#
# Usage (run from the project root on a Linux machine):
#   pyinstaller build/iso_assist_linux.spec
#
# Output:
#   dist/ISO_Manual_Assistant/          (folder bundle)
#   → packaged into ISO_Manual_Assistant.AppImage by build_linux.sh
#
# Runtime requirement on the user's machine:
#   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
#                    gir1.2-webkit2-4.1   (or webkit2-4.0 on older distros)
#
# User data is stored at:
#   ~/.local/share/ISO Manual Assistant/    (XDG_DATA_HOME)

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

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
        # UI must be at app/ui/ so desktop.py can find it via sys._MEIPASS
        (str(ROOT / 'src' / 'iso_assist' / 'ui' / 'index.html'), 'iso_assist/ui'),

        # Pre-built ChromaDB knowledge base seed (optional)
        *( [(str(ROOT / 'data' / 'vector_db'), 'data/vector_db')]
           if (ROOT / 'data' / 'vector_db').exists() else [] ),

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

        # ── pywebview Linux backend (GTK + WebKit2) ───────────────────────────
        'webview.platforms.gtk',

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
        'gi',
        'gi.repository.Gtk',
        'gi.repository.WebKit2',

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
        # Windows/macOS-only backends
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'webview.platforms.cocoa',
        'winreg',
    ],

    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ISO_Manual_Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ISO_Manual_Assistant',    # → dist/ISO_Manual_Assistant/
)
