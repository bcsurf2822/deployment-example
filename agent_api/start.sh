#!/bin/bash
set -e

echo "[AGENT-API-START] Starting services..."

# Start supervisor in background
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf &

# Wait for MCP server to be ready
echo "[AGENT-API-START] Waiting for MCP server to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:3001 >/dev/null 2>&1; then
        echo "[AGENT-API-START] MCP server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "[AGENT-API-START] MCP server failed to start"
        exit 1
    fi
    sleep 1
done

# Wait for FastAPI to be ready
echo "[AGENT-API-START] Waiting for FastAPI to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        echo "[AGENT-API-START] FastAPI is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "[AGENT-API-START] FastAPI failed to start"
        exit 1
    fi
    sleep 1
done

echo "[AGENT-API-START] All services are ready!"

# Keep the container running
wait