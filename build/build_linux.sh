#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ISO Manual Assistant — Linux Build Script
#
#  Produces:
#    dist/ISO_Manual_Assistant/               (folder bundle)
#    dist/ISO_Manual_Assistant_v1.0.0.AppImage (universal Linux package)
#
#  Run from the project root:
#    bash build/build_linux.sh
#
#  System requirements (Ubuntu/Debian):
#    sudo apt install python3 python3-pip python3-gi python3-gi-cairo \
#                     gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
#                     libgtk-3-dev libwebkit2gtk-4.1-dev \
#                     fuse libfuse2 patchelf
#
#  Fedora/RHEL equivalent:
#    sudo dnf install python3 python3-pip python3-gobject \
#                     gtk3-devel webkit2gtk4.1-devel \
#                     fuse fuse-libs patchelf
# ═══════════════════════════════════════════════════════════════
set -e

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "============================================================"
echo " ISO Manual Assistant -- Linux Build"
echo "============================================================"
echo ""
echo "[INFO] Project root: $ROOT"
echo ""

# ── 1. Prerequisites ──────────────────────────────────────────────────────────
echo "[1/6] Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found."
    echo "        Ubuntu:  sudo apt install python3 python3-pip"
    echo "        Fedora:  sudo dnf install python3 python3-pip"
    exit 1
fi
python3 --version

# Check GTK / WebKit2 (pywebview requirement on Linux)
if ! python3 -c "import gi; gi.require_version('WebKit2','4.1'); from gi.repository import WebKit2" 2>/dev/null; then
    if ! python3 -c "import gi; gi.require_version('WebKit2','4.0'); from gi.repository import WebKit2" 2>/dev/null; then
        echo "[ERROR] WebKit2GTK not found. Install it first:"
        echo "        Ubuntu 22+: sudo apt install gir1.2-webkit2-4.1 libwebkit2gtk-4.1-dev"
        echo "        Ubuntu 20:  sudo apt install gir1.2-webkit2-4.0 libwebkit2gtk-4.0-dev"
        echo "        Fedora:     sudo dnf install webkit2gtk4.1-devel"
        exit 1
    fi
fi
echo "       WebKit2GTK: OK"

if ! python3 -c "import PyInstaller" &>/dev/null; then
    echo "[..] Installing PyInstaller..."
    pip3 install pyinstaller --quiet
fi
echo "       PyInstaller: ready"
echo ""

# ── 1b. Build knowledge base if needed ────────────────────────────────────────
if [ ! -d "$ROOT/data/vector_db" ]; then
    if [ -d "$ROOT/data/approved_documents" ] && [ "$(ls -A "$ROOT/data/approved_documents" 2>/dev/null)" ]; then
        echo "[..] No vector_db found but documents exist — building knowledge base..."
        echo "     (Requires Ollama + nomic-embed-text to be running)"
        echo ""
        python3 build/build_kb.py || {
            echo "[WARN] Knowledge base build failed. Make sure Ollama is running:"
            echo "       ollama serve && ollama pull nomic-embed-text"
            echo ""
        }
    else
        echo "[WARN] No pre-built KB found. Users will need to rebuild after installing."
        echo ""
    fi
else
    echo "[OK]  Pre-built knowledge base found -- will be bundled."
    echo ""
fi

# ── 2. Clean ──────────────────────────────────────────────────────────────────
echo "[2/6] Cleaning previous output..."
rm -rf "$ROOT/dist/ISO_Manual_Assistant"
rm -f  "$ROOT/dist/ISO_Manual_Assistant"*.AppImage
find "$ROOT/app"          -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$ROOT/setup_wizard" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
echo "       Done."
echo ""

# ── 3. Install Python dependencies ────────────────────────────────────────────
echo "[3/6] Installing Python dependencies..."
pip3 install -r requirements.txt --quiet
echo "       Done."
echo ""

# ── 4. Build folder bundle with PyInstaller ───────────────────────────────────
echo "[4/6] Building with PyInstaller..."
echo "       (takes 3–6 minutes)"
echo ""

python3 -m PyInstaller build/iso_assist_linux.spec --noconfirm --clean

BUNDLE="$ROOT/dist/ISO_Manual_Assistant"
if [ ! -d "$BUNDLE" ]; then
    echo "[ERROR] dist/ISO_Manual_Assistant/ not found after build."
    exit 1
fi
echo ""
echo "[OK]  Bundle built: dist/ISO_Manual_Assistant/"
echo ""

# ── 5. Create .desktop launcher ───────────────────────────────────────────────
echo "[5/6] Creating .desktop file..."

DESKTOP_FILE="$BUNDLE/ISO_Manual_Assistant.desktop"
cat > "$DESKTOP_FILE" << 'DESKTOP'
[Desktop Entry]
Name=ISO Manual Assistant
Comment=Query ISO 9001 / 14001 documents with AI
Exec=ISO_Manual_Assistant
Icon=iso_manual_assistant
Type=Application
Categories=Office;Productivity;
Terminal=false
StartupWMClass=ISO_Manual_Assistant
DESKTOP

echo "       Done."
echo ""

# ── 6. Package as AppImage ────────────────────────────────────────────────────
echo "[6/6] Packaging as AppImage..."
echo ""

APPIMAGE_OUT="$ROOT/dist/ISO_Manual_Assistant_v1.0.0.AppImage"
APPIMAGETOOL="$ROOT/build/appimagetool-x86_64.AppImage"

# Download appimagetool if not present
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "       Downloading appimagetool..."
    ARCH=$(uname -m)
    curl -L -o "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage" \
        --progress-bar
    chmod +x "$APPIMAGETOOL"
fi

# AppImage requires an AppDir layout with a root .desktop + AppRun
APPDIR="$ROOT/dist/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy the PyInstaller bundle into AppDir
cp -r "$BUNDLE/." "$APPDIR/usr/bin/"

# AppRun entry point
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/ISO_Manual_Assistant" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# .desktop file at AppDir root (required by AppImage spec)
cp "$DESKTOP_FILE" "$APPDIR/ISO_Manual_Assistant.desktop"
cp "$DESKTOP_FILE" "$APPDIR/usr/share/applications/"

# Placeholder icon (replace with a real 256x256 PNG at build/icon.png)
if [ -f "$ROOT/build/icon.png" ]; then
    cp "$ROOT/build/icon.png" "$APPDIR/iso_manual_assistant.png"
    cp "$ROOT/build/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/iso_manual_assistant.png"
else
    # Create a minimal placeholder so appimagetool doesn't fail
    python3 -c "
import struct, zlib, base64
# Minimal 1x1 purple PNG
data = b'\\x89PNG\\r\\n\\x1a\\n' + b'\\x00\\x00\\x00\\rIHDR' + struct.pack('>IIBBBBB',1,1,8,2,0,0,0) + b'\\x90wS\\xde' + b'\\x00\\x00\\x00\\x0cIDATx\\x9cc\\xf8\\x9f\\x81\\x00\\x00\\x01\\x04\\x00\\x01\\xf5\\x18\\xd8' + b'\\x00\\x00\\x00\\x00IEND\\xaeB\\x60\\x82'
with open('$APPDIR/iso_manual_assistant.png','wb') as f: f.write(data)
" 2>/dev/null || touch "$APPDIR/iso_manual_assistant.png"
fi

# Build the AppImage
ARCH=$(uname -m) "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_OUT" 2>&1 || {
    echo "[WARN] AppImage creation failed. The folder bundle is still usable:"
    echo "       dist/ISO_Manual_Assistant/ISO_Manual_Assistant"
    echo ""
    echo "       To run directly:"
    echo "       chmod +x dist/ISO_Manual_Assistant/ISO_Manual_Assistant"
    echo "       ./dist/ISO_Manual_Assistant/ISO_Manual_Assistant"
    exit 0
}

if [ -f "$APPIMAGE_OUT" ]; then
    chmod +x "$APPIMAGE_OUT"
    SIZE=$(du -sh "$APPIMAGE_OUT" | cut -f1)
    echo "[OK]  AppImage created: dist/ISO_Manual_Assistant_v1.0.0.AppImage  ($SIZE)"
fi

echo ""

# ── Done ──────────────────────────────────────────────────────────────────────
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo ""
echo "  Folder bundle: dist/ISO_Manual_Assistant/"
if [ -f "$APPIMAGE_OUT" ]; then
echo "  AppImage:      dist/ISO_Manual_Assistant_v1.0.0.AppImage"
fi
echo ""
echo "  To run locally:"
echo "    chmod +x dist/ISO_Manual_Assistant_v1.0.0.AppImage"
echo "    ./dist/ISO_Manual_Assistant_v1.0.0.AppImage"
echo ""
echo "  To install a desktop shortcut for the current user:"
echo "    cp dist/ISO_Manual_Assistant_v1.0.0.AppImage ~/.local/bin/"
echo "    cat > ~/.local/share/applications/iso-manual-assistant.desktop << EOF"
echo "    [Desktop Entry]"
echo "    Name=ISO Manual Assistant"
echo "    Exec=$HOME/.local/bin/ISO_Manual_Assistant_v1.0.0.AppImage"
echo "    Icon=iso_manual_assistant"
echo "    Type=Application"
echo "    Categories=Office;Productivity;"
echo "    EOF"
echo ""
echo "  System requirements on end-user machines:"
echo "    Ubuntu 22+: sudo apt install gir1.2-webkit2-4.1 libfuse2"
echo "    Ubuntu 20:  sudo apt install gir1.2-webkit2-4.0 libfuse2"
echo "    Fedora:     sudo dnf install webkit2gtk4.1 fuse-libs"
echo ""
