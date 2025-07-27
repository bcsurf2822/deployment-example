#!/bin/bash
# Simple health check - verify Python environment and imports
python -c "import sys; import os; print(f'[RAG-PIPELINE-HEALTHCHECK] Python {sys.version} - OK')" || exit 1

# Check if required modules can be imported
python -c "import supabase, openai, google.auth; print('[RAG-PIPELINE-HEALTHCHECK] Core dependencies - OK')" || exit 1

echo "[RAG-PIPELINE-HEALTHCHECK] Health check passed"