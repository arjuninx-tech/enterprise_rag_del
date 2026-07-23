"""
build/build_kb.py
─────────────────
Standalone script to build (or rebuild) the ISO Manual Assistant
knowledge base from source documents in data/approved_documents/.

Run this BEFORE build_windows.bat so the vector_db is ready to bundle.

Usage (from project root):
    python build/build_kb.py

What it does:
    1. Verifies Ollama is running and nomic-embed-text is available.
    2. Reads every .pdf / .docx / .txt / .md file in data/approved_documents/.
    3. Chunks, embeds, and upserts all text into data/vector_db/
       (ChromaDB persistent collection "iso_documents").
    4. Prints a summary of indexed documents and chunk count.

Requirements:
    - Ollama must be running:  ollama serve
    - nomic-embed-text pulled: ollama pull nomic-embed-text
    - pip install chromadb ollama pdfplumber python-docx pypdf
"""

import sys
from pathlib import Path

# Ensure the src-layout package is importable from the project root.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from iso_assist.config import DOCS_PATH, CHROMA_PATH, EMBED_MODEL, OLLAMA_BASE_URL


def _check_ollama():
    """Return (ok, message)."""
    try:
        import ollama
        client = ollama.Client(host=OLLAMA_BASE_URL)
        models = client.list()
        names  = [m["name"] for m in models.get("models", [])]
        if not any(EMBED_MODEL in n for n in names):
            return False, (
                f"Model '{EMBED_MODEL}' not found locally.\n"
                f"Pull it with:  ollama pull {EMBED_MODEL}"
            )
        return True, f"Ollama OK — {EMBED_MODEL} ready."
    except Exception as exc:
        return False, (
            f"Cannot connect to Ollama at {OLLAMA_BASE_URL}.\n"
            f"Start it with:  ollama serve\n"
            f"Error: {exc}"
        )


def main():
    print("=" * 60)
    print(" ISO Manual Assistant — Knowledge Base Builder")
    print("=" * 60)
    print()

    # ── 1. Check source documents ─────────────────────────────────────────────
    if not DOCS_PATH.exists() or not any(DOCS_PATH.iterdir()):
        print(f"[WARN] No documents found in: {DOCS_PATH}")
        print("       Add .pdf / .docx / .txt / .md files there and re-run.")
        print()
        print("       The knowledge base was NOT built.")
        sys.exit(0)

    supported = (".pdf", ".docx", ".txt", ".md", ".markdown")
    doc_files = [f for f in DOCS_PATH.iterdir()
                 if f.is_file() and f.suffix.lower() in supported]

    if not doc_files:
        print(f"[WARN] No supported files in {DOCS_PATH}")
        print(f"       Supported: {', '.join(supported)}")
        sys.exit(0)

    print(f"[OK]  Found {len(doc_files)} source document(s) in {DOCS_PATH}:")
    for f in sorted(doc_files):
        size_kb = round(f.stat().st_size / 1024, 1)
        print(f"        {f.name}  ({size_kb} KB)")
    print()

    # ── 2. Check Ollama ───────────────────────────────────────────────────────
    print(f"[..] Checking Ollama ({OLLAMA_BASE_URL})…")
    ok, msg = _check_ollama()
    if not ok:
        print(f"[ERROR] {msg}")
        sys.exit(1)
    print(f"[OK]  {msg}")
    print()

    # ── 3. Run ingestion ──────────────────────────────────────────────────────
    print("[..] Building knowledge base (this may take several minutes)…")
    print()

    from iso_assist.services.ingest import rebuild_index

    def on_msg(message: str):
        print(f"      {message}")

    def on_chunks(done: int, total: int):
        pct = int(done / total * 100) if total else 0
        bar = "#" * (pct // 5) + "." * (20 - pct // 5)
        print(f"\r      [{bar}] {done}/{total} chunks", end="", flush=True)

    result = rebuild_index(
        progress_callback=on_msg,
        chunk_progress_callback=on_chunks,
    )
    print()  # newline after progress bar
    print()

    # ── 4. Summary ────────────────────────────────────────────────────────────
    if result.get("error"):
        print(f"[ERROR] Build failed: {result['error']}")
        sys.exit(1)

    doc_count   = result.get("documents", len(doc_files))
    chunk_count = result.get("chunks", 0)
    print("=" * 60)
    print(" Knowledge base built successfully!")
    print("=" * 60)
    print(f"  Documents indexed : {doc_count}")
    print(f"  Chunks stored     : {chunk_count}")
    print(f"  Output location   : {CHROMA_PATH}")
    print()
    print("  You can now run build_windows.bat to package the app.")
    print("  The vector_db folder will be bundled automatically.")
    print()


if __name__ == "__main__":
    main()
