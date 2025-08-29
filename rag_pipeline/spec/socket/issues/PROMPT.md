# WebSocket Message Routing Issue: Processing Notifications Not Reaching Frontend

## Problem Summary
The WebSocket server is incorrectly routing processing status notifications from the Google Drive RAG pipeline. Instead of forwarding these notifications to the frontend client (UploadQueue.tsx), the server is broadcasting them to all connected clients, including sending them back to the Google Drive service itself. This prevents the frontend from receiving and displaying real-time processing status updates.

## Current Architecture
- **Frontend (Next.js)**: Socket client that uploads files and expects processing status updates
- **Socket Server**: Central hub for WebSocket communications (port 8002)
- **Google Drive RAG Pipeline**: Socket client that processes files and emits status updates
- **Local Files RAG Pipeline**: Another socket client for local file processing

## Evidence from Logs

### Socket Connection IDs:
- **Frontend/UploadQueue**: `UjDooe-36iZAMV8mAAAE` 
- **Google Drive Pipeline**: `xjhCZX89rj3YKUyyAAAA` (main connection ID: `431LlOJhOtK-8_W5AAAB`)
- **Local Files Pipeline**: `omnhhJczXslb6v8IAAAC`

### Problematic Message Flow:

1. **Upload Complete Event (Working Correctly)**
   - Line 39-42: Frontend emits `upload-complete` with file details
   - Line 43-48: Google Drive receives the event and starts processing
   - Line 54-67: Socket server broadcasts to all clients

2. **Processing Started Event (BROKEN)**
   - Line 71-77: Google Drive emits `processing-started` to socket server
   - Line 88-97: Socket server acknowledges and broadcasts to ALL clients
   - Line 98-105: **PROBLEM**: Google Drive receives its own `processing-started` event back
   - **MISSING**: Frontend never logs receiving `processing-started` event

3. **Processing Complete Event (BROKEN)**
   - Line 145-154: Google Drive emits `processing-complete` 
   - Line 155-173: Socket server broadcasts to all clients
   - Line 174-181: **PROBLEM**: Google Drive receives its own event back
   - **MISSING**: Frontend never logs receiving the event

## Expected Behavior

### Correct Message Flow:
```
1. Frontend → Socket Server: "upload-complete" 
2. Socket Server → Google Drive: "upload-complete" (trigger processing)
3. Google Drive → Socket Server: "processing-started"
4. Socket Server → Frontend: "processing-started" (update UI)
5. Google Drive → Socket Server: "processing-complete"  
6. Socket Server → Frontend: "processing-complete" (update UI)
```

### What Frontend Expects (from UploadQueue.tsx):
- Lines 42-51: Listens for `processing-started` to update status to "processing"
- Lines 53-61: Listens for `processing-complete` to update status to "success"
- Lines 63-73: Listens for `processing-failed` to update status to "error"

## Actual Behavior

The socket server is using a broadcast pattern that sends messages to ALL connected clients:
- Line 61: `emitting event "upload-complete" to all [/]`
- Line 89: `emitting event "processing-started" to all [/]`
- Line 165: `emitting event "processing-complete" to all [/]`

This causes:
1. Google Drive to receive its own processing events back (creating potential loops)
2. Frontend never receives the processing status updates it needs
3. UI remains stuck showing "Upload complete!" instead of processing status

## Root Cause Analysis

The socket server appears to be using:
```python
socket.emit('event-name', data, broadcast=True)  # Sends to ALL clients
```

Instead of targeted emission:
```python
# Should identify the original requester and emit specifically to them
socket.to(frontend_socket_id).emit('processing-started', data)
```

## Required Fix

The socket server needs to:

1. **Track client types/roles** when they connect
   - Frontend clients (web browsers)
   - RAG pipeline clients (Google Drive, Local Files)

2. **Implement proper message routing**:
   - When receiving processing events from RAG pipelines → Forward ONLY to frontend clients
   - When receiving upload events from frontend → Forward ONLY to appropriate RAG pipeline
   - Avoid broadcasting processing status events to all clients

3. **Consider implementing rooms or namespaces**:
   - `/frontend` namespace for web clients
   - `/pipeline` namespace for RAG processors
   - Or use Socket.IO rooms to group clients by type

## Files to Review/Modify

1. **Socket Server** (`rag_pipeline/socket_server/main.py` or similar)
   - Review the event handlers for `processing-started`, `processing-complete`, `processing-failed`
   - Check how `broadcast=True` or `emit('all')` is being used
   - Implement client identification and targeted routing

2. **Google Drive Pipeline** (`rag_pipeline/Google_Drive/`)
   - Verify it's correctly emitting events (appears to be working)
   - Ensure it's not acting on its own emitted events

3. **Frontend** (`frontend/components/rag-pipelines/UploadQueue.tsx`)
   - Already has correct event listeners (lines 76-78)
   - Just needs to actually receive the events

## Testing Verification

After fixing, verify:
1. Frontend console shows `[UPLOAD-QUEUE] Received processing-started:` logs
2. Frontend console shows `[UPLOAD-QUEUE] Received processing-complete:` logs
3. Google Drive pipeline does NOT receive its own events back
4. UI correctly transitions through: uploading → processing → success states
5. No duplicate processing or infinite loops occur

## Additional Context

The issue appears consistently across multiple processing cycles in the logs (the file is processed twice, showing the same routing problem both times). The acknowledgment pattern (`processing_started_acknowledged`, `processing_complete_acknowledged`) suggests the server knows it received the events but is routing them incorrectly.