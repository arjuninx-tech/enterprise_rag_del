#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ISO Manual Assistant — macOS Build Script
#  Run from the project root:  bash build/build_mac.sh
# ═══════════════════════════════════════════════════════════════
set -e   # exit on first error

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "============================================================"
echo " ISO Manual Assistant -- macOS Build"
echo "============================================================"
echo ""
echo "[INFO] Project root: $ROOT"
echo ""

# ── 1. Prerequisites ──────────────────────────────────────────────────────────
echo "[1/6] Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Install Python 3.11+ from https://python.org"
    exit 1
fi
python3 --version

if ! python3 -c "import PyInstaller" &>/dev/null; then
    echo "[..] Installing PyInstaller..."
    pip3 install pyinstaller --quiet
fi
echo "       PyInstaller ready."

# Check for Homebrew (needed for create-dmg)
if ! command -v brew &>/dev/null; then
    echo "[WARN] Homebrew not found. DMG creation will be skipped."
    echo "       Install Homebrew: https://brew.sh"
    HAVE_BREW=false
else
    HAVE_BREW=true
fi

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

# ── 2. Clean previous build ───────────────────────────────────────────────────
echo "[2/6] Cleaning previous output..."
rm -rf "$ROOT/dist/ISO Manual Assistant.app"
rm -rf "$ROOT/dist/ISO Manual Assistant"
rm -f  "$ROOT/dist/ISO_Manual_Assistant_v"*".dmg"
find "$ROOT/app"          -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$ROOT/setup_wizard" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
echo "       Done."
echo ""

# ── 3. Install Python dependencies ────────────────────────────────────────────
echo "[3/6] Installing Python dependencies..."
pip3 install -r requirements.txt --quiet
echo "       Done."
echo ""

# ── 4. Build .app with PyInstaller ───────────────────────────────────────────
echo "[4/6] Building .app bundle with PyInstaller..."
echo "       (takes 3–6 minutes)"
echo ""

python3 -m PyInstaller build/iso_assist_mac.spec --noconfirm --clean

APP_PATH="$ROOT/dist/ISO Manual Assistant.app"
if [ ! -d "$APP_PATH" ]; then
    echo "[ERROR] .app bundle not found after build."
    exit 1
fi
echo ""
echo "[OK]  App built: dist/ISO Manual Assistant.app"
echo ""

# ── 5. Code-sign (optional — skip if no Apple Developer ID) ──────────────────
echo "[5/6] Code signing..."
# Uncomment and set your Developer ID to sign the app:
# DEVELOPER_ID="Developer ID Application: Your Name (XXXXXXXXXX)"
# codesign --deep --force --verify --verbose \
#     --sign "$DEVELOPER_ID" \
#     --options runtime \
#     --entitlements build/entitlements.plist \
#     "$APP_PATH"
# echo "[OK]  App signed."

# Without signing, the app still runs if the user right-clicks → Open
echo "       (Skipped — add your Developer ID to the script to enable signing)"
echo ""

# ── 6. Create .dmg ────────────────────────────────────────────────────────────
echo "[6/6] Creating .dmg installer..."
DMG_PATH="$ROOT/dist/ISO_Manual_Assistant_v1.0.0_macOS.dmg"

if $HAVE_BREW; then
    # Install create-dmg if missing
    if ! command -v create-dmg &>/dev/null; then
        echo "       Installing create-dmg via Homebrew..."
        brew install create-dmg --quiet
    fi

    create-dmg \
        --volname "ISO Manual Assistant" \
        --volicon "build/icon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 128 \
        --icon "ISO Manual Assistant.app" 150 170 \
        --hide-extension "ISO Manual Assistant.app" \
        --app-drop-link 450 170 \
        --no-internet-enable \
        "$DMG_PATH" \
        "$ROOT/dist/ISO Manual Assistant.app" 2>/dev/null || {
            # create-dmg exits non-zero if it can't find an icon file — use fallback
            echo "       (icon.icns not found, creating DMG without custom icon)"
            hdiutil create \
                -volname "ISO Manual Assistant" \
                -srcfolder "$ROOT/dist/ISO Manual Assistant.app" \
                -ov -format UDZO \
                "$DMG_PATH"
        }
else
    # No Homebrew — use built-in hdiutil
    echo "       (Homebrew not available — using hdiutil for basic DMG)"
    hdiutil create \
        -volname "ISO Manual Assistant" \
        -srcfolder "$ROOT/dist/ISO Manual Assistant.app" \
        -ov -format UDZO \
        "$DMG_PATH"
fi

if [ -f "$DMG_PATH" ]; then
    SIZE=$(du -sh "$DMG_PATH" | cut -f1)
    echo "[OK]  DMG created: dist/ISO_Manual_Assistant_v1.0.0_macOS.dmg  ($SIZE)"
else
    echo "[WARN] DMG creation failed. The .app bundle is still usable directly."
fi
echo ""

# ── Done ──────────────────────────────────────────────────────────────────────
echo "============================================================"
echo " BUILD COMPLETE"
echo "============================================================"
echo ""
echo "  App bundle:  dist/ISO Manual Assistant.app"
if [ -f "$DMG_PATH" ]; then
echo "  Installer:   dist/ISO_Manual_Assistant_v1.0.0_macOS.dmg"
fi
echo ""
echo "  To distribute:"
echo "    1. Test the .app by double-clicking it"
echo "    2. Share the .dmg — users drag the app to /Applications"
echo ""
echo "  Note: Without code signing, users must right-click the app"
echo "        and choose Open on first launch (macOS Gatekeeper)."
echo ""
echo "  For App Store / notarization, set DEVELOPER_ID in this script"
echo "  and run: xcrun notarytool submit <dmg> --apple-id ... --wait"
echo ""
