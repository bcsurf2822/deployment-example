# Socket.IO Event Handlers

## Event Emission Strategy

Events should be emitted at key points in the pipeline lifecycle to provide real-time updates to connected clients.

## Event Types and Payloads

### 1. Pipeline Lifecycle Events

#### `pipeline:online`
Emitted when a pipeline starts up or comes online.

```python
@pipeline_status.on_status_change
async def emit_pipeline_online():
    payload = {
        "pipeline_id": pipeline_id,
        "pipeline_type": pipeline_type,  # "google_drive" or "local_files"
        "status": "online",
        "started_at": datetime.now().isoformat(),
        "check_interval": pipeline_status.data.get("check_interval", 60),
        "watch_location": get_watch_location()  # folder_id or directory path
    }
    
    await sio.emit('pipeline:online', payload, namespace=f'/{pipeline_type}')
    print(f"[SOCKET-IO] Emitted pipeline:online for {pipeline_type}")
```

#### `pipeline:offline` 
Emitted when pipeline shuts down or goes offline.

```python
async def emit_pipeline_offline():
    payload = {
        "pipeline_id": pipeline_id,
        "pipeline_type": pipeline_type,
        "status": "offline",
        "shutdown_at": datetime.now().isoformat(),
        "reason": "normal_shutdown"  # or "error", "timeout"
    }
    
    await sio.emit('pipeline:offline', payload, namespace=f'/{pipeline_type}')
```

### 2. File Processing Events

#### `file:processing`
Emitted when a file starts being processed.

```python
async def emit_file_processing(filename: str, file_id: str, file_info: dict):
    payload = {
        "pipeline_id": pipeline_id,
        "file": {
            "name": filename,
            "id": file_id,
            "size": file_info.get("size"),
            "mime_type": file_info.get("mime_type"),
            "started_at": datetime.now().isoformat()
        },
        "processing_stage": "extraction",  # "extraction", "chunking", "embedding"
        "estimated_duration": estimate_processing_time(file_info)
    }
    
    await sio.emit('file:processing', payload, namespace=f'/{pipeline_type}')
    print(f"[SOCKET-IO] File processing started: {filename}")
```

#### `file:progress`
Emitted during file processing to show progress.

```python
async def emit_file_progress(filename: str, stage: str, progress: float):
    payload = {
        "pipeline_id": pipeline_id,
        "file": {"name": filename, "id": file_id},
        "processing_stage": stage,  # "extraction", "chunking", "embedding", "storing"
        "progress": progress,  # 0.0 to 1.0
        "timestamp": datetime.now().isoformat()
    }
    
    await sio.emit('file:progress', payload, namespace=f'/{pipeline_type}')
```

#### `file:completed`
Emitted when file processing completes successfully.

```python
async def emit_file_completed(filename: str, file_id: str, stats: dict):
    payload = {
        "pipeline_id": pipeline_id,
        "file": {
            "name": filename,
            "id": file_id,
            "completed_at": datetime.now().isoformat()
        },
        "results": {
            "chunks_created": stats.get("chunks", 0),
            "embeddings_generated": stats.get("embeddings", 0),
            "processing_duration": stats.get("duration", 0),
            "content_length": stats.get("content_length", 0)
        },
        "success": True
    }
    
    await sio.emit('file:completed', payload, namespace=f'/{pipeline_type}')
    print(f"[SOCKET-IO] File completed: {filename}")
```

#### `file:failed`
Emitted when file processing fails.

```python
async def emit_file_failed(filename: str, file_id: str, error: Exception):
    payload = {
        "pipeline_id": pipeline_id,
        "file": {
            "name": filename,
            "id": file_id,
            "failed_at": datetime.now().isoformat()
        },
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "stage": determine_failure_stage(error),
            "retryable": is_retryable_error(error)
        },
        "success": False
    }
    
    await sio.emit('file:failed', payload, namespace=f'/{pipeline_type}')
    print(f"[SOCKET-IO] File failed: {filename} - {error}")
```

### 3. Status Update Events

#### `status:update`
Emitted for general status changes.

```python
async def emit_status_update(status_changes: dict):
    payload = {
        "pipeline_id": pipeline_id,
        "timestamp": datetime.now().isoformat(),
        "changes": status_changes,
        "current_status": pipeline_status.get()
    }
    
    await sio.emit('status:update', payload, namespace=f'/{pipeline_type}')
```

#### `heartbeat`
Emitted periodically to maintain connection.

```python
async def emit_heartbeat():
    payload = {
        "pipeline_id": pipeline_id,
        "timestamp": datetime.now().isoformat(),
        "status": "alive",
        "uptime": get_uptime_seconds(),
        "memory_usage": get_memory_usage(),
        "active_files": len(pipeline_status.data.get("files_processing", []))
    }
    
    await sio.emit('heartbeat', payload, namespace=f'/{pipeline_type}')
```

## Integration with Existing Code

### 1. Modify PipelineStatus Class

Add Socket.IO event emission to existing methods:

```python
class PipelineStatus:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = {...}
        self.socketio_server = None  # Will be set by status_server
    
    def set_socketio_server(self, sio_instance):
        """Set the Socket.IO server instance for event emission."""
        self.socketio_server = sio_instance
    
    async def _emit_if_connected(self, event: str, data: dict):
        """Safely emit Socket.IO event if server is available."""
        if self.socketio_server:
            try:
                pipeline_type = data.get("pipeline_type", "unknown")
                await self.socketio_server.emit(event, data, namespace=f'/{pipeline_type}')
            except Exception as e:
                print(f"[SOCKET-IO] Failed to emit {event}: {e}")
    
    def add_processing_file(self, filename: str, file_id: Optional[str] = None):
        """Add a file to processing list and emit event."""
        with self.lock:
            file_info = {
                "name": filename,
                "id": file_id,
                "started_at": datetime.now().isoformat()
            }
            self.data["files_processing"].append(file_info)
            self.data["last_activity"] = datetime.now().isoformat()
            
            # Emit Socket.IO event
            asyncio.create_task(self._emit_if_connected('file:processing', {
                "pipeline_id": os.getenv("RAG_PIPELINE_ID", "unknown"),
                "file": file_info,
                "processing_stage": "started"
            }))
    
    def complete_file(self, filename: str, success: bool = True, stats: dict = None):
        """Move file from processing to completed/failed and emit event."""
        with self.lock:
            # Existing logic...
            
            if removed:
                file_info = removed[0]
                file_info["completed_at"] = datetime.now().isoformat()
                
                if success:
                    self.data["files_completed"].append(file_info)
                    self.data["total_processed"] += 1
                    
                    # Emit success event
                    asyncio.create_task(self._emit_if_connected('file:completed', {
                        "pipeline_id": os.getenv("RAG_PIPELINE_ID", "unknown"),
                        "file": file_info,
                        "results": stats or {},
                        "success": True
                    }))
                else:
                    self.data["files_failed"].append(file_info)
                    self.data["total_failed"] += 1
                    
                    # Emit failure event
                    asyncio.create_task(self._emit_if_connected('file:failed', {
                        "pipeline_id": os.getenv("RAG_PIPELINE_ID", "unknown"),
                        "file": file_info,
                        "error": stats or {},
                        "success": False
                    }))
```

### 2. Integration with File Watchers

Update file processing loops to emit events:

```python
# In drive_watcher.py or local file watcher
async def process_file_with_events(file_info):
    filename = file_info["name"]
    file_id = file_info["id"]
    
    try:
        # Start processing
        pipeline_status.add_processing_file(filename, file_id)
        await sio.emit('file:processing', {...})
        
        # Extract content
        await sio.emit('file:progress', {
            "file": {"name": filename, "id": file_id},
            "processing_stage": "extraction",
            "progress": 0.2
        })
        
        content = extract_content(file_info)
        
        # Create chunks
        await sio.emit('file:progress', {
            "file": {"name": filename, "id": file_id},
            "processing_stage": "chunking", 
            "progress": 0.5
        })
        
        chunks = create_chunks(content)
        
        # Generate embeddings
        await sio.emit('file:progress', {
            "file": {"name": filename, "id": file_id},
            "processing_stage": "embedding",
            "progress": 0.8
        })
        
        embeddings = generate_embeddings(chunks)
        
        # Store in database
        store_results(chunks, embeddings)
        
        # Complete
        pipeline_status.complete_file(filename, success=True, stats={
            "chunks": len(chunks),
            "embeddings": len(embeddings),
            "duration": time.time() - start_time
        })
        
    except Exception as e:
        pipeline_status.complete_file(filename, success=False, stats={
            "error": str(e),
            "stage": determine_failure_stage(e)
        })
        raise
```

### 3. Error Handling

Implement robust error handling for Socket.IO events:

```python
class SocketIOEventHandler:
    def __init__(self, sio_server, pipeline_id, pipeline_type):
        self.sio = sio_server
        self.pipeline_id = pipeline_id
        self.pipeline_type = pipeline_type
        self.retry_count = {}
        self.max_retries = 3
    
    async def emit_with_retry(self, event: str, data: dict, retries: int = 3):
        """Emit event with retry logic."""
        for attempt in range(retries):
            try:
                await self.sio.emit(event, data, namespace=f'/{self.pipeline_type}')
                self.retry_count[event] = 0
                return True
            except Exception as e:
                print(f"[SOCKET-IO] Attempt {attempt + 1} failed for {event}: {e}")
                if attempt == retries - 1:
                    self.retry_count[event] = self.retry_count.get(event, 0) + 1
                    return False
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return False
    
    async def emit_file_event(self, event_type: str, filename: str, **kwargs):
        """Emit file-related events with standard format."""
        payload = {
            "pipeline_id": self.pipeline_id,
            "file": {"name": filename, **kwargs.get("file_info", {})},
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        return await self.emit_with_retry(f'file:{event_type}', payload)
```

This event system provides comprehensive real-time updates while maintaining compatibility with existing code patterns.