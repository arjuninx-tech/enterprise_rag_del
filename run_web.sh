#!/bin/bash
echo "Starting Private RAG Workbench (Web Mode)..."
echo "Open your browser at: http://localhost:5000"
echo
PYTHON_BIN=python3
if [ -x .venv/bin/python ]; then PYTHON_BIN=.venv/bin/python; fi
PYTHONPATH=src "$PYTHON_BIN" -m iso_assist.server
