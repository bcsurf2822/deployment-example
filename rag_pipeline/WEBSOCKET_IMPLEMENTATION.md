# WebSocket Implementation for RAG Pipeline

## Overview

The RAG pipeline now includes Socket.IO WebSocket support for real-time status updates. This implementation follows the specification in `/spec/resources/websockets/rag_pipeline/02-server-setup.md`.

## Features Implemented

### 1. Socket.IO Server Integration
- **File**: `status_server.py`
- **Port**: 8004 (WebSocket server runs on HTTP port + 1)
- **Technology**: python-socketio with eventlet backend
- **Async Support**: Full async/await support with threading compatibility

### 2. Event System
The `PipelineStatus` class now emits WebSocket events for:
- `pipeline:status` - General status updates
- `pipeline:file_processing_started` - File processing begins
- `pipeline:file_completed` - File successfully processed
- `pipeline:file_failed` - File processing failed

### 3. Namespace Support
Three namespaces are configured:
- `/google_drive` - Google Drive pipeline events
- `/local_files` - Local Files pipeline events  
- `/pipeline` - General pipeline events

### 4. CORS Configuration
Environment-based CORS settings:
- **Development**: `localhost:3000`, `127.0.0.1:3000`
- **Production**: Configure via `ENVIRONMENT` variable

## Technical Implementation

### Server Architecture
- **HTTP Server**: Port 8003 (existing functionality)
- **WebSocket Server**: Port 8004 (new Socket.IO server)
- **Integration**: Both servers run in separate threads
- **Health Check**: Enhanced to include WebSocket status

### Event Emission
```python
# Status update with WebSocket emission
pipeline_status.update(status="running", pipeline_type="google_drive")

# File processing events
pipeline_status.add_processing_file("document.pdf", "12345")
pipeline_status.complete_file("document.pdf", success=True)
```

### Client Connection
```javascript
// Connect to WebSocket server
const socket = io("ws://localhost:8004", {
  transports: ["websocket", "polling"]
});

// Subscribe to namespace
const googleDriveSocket = io("ws://localhost:8004/google_drive");
```

## Configuration

### Environment Variables
- `ENVIRONMENT` - Set to "production" for production CORS settings
- `SOCKET_IO_TRANSPORTS` - Available transports (websocket,polling)

### Docker Integration
- **Ports Exposed**: 8003 (HTTP), 8004 (WebSocket)  
- **Environment**: `SOCKET_IO_TRANSPORTS=websocket,polling`
- **Health Check**: Updated to monitor both servers

## Dependencies Added
```
python-socketio>=5.8.0
eventlet>=0.33.0
```

## Testing

### Manual Testing
Run the test script:
```bash
cd rag_pipeline
python test_websocket.py
```

This will:
1. Start both HTTP and WebSocket servers
2. Simulate status updates and file processing
3. Display connection information
4. Keep servers running for client testing

### Connection Endpoints
- **HTTP Status**: `http://localhost:8003/status`
- **Health Check**: `http://localhost:8003/health`  
- **WebSocket**: `ws://localhost:8004/socket.io/`

### Event Testing
Connect a Socket.IO client to test real-time events:
```javascript
socket.on("pipeline:status", (data) => {
  console.log("Status update:", data);
});

socket.on("pipeline:file_processing_started", (data) => {
  console.log("File processing started:", data);
});
```

## Integration with Frontend

The frontend can now connect to `ws://localhost:8004/socket.io/` and subscribe to:
- Status updates for real-time pipeline monitoring
- File processing events for live upload feedback
- Namespace-specific events based on pipeline type

## Production Deployment

In production:
1. Configure proper CORS origins in environment
2. Ensure ports 8003 and 8004 are accessible
3. Use SSL/TLS termination for secure WebSocket connections
4. Monitor both HTTP and WebSocket server health

## Phase 1 Complete ✅

The backend WebSocket server is now fully implemented with:
- ✅ Socket.IO integration with existing HTTP server
- ✅ Real-time event emission for status updates
- ✅ Namespace configuration for different pipeline types  
- ✅ CORS and environment configuration
- ✅ Docker integration with port exposure
- ✅ Enhanced health checking
- ✅ Test script for verification

Next phase: Frontend WebSocket client integration.