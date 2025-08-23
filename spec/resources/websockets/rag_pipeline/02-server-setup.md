# Socket.IO Server Setup

## Integration with Existing HTTP Server

The Socket.IO server will run alongside the existing HTTP status server on the same port (8003) using the same threading model.

## Server Configuration

### 1. AsyncServer Initialization

Add to `status_server.py` after existing imports:

```python
import socketio
import asyncio
from typing import Dict, Any, List, Optional

# Create Socket.IO server instance
sio = socketio.AsyncServer(
    cors_allowed_origins="*",  # Configure based on environment
    async_mode='threading',    # Compatible with existing threading
    logger=True,               # Enable logging for debugging
    engineio_logger=False      # Reduce log noise
)

# Create ASGI/WSGI wrapper for HTTP integration
app = socketio.ASGIApp(sio)
```

### 2. CORS Configuration

Configure CORS based on environment:

```python
def get_cors_config():
    """Get CORS configuration based on environment."""
    import os
    
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        return [
            "https://yourdomain.com",
            "https://chat.yourdomain.com"
        ]
    else:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

# Update server initialization
sio = socketio.AsyncServer(
    cors_allowed_origins=get_cors_config(),
    cors_credentials=True,
    async_mode='threading'
)
```

### 3. Server Integration Pattern

Modify the existing `start_status_server` function:

```python
def start_status_server(port: int = 8003):
    """Start the status server with Socket.IO support."""
    from werkzeug.serving import WSGIRequestHandler
    from werkzeug.serving import make_server
    
    # Create hybrid server that handles both HTTP and WebSocket
    class HybridHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            """Handle HTTP GET requests (existing logic)."""
            if self.path == "/status":
                # Existing HTTP status logic
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                status = pipeline_status.get()
                # Add WebSocket connection info
                status["websocket_enabled"] = True
                status["websocket_path"] = "/socket.io"
                
                self.wfile.write(json.dumps(status, indent=2).encode())
            
            elif self.path == "/health":
                # Existing health check
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"OK")
            
            else:
                # Let Socket.IO handle WebSocket upgrade requests
                self.send_response(404)
                self.end_headers()
    
    # Start HTTP server
    server = HTTPServer(("0.0.0.0", port), HybridHandler)
    
    # Start Socket.IO server in separate thread
    socketio_thread = threading.Thread(
        target=lambda: sio.start_background_task(_run_socketio_server, port),
        daemon=True
    )
    socketio_thread.start()
    
    # Start HTTP server in main thread
    http_thread = threading.Thread(target=server.serve_forever, daemon=True)
    http_thread.start()
    
    print(f"[STATUS-SERVER] HTTP server started on port {port}")
    print(f"[STATUS-SERVER] Socket.IO server started on port {port}")
    
    return server

async def _run_socketio_server(port: int):
    """Run Socket.IO server."""
    import eventlet
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', port + 1)), app)
```

### 4. Alternative: Single Port Configuration

For a cleaner single-port setup, use the ASGI approach:

```python
from socketio import ASGIApp
import uvicorn

# Create a combined ASGI application
app = socketio.ASGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'},
    '/status': {'content_type': 'application/json', 'filename': None}
})

def start_status_server(port: int = 8003):
    """Start unified HTTP/WebSocket server."""
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
```

### 5. Namespace Configuration

Set up namespaces for different pipeline types:

```python
# Namespace for Google Drive pipeline
@sio.event(namespace='/google_drive')
async def connect(sid, environ):
    print(f"[SOCKET-IO] Google Drive client connected: {sid}")
    await sio.emit('pipeline:status', pipeline_status.get(), 
                  namespace='/google_drive', room=sid)

@sio.event(namespace='/google_drive')
async def disconnect(sid):
    print(f"[SOCKET-IO] Google Drive client disconnected: {sid}")

# Namespace for Local Files pipeline  
@sio.event(namespace='/local_files')
async def connect(sid, environ):
    print(f"[SOCKET-IO] Local Files client connected: {sid}")
    await sio.emit('pipeline:status', pipeline_status.get(),
                  namespace='/local_files', room=sid)

@sio.event(namespace='/local_files')
async def disconnect(sid):
    print(f"[SOCKET-IO] Local Files client disconnected: {sid}")
```

### 6. Environment Variables

Add these environment variables for configuration:

```bash
# Socket.IO Configuration
SOCKET_IO_PORT=8003
SOCKET_IO_CORS_ORIGIN=http://localhost:3000
SOCKET_IO_PATH=/socket.io
SOCKET_IO_NAMESPACE=/pipeline
SOCKET_IO_LOG_LEVEL=INFO
```

### 7. Docker Integration

Update Docker configuration to expose WebSocket port:

```dockerfile
# In Dockerfile
EXPOSE 8003

# Ensure WebSocket headers are handled
ENV SOCKET_IO_TRANSPORTS=websocket,polling
```

### 8. Health Check Integration

Add WebSocket health check to existing endpoint:

```python
def do_GET(self):
    if self.path == "/health":
        # Check both HTTP and WebSocket health
        health_status = {
            "status": "healthy",
            "http_server": "running",
            "websocket_server": "running" if sio else "disabled",
            "connected_clients": len(sio.manager.get_participants("/", "/"))
        }
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(health_status).encode())
```

This setup maintains compatibility with existing HTTP clients while adding WebSocket support for real-time updates.