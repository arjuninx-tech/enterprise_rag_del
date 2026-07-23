# Building the Windows Installer

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10 – 3.12 | [python.org](https://python.org) |
| PyInstaller | 6.x | `pip install pyinstaller` |
| Inno Setup | 6.x | [jrsoftware.org](https://jrsoftware.org/isdl.php) |
| UPX (optional) | any | `winget install upx` |

All dependencies in `requirements.txt` must be installed in the active Python environment before building.

---

## Quick build

```bat
# From the project root, with your venv active:
.\build\build_windows.bat
```

Output: `dist\ISO_Manual_Assistant_Setup_v1.0.0.exe`

---

## Bundling a pre-built knowledge base (recommended)

The installer can include a pre-built ChromaDB vector index so end-users can ask questions immediately without uploading documents.

**Steps:**
1. Place your ISO documents in `data\approved_documents\`
2. Run the app normally: `python -m app.desktop`
3. Click **Knowledge Base → Rebuild Index** and wait for it to complete
4. Close the app
5. Run `build\build_windows.bat`

The build script will detect `data\vector_db\` and bundle it automatically. The installer copies it to `%APPDATA%\ISO Manual Assistant\data\vector_db\` during installation.

**What is NOT bundled** (by design):
- `data\chats.db` — chat history is per-user, created fresh on first run
- `data\approved_documents\` — users manage their own source documents

---

## What the installer does

1. **Welcome / License / Directory** — standard Inno Setup pages
2. **Model Selection** — custom checkbox page:
   - `nomic-embed-text` — always included (required for KB search)
   - `Qwen 2.5 – 7B` — pre-selected (recommended)
   - `Qwen 3 – 8B`, `Gemma 3 – 4B`, `Llama 3.1 – 8B` — optional
3. **File copy** — copies app to `Program Files\ISO Manual Assistant\`
4. **Ollama setup** — checks if Ollama is installed; downloads and installs it silently if not
5. **Model downloads** — for each selected model, runs `ollama pull <model>` with a progress bar
6. **Finish** — optional desktop shortcut, then launches the app

---

## Customising

### Change app version
Edit `#define AppVersion` at the top of `installer.iss`.

### Add an icon
Put `icon.ico` in `build\` and uncomment the `icon=` line in `iso_assist.spec`.

### Sign the installer
After building, use `signtool.exe` from the Windows SDK:
```bat
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 ^
  /a dist\ISO_Manual_Assistant_Setup_v1.0.0.exe
```

---

## Troubleshooting builds

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: chromadb` at runtime | Run `pip install chromadb` in the build env then rebuild |
| `webview` window blank | Ensure Edge WebView2 Runtime is installed on the target machine ([download](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)) |
| Installer can't find Ollama after download | Antivirus may have blocked `OllamaSetup.exe` — whitelist it |
| `ollama pull` times out | Check internet connectivity; models can also be pulled manually after install |
| App crashes on start | Run `ISO_Manual_Assistant.exe` from a terminal to see Python traceback |
