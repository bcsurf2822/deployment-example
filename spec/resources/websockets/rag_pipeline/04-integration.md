# Integration with Existing RAG Pipeline Code

## Files to Modify

### 1. status_server.py - Primary Integration Point

#### Current State Analysis
- HTTP server on port 8003 with `/status` and `/health` endpoints
- `PipelineStatus` class manages shared state with threading locks
- Background thread serves HTTP requests

#### Required Changes

**A. Add Socket.IO imports and initialization:**

```python
import socketio
import asyncio
from typing import Dict, Any, Optional
import os

# Socket.IO server instance - add after existing imports
sio = socketio.AsyncServer(
    cors_allowed_origins=os.getenv('SOCKET_IO_CORS_ORIGIN', '*').split(','),
    async_mode='threading',
    logger=os.getenv('SOCKET_IO_LOG_LEVEL', 'INFO').lower() == 'debug'
)

# Global reference for pipeline type
PIPELINE_TYPE = os.getenv('RAG_SERVICE', 'unknown')
PIPELINE_ID = os.getenv('RAG_PIPELINE_ID', f'{PIPELINE_TYPE}-{os.getpid()}')
```

**B. Modify PipelineStatus class:**

```python
class PipelineStatus:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = {
            # ... existing fields ...
        }
        self.socketio_server = None
        self.event_handler = None
    
    def set_socketio_server(self, sio_instance):
        """Initialize Socket.IO integration."""
        self.socketio_server = sio_instance
        self.event_handler = SocketIOEventHandler(sio_instance, PIPELINE_ID, PIPELINE_TYPE)
    
    def add_processing_file(self, filename: str, file_id: Optional[str] = None):
        """Add file to processing list and emit Socket.IO event."""
        with self.lock:
            file_info = {
                "name": filename,
                "id": file_id,
                "started_at": datetime.now().isoformat()
            }
            self.data["files_processing"].append(file_info)
            self.data["last_activity"] = datetime.now().isoformat()
        
        # Emit event asynchronously (non-blocking)
        if self.event_handler:
            asyncio.run_coroutine_threadsafe(
                self.event_handler.emit_file_processing(filename, file_id, file_info),
                asyncio.get_event_loop()
            )
    
    def complete_file(self, filename: str, success: bool = True, stats: dict = None):
        """Complete file processing and emit appropriate event."""
        with self.lock:
            # Existing logic to move file between lists...
            processing = [f for f in self.data["files_processing"] if f["name"] != filename]
            removed = [f for f in self.data["files_processing"] if f["name"] == filename]
            
            if removed:
                file_info = removed[0]
                file_info["completed_at"] = datetime.now().isoformat()
                
                if success:
                    self.data["files_completed"].append(file_info)
                    self.data["total_processed"] += 1
                    if len(self.data["files_completed"]) > 10:
                        self.data["files_completed"] = self.data["files_completed"][-10:]
                    
                    # Emit success event
                    if self.event_handler:
                        asyncio.run_coroutine_threadsafe(
                            self.event_handler.emit_file_completed(filename, file_info.get("id"), stats or {}),
                            asyncio.get_event_loop()
                        )
                else:
                    self.data["files_failed"].append(file_info)
                    self.data["total_failed"] += 1
                    if len(self.data["files_failed"]) > 5:
                        self.data["files_failed"] = self.data["files_failed"][-5:]
                    
                    # Emit failure event
                    if self.event_handler:
                        asyncio.run_coroutine_threadsafe(
                            self.event_handler.emit_file_failed(filename, file_info.get("id"), stats or {}),
                            asyncio.get_event_loop()
                        )
            
            self.data["files_processing"] = processing
            self.data["last_activity"] = datetime.now().isoformat()
    
    def update(self, **kwargs):
        """Update status and emit general status event."""
        with self.lock:
            old_status = self.data.get("status")
            self.data.update(kwargs)
            self.data["last_activity"] = datetime.now().isoformat()
            
            # Emit status change events
            new_status = self.data.get("status")
            if old_status != new_status and self.event_handler:
                asyncio.run_coroutine_threadsafe(
                    self.event_handler.emit_status_update(kwargs),
                    asyncio.get_event_loop()
                )
```

**C. Update start_status_server function:**

```python
def start_status_server(port: int = 8003):
    """Start HTTP and Socket.IO servers."""
    # Set up Socket.IO event handlers
    setup_socketio_handlers()
    
    # Connect Socket.IO to pipeline status
    pipeline_status.set_socketio_server(sio)
    
    # Start Socket.IO server in background thread
    import eventlet
    eventlet.monkey_patch()
    
    def run_socketio():
        """Run Socket.IO server on separate port."""
        socketio_port = port + 100  # e.g., 8103 for Socket.IO
        eventlet.wsgi.server(
            eventlet.listen(('0.0.0.0', socketio_port)), 
            socketio.WSGIApp(sio)
        )
    
    socketio_thread = threading.Thread(target=run_socketio, daemon=True)
    socketio_thread.start()
    
    # Start existing HTTP server
    server = HTTPServer(("0.0.0.0", port), StatusHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    print(f"[STATUS-SERVER] HTTP server started on port {port}")
    print(f"[STATUS-SERVER] Socket.IO server started on port {port + 100}")
    
    # Emit pipeline online event
    asyncio.run_coroutine_threadsafe(
        sio.emit('pipeline:online', {
            "pipeline_id": PIPELINE_ID,
            "pipeline_type": PIPELINE_TYPE,
            "status": "online",
            "started_at": datetime.now().isoformat()
        }, namespace=f'/{PIPELINE_TYPE}'),
        asyncio.new_event_loop()
    )
    
    return server

def setup_socketio_handlers():
    """Set up Socket.IO connection handlers."""
    
    @sio.event
    async def connect(sid, environ):
        pipeline_type = environ.get('HTTP_X_PIPELINE_TYPE', PIPELINE_TYPE)
        print(f"[SOCKET-IO] Client connected: {sid} to {pipeline_type}")
        
        # Send current status to new client
        current_status = pipeline_status.get()
        await sio.emit('pipeline:status', current_status, room=sid)
    
    @sio.event  
    async def disconnect(sid):
        print(f"[SOCKET-IO] Client disconnected: {sid}")
    
    @sio.event
    async def subscribe(sid, data):
        """Subscribe to specific pipeline updates."""
        pipeline_type = data.get('pipeline_type', PIPELINE_TYPE)
        await sio.enter_room(sid, f'pipeline:{pipeline_type}')
        print(f"[SOCKET-IO] Client {sid} subscribed to {pipeline_type}")
    
    @sio.event
    async def unsubscribe(sid, data):
        """Unsubscribe from pipeline updates."""
        pipeline_type = data.get('pipeline_type', PIPELINE_TYPE)
        await sio.leave_room(sid, f'pipeline:{pipeline_type}')
        print(f"[SOCKET-IO] Client {sid} unsubscribed from {pipeline_type}")
```

### 2. supabase_status.py - Database Integration

#### Required Changes

**A. Add Socket.IO event emission to database updates:**

```python
class SupabaseStatusTracker:
    def __init__(self, pipeline_id: str, pipeline_type: str):
        # ... existing initialization ...
        self.socketio_handler = None
    
    def set_socketio_handler(self, handler):
        """Set Socket.IO event handler."""
        self.socketio_handler = handler
    
    def update_processing_status(self, 
                                files_processing: list = None,
                                files_completed: list = None,
                                files_failed: list = None,
                                is_checking: bool = None,
                                next_check_time: str = None):
        """Update detailed processing status with Socket.IO events."""
        try:
            # Existing Supabase update logic...
            result = self.update_status(status_details)
            
            # Emit Socket.IO events for changes
            if self.socketio_handler and result:
                if files_completed:
                    for file_info in files_completed[-1:]:  # Only emit for newest
                        asyncio.run_coroutine_threadsafe(
                            self.socketio_handler.emit_file_completed(
                                file_info.get("name", "unknown"),
                                file_info.get("id"),
                                {"database_updated": True}
                            ),
                            asyncio.get_event_loop()
                        )
                
                if files_failed:
                    for file_info in files_failed[-1:]:  # Only emit for newest
                        asyncio.run_coroutine_threadsafe(
                            self.socketio_handler.emit_file_failed(
                                file_info.get("name", "unknown"),
                                file_info.get("id"),
                                {"database_updated": True}
                            ),
                            asyncio.get_event_loop()
                        )
            
            return result
        except Exception as e:
            print(f"[SUPABASE-STATUS] Error updating processing status: {e}")
            return None
```

### 3. Drive Watcher Integration (drive_watcher.py)

#### Required Changes

**A. Import and initialize event handler:**

```python
# Add at top of file
from status_server import pipeline_status

class GoogleDriveWatcher:
    def __init__(self, credentials_path, token_path, config_path):
        # ... existing initialization ...
        self.event_handler = None
    
    def set_event_handler(self, handler):
        """Set Socket.IO event handler."""
        self.event_handler = handler
    
    async def process_file(self, file_info):
        """Process file with Socket.IO event emission."""
        filename = file_info["name"]
        file_id = file_info["id"]
        
        try:
            # Emit processing started
            if self.event_handler:
                await self.event_handler.emit_file_processing(filename, file_id, file_info)
            
            # Add to pipeline status
            pipeline_status.add_processing_file(filename, file_id)
            
            # Process file (existing logic)
            result = await self._process_file_content(file_info)
            
            # Complete successfully
            pipeline_status.complete_file(filename, success=True, stats=result)
            
        except Exception as e:
            # Complete with failure
            pipeline_status.complete_file(filename, success=False, stats={
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
```

### 4. Local Files Integration (Local_Files/main.py)

#### Required Changes

Similar pattern to Google Drive integration:

```python
from status_server import pipeline_status
from status_server import sio

class LocalFilesWatcher:
    def __init__(self, config_path):
        # ... existing initialization ...
        self.event_handler = None
        
        # Connect to pipeline status
        if pipeline_status.event_handler:
            self.event_handler = pipeline_status.event_handler
    
    def process_file_with_events(self, file_path, file_id):
        """Process file with real-time event emission."""
        filename = os.path.basename(file_path)
        
        try:
            # Start processing
            pipeline_status.add_processing_file(filename, file_id)
            
            # Emit progress events during processing
            if self.event_handler:
                asyncio.run(self.event_handler.emit_file_progress(
                    filename, "extraction", 0.2
                ))
            
            # Extract content
            content = self.extract_content(file_path)
            
            if self.event_handler:
                asyncio.run(self.event_handler.emit_file_progress(
                    filename, "chunking", 0.5
                ))
            
            # Create chunks and embeddings
            chunks = self.create_chunks(content)
            embeddings = self.generate_embeddings(chunks)
            
            if self.event_handler:
                asyncio.run(self.event_handler.emit_file_progress(
                    filename, "storing", 0.9
                ))
            
            # Store in database
            self.store_results(chunks, embeddings, file_info)
            
            # Complete successfully
            pipeline_status.complete_file(filename, success=True, stats={
                "chunks": len(chunks),
                "embeddings": len(embeddings),
                "content_length": len(content)
            })
            
        except Exception as e:
            pipeline_status.complete_file(filename, success=False, stats={
                "error": str(e),
                "stage": "processing"
            })
            raise
```

### 5. Docker Configuration Updates

#### docker-compose.dev.yml

```yaml
services:
  rag-google-drive-dev:
    environment:
      - SOCKET_IO_CORS_ORIGIN=http://localhost:3000
      - RAG_SERVICE=google_drive
      - RAG_PIPELINE_ID=gdrive-dev-${HOSTNAME:-local}
    ports:
      - "8003:8003"   # HTTP status server
      - "8103:8103"   # Socket.IO server
  
  rag-local-files-dev:
    environment:
      - SOCKET_IO_CORS_ORIGIN=http://localhost:3000
      - RAG_SERVICE=local_files  
      - RAG_PIPELINE_ID=local-dev-${HOSTNAME:-local}
    ports:
      - "8004:8003"   # HTTP status server
      - "8104:8103"   # Socket.IO server
```

### 6. Environment Variables

Add to .env files:

```bash
# Socket.IO Configuration
SOCKET_IO_CORS_ORIGIN=http://localhost:3000,https://yourdomain.com
SOCKET_IO_LOG_LEVEL=INFO
SOCKET_IO_HEARTBEAT_INTERVAL=30
SOCKET_IO_TIMEOUT=60

# Pipeline identification
RAG_PIPELINE_ID=auto-generated-if-not-set
```

### 7. Error Handling and Graceful Degradation

```python
class SocketIOEventHandler:
    def __init__(self, sio_server, pipeline_id, pipeline_type):
        self.sio = sio_server
        self.pipeline_id = pipeline_id
        self.pipeline_type = pipeline_type
        self.failed_emit_count = 0
        self.max_failed_emits = 10
    
    async def safe_emit(self, event: str, data: dict):
        """Emit with error handling and graceful degradation."""
        try:
            await self.sio.emit(event, data, namespace=f'/{self.pipeline_type}')
            self.failed_emit_count = 0  # Reset on success
            return True
        except Exception as e:
            self.failed_emit_count += 1
            print(f"[SOCKET-IO] Failed to emit {event}: {e}")
            
            # Disable Socket.IO emission if too many failures
            if self.failed_emit_count > self.max_failed_emits:
                print(f"[SOCKET-IO] Disabling events after {self.max_failed_emits} failures")
                return False
            
            return False
    
    async def emit_file_processing(self, filename: str, file_id: str, file_info: dict):
        """Emit file processing event with error handling."""
        if self.failed_emit_count <= self.max_failed_emits:
            await self.safe_emit('file:processing', {
                "pipeline_id": self.pipeline_id,
                "file": {"name": filename, "id": file_id, **file_info},
                "timestamp": datetime.now().isoformat()
            })
```

This integration maintains backward compatibility while adding real-time Socket.IO events to the existing RAG pipeline architecture.