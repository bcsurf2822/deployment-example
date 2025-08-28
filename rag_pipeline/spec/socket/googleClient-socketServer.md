# Google Drive Watcher - Socket Server Integration

**Feature**: Real-time File Processing via WebSocket Notifications  
**Date**: August 28, 2025  
**Status**: Successfully Implemented

## Overview
Established bidirectional WebSocket connection between the Google Drive watcher client and the RAG pipeline socket server to enable immediate processing of uploaded files, while maintaining the existing timer-based fallback system for manual Google Drive uploads.

## Architecture Components

### 1. Socket Server (`rag_pipeline/socket_server.py`)
- Running on port 8002
- Uses Socket.IO with FastAPI/ASGI
- Handles multiple client connections
- Broadcasts `upload-complete` events to all connected clients

### 2. Google Drive Watcher Client (`rag_pipeline/Google_Drive/drive_watcher.py`)
- Connects to socket server via `socketio.Client`
- Listens for `upload-complete` events
- Processes files immediately upon notification
- Maintains timer-based checking as fallback (60-second intervals)

### 3. Frontend Integration
- Emits `upload-complete` event after successful Google Drive upload
- Includes file metadata: fileName, googleDriveId, fileSize

## Implementation Details

### Connection Setup
```python
# In main.py - Socket client setup alongside timer loop
watcher.setup_socket_client()

# Socket connection uses Docker service names
RAG_SOCKET_URL=http://rag-socket-server-dev:8002
```

### Event Flow
1. User uploads file via frontend
2. Frontend emits `upload-complete` to socket server
3. Socket server broadcasts to all connected clients
4. Google Drive watcher receives event and processes immediately
5. Timer-based check runs 60 seconds later, skips already-processed files

### Key Features Implemented

#### 1. Socket Client Connection
- Auto-connects on startup
- Identifies itself to server as "google-drive-watcher"
- Handles connection/disconnection gracefully
- Runs in separate daemon thread

#### 2. Immediate Processing
- `process_file_immediately()` method for instant processing
- Fetches file metadata directly from Google Drive API
- Validates file location and modification time
- Prevents double-processing with thread-safe locks

#### 3. Double-Processing Prevention
- `processing_files` set with thread-safe Lock()
- Files marked as "processing" before any operation
- Timer checks skip files already being processed
- ModifiedTime comparison prevents reprocessing unchanged files

#### 4. Docker Integration
- Added `RAG_SOCKET_URL` environment variable to docker-compose.dev.yml
- Service dependencies ensure socket server starts first
- Container networking enables inter-service communication

## Challenges Resolved

### Issue 1: Socket Connection Not Established
**Problem**: Google Drive watcher wasn't connecting to socket server  
**Cause**: Missing `RAG_SOCKET_URL` environment variable in Docker configuration  
**Solution**: Added environment variable to both Google Drive and Local Files services in docker-compose.dev.yml

### Issue 2: Event Name Mismatch
**Problem**: Frontend sending "upload-complete" but server expecting different format  
**Cause**: Incorrect decorator syntax `@sio.event("upload-complete")` instead of `@sio.on("upload-complete")`  
**Solution**: Fixed decorator syntax in socket_server.py

### Issue 3: Socket Client Never Called
**Problem**: `setup_socket_client()` was never being invoked  
**Cause**: main.py was calling `check_for_changes()` directly instead of using `watch_for_changes()`  
**Solution**: Added explicit `watcher.setup_socket_client()` call before the timer loop

### Issue 4: Self-Blocking Processing
**Problem**: Files marked as "already being processed" on first attempt  
**Cause**: `process_file_immediately()` added file to `processing_files` set, then `process_file()` checked the same set and skipped  
**Solution**: Temporarily remove file from set before calling `process_file()`

## Testing Results

Successfully tested end-to-end flow:
1. File upload triggers socket notification
2. Google Drive watcher receives event immediately
3. File is processed without waiting for timer
4. Timer-based check correctly skips already-processed file
5. System maintains reliability with dual processing modes

## Benefits Achieved

1. **Instant Processing**: Files process immediately after upload (no 60-second wait)
2. **Maintained Reliability**: Timer-based system remains as backup for manual uploads
3. **Thread Safety**: Proper locking prevents race conditions
4. **Zero Duplication**: Smart state management prevents duplicate processing
5. **Graceful Degradation**: Socket failures don't break timer-based processing

## Future Enhancements

- Add WebSocket authentication for security
- Implement reconnection logic with exponential backoff
- Add progress notifications during file processing
- Extend to Local Files watcher for consistency
- Add metrics for socket vs timer processing rates