#!/bin/bash
set -e

# Default to Google Drive pipeline if no service specified
SERVICE=${RAG_SERVICE:-google_drive}

# Log startup
echo "[RAG-PIPELINE-CONTAINER] Starting RAG Pipeline service: $SERVICE"

case "$SERVICE" in
    "google_drive")
        echo "[RAG-PIPELINE-CONTAINER] Starting Google Drive pipeline"
        cd Google_Drive
        exec python main.py "$@"
        ;;
    "local_files")
        echo "[RAG-PIPELINE-CONTAINER] Starting Local Files pipeline"
        cd Local_Files
        exec python main.py "$@"
        ;;
    *)
        echo "[RAG-PIPELINE-CONTAINER] Unknown service: $SERVICE"
        echo "[RAG-PIPELINE-CONTAINER] Available services: google_drive, local_files"
        exit 2
        ;;
esac