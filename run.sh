#!/usr/bin/env bash
echo "Starting Private RAG Workbench..."
PYTHON_BIN=python3
if [ -x .venv/bin/python ]; then PYTHON_BIN=.venv/bin/python; fi
PYTHONPATH=src "$PYTHON_BIN" -m iso_assist.desktop
