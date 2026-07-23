@echo off
echo Starting Private RAG Workbench (Desktop)...
if exist .venv\Scripts\python.exe set "PYTHON=.venv\Scripts\python.exe"
if not defined PYTHON set "PYTHON=python"
set PYTHONPATH=src
"%PYTHON%" -m iso_assist.desktop
