"""
iso_assist_main.py
──────────────────
PyInstaller entry point for the ISO Manual Assistant desktop app.

PyInstaller cannot use the -m (module) invocation pattern, so this file
acts as the single __main__ script that boots the application.

In a frozen build:
  - All bundled code lives under sys._MEIPASS (read-only)
  - User data (ChromaDB, chats.db, documents) is stored in:
        %APPDATA%\\ISO Manual Assistant   (Windows)
        ~/Library/Application Support/ISO Manual Assistant  (macOS)
        ~/.local/share/ISO Manual Assistant  (Linux)
"""

import sys
from pathlib import Path

# When frozen, sys._MEIPASS is already the first entry in sys.path,
# so bundled packages are importable directly. In development mode,
# ensure the src-layout package is importable.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from iso_assist.desktop import main  # noqa: E402

if __name__ == "__main__":
    main()
