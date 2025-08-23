# Migration Guide: HTTP Polling to WebSocket

## Overview

This guide provides a step-by-step migration path from the current HTTP polling architecture to real-time WebSocket communication using Socket.IO.

## Pre-Migration Checklist

### 1. Environment Verification

**Required Dependencies**:
```bash
# Python backend
pip install "python-socketio[asyncio]>=5.10.0"

# TypeScript frontend  
npm install socket.io-client@^4.7.0
```

**Environment Variables**:
```bash
# Backend
SOCKET_IO_PORT=8103
SOCKET_IO_CORS_ORIGIN=http://localhost:3000
RAG_PIPELINE_ID=auto-generated-if-not-set

# Frontend
NEXT_PUBLIC_SOCKET_IO_URL=http://localhost:8103
NEXT_PUBLIC_SOCKET_TIMEOUT=5000
```

**Port Availability**:
- Ensure port 8103 is available for Socket.IO server
- Update Docker Compose port mappings
- Configure firewall rules if necessary

### 2. Backup Current Implementation

```bash
# Create backup of current components
cp components/rag-pipelines/RAGPipelineStatus.tsx components/rag-pipelines/RAGPipelineStatus.backup.tsx
cp app/api/rag-status/route.ts app/api/rag-status/route.backup.ts
cp rag_pipeline/status_server.py rag_pipeline/status_server.backup.py
```

## Phase 1: Backend WebSocket Integration

### Step 1.1: Install Python Dependencies

```bash
cd rag_pipeline
pip install "python-socketio[asyncio]>=5.10.0"

# Update requirements.txt
echo "python-socketio[asyncio]>=5.10.0" >> requirements.txt
```

### Step 1.2: Enhance Status Server

**File**: `rag_pipeline/status_server.py`

**Changes**:
1. Add Socket.IO imports at the top
2. Create Socket.IO server instance
3. Add event handlers for connection management
4. Integrate with existing PipelineStatus class
5. Start Socket.IO server alongside HTTP server

**Verification**:
```bash
# Test the status server with WebSocket support
cd rag_pipeline
python status_server.py

# In another terminal, check both endpoints
curl http://localhost:8003/health  # HTTP endpoint
curl http://localhost:8103/health  # Socket.IO endpoint (if implemented)
```

### Step 1.3: Update Pipeline Components

**Files to modify**:
- `rag_pipeline/Google_Drive/main.py`
- `rag_pipeline/Local_Files/main.py`
- `rag_pipeline/supabase_status.py`

**Changes**:
1. Import and initialize event handler
2. Add event emission to file processing methods
3. Connect to pipeline status for automatic events

**Verification**:
```bash
# Test Google Drive pipeline with events
cd rag_pipeline/Google_Drive
python main.py --single-run

# Check status server logs for Socket.IO events
```

### Step 1.4: Update Docker Configuration

**File**: `docker-compose.dev.yml`

```yaml
services:
  rag-google-drive-dev:
    ports:
      - "8003:8003"   # HTTP status server
      - "8103:8103"   # Socket.IO server
    environment:
      - SOCKET_IO_CORS_ORIGIN=http://localhost:3000
      - RAG_PIPELINE_ID=gdrive-dev
```

**Verification**:
```bash
# Test Docker setup
python deploy.py --mode dev --with-rag

# Check port accessibility
curl http://localhost:8003/status
curl http://localhost:8103/health
```

## Phase 2: Frontend WebSocket Integration

### Step 2.1: Install Frontend Dependencies

```bash
cd frontend
npm install socket.io-client@^4.7.0

# Optional: Add zod for runtime validation
npm install zod
```

### Step 2.2: Create WebSocket Infrastructure

**New files to create**:
1. `lib/socket.ts` - Socket.IO client
2. `lib/types/socket.ts` - TypeScript interfaces
3. `lib/socket-health.ts` - Health monitoring
4. `lib/socket-fallback.ts` - Fallback handling

**Implementation order**:
1. Start with basic Socket.IO client
2. Add TypeScript type definitions
3. Implement connection management
4. Add health monitoring and fallback

**Verification**:
```bash
# Test TypeScript compilation
npm run build

# Check for type errors
npx tsc --noEmit
```

### Step 2.3: Create Socket Context Provider

**File**: `components/providers/SocketProvider.tsx`

**Implementation steps**:
1. Create React context with reducer
2. Implement Socket.IO connection logic
3. Add event handlers for pipeline events
4. Integrate health monitoring
5. Export custom hooks

**Verification**:
```tsx
// Test component to verify context
function TestSocket() {
  const { state, connectionHealth } = useSocket();
  return (
    <div>
      <p>Connected: {state.isConnected ? 'Yes' : 'No'}</p>
      <p>Health: {connectionHealth.isHealthy ? 'Good' : 'Poor'}</p>
    </div>
  );
}
```

### Step 2.4: Update RAG Status Component

**File**: `components/rag-pipelines/RAGPipelineStatus.tsx`

**Migration approach**:
1. Keep existing HTTP logic as fallback
2. Add WebSocket event listeners
3. Create UI for connection status
4. Implement real-time file progress
5. Add manual connection controls

**Testing**:
```bash
# Start development server
npm run dev

# Test in browser at http://localhost:3000/rag-pipelines
```

## Phase 3: API Enhancement and Integration

### Step 3.1: Update Existing HTTP Endpoint

**File**: `app/api/rag-status/route.ts`

**Changes**:
1. Add WebSocket availability check
2. Include WebSocket connection info in response
3. Optimize caching for WebSocket-enabled scenarios
4. Add fallback mode indicators

**New response fields**:
```typescript
interface ResponseData {
  // ... existing fields ...
  websocket_available: boolean;
  websocket_url?: string;
  websocket_namespaces?: string[];
  fallback_mode: boolean;
}
```

### Step 3.2: Create WebSocket Info Endpoint

**New file**: `app/api/socket/info/route.ts`

**Purpose**:
- Check WebSocket server availability
- Return connection configuration
- Provide health status
- Enable dynamic fallback decisions

### Step 3.3: Create Health Check Endpoint

**New file**: `app/api/health/route.ts`

**Purpose**:
- Overall system health monitoring
- WebSocket server status
- Database connectivity
- Pipeline component health

## Phase 4: Dual-Mode Operation (Transition Period)

### Step 4.1: Feature Flag Implementation

**Environment variable**:
```bash
NEXT_PUBLIC_WEBSOCKET_ENABLED=true  # Enable WebSocket mode
NEXT_PUBLIC_FALLBACK_ENABLED=true   # Allow HTTP fallback
```

**Component logic**:
```typescript
const useWebSocket = process.env.NEXT_PUBLIC_WEBSOCKET_ENABLED === 'true';
const allowFallback = process.env.NEXT_PUBLIC_FALLBACK_ENABLED === 'true';

if (useWebSocket) {
  // Try WebSocket first
  connectToWebSocket()
    .catch(() => {
      if (allowFallback) {
        enableHttpPolling();
      }
    });
}
```

### Step 4.2: A/B Testing Setup

**User-based routing**:
```typescript
function getConnectionMode(userId: string): 'websocket' | 'http' {
  // Route 50% of users to WebSocket
  const hash = simpleHash(userId);
  return hash % 2 === 0 ? 'websocket' : 'http';
}
```

### Step 4.3: Monitoring and Metrics

**Key metrics to track**:
- WebSocket connection success rate
- Event delivery latency
- Fallback activation frequency
- User experience improvements
- Error rates by connection type

## Phase 5: Full Migration and Cleanup

### Step 5.1: Gradual Rollout

**Week 1**: 25% WebSocket, 75% HTTP
```bash
WEBSOCKET_ROLLOUT_PERCENTAGE=25
```

**Week 2**: 50% WebSocket, 50% HTTP
```bash
WEBSOCKET_ROLLOUT_PERCENTAGE=50
```

**Week 3**: 75% WebSocket, 25% HTTP
```bash
WEBSOCKET_ROLLOUT_PERCENTAGE=75
```

**Week 4**: 100% WebSocket (with HTTP fallback)
```bash
WEBSOCKET_ROLLOUT_PERCENTAGE=100
```

### Step 5.2: Performance Validation

**Success criteria**:
- WebSocket connection success rate > 95%
- Event latency < 100ms average
- Fallback rate < 5%
- Zero data loss during connection switches
- Improved user satisfaction scores

**Rollback conditions**:
- Connection success rate < 90%
- Event latency > 500ms average
- Error rate increase > 50%
- Critical functionality breaks

### Step 5.3: Legacy Code Removal

**After successful validation**:

1. Remove old polling logic from frontend:
```typescript
// Remove from RAGPipelineStatus.tsx
const DISABLE_RAG_POLLING = process.env.NEXT_PUBLIC_DISABLE_RAG_POLLING === 'true';

// Delete polling interval logic
let pollInterval = MIN_POLL_INTERVAL;
```

2. Simplify HTTP endpoint:
```typescript
// Simplify /api/rag-status/route.ts
// Remove polling-specific optimizations
// Keep basic HTTP endpoint for health checks
```

3. Clean up feature flags:
```bash
# Remove from environment
unset NEXT_PUBLIC_WEBSOCKET_ENABLED
unset NEXT_PUBLIC_FALLBACK_ENABLED
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. WebSocket Connection Failures

**Symptoms**:
- "Connection failed" errors
- Automatic fallback to HTTP
- High reconnection attempts

**Debug steps**:
```bash
# Check Socket.IO server
curl http://localhost:8103/health

# Check port accessibility
netstat -tulpn | grep 8103

# Review server logs
docker logs <container-id> | grep SOCKET-IO
```

**Solutions**:
- Verify port configuration
- Check firewall rules
- Validate CORS settings
- Review proxy configuration

#### 2. Event Delivery Issues

**Symptoms**:
- Missing real-time updates
- Delayed file status changes
- Inconsistent UI state

**Debug steps**:
```bash
# Check event emission in backend
# Look for "[SOCKET-IO] Emitted" logs

# Monitor frontend event reception
# Use browser DevTools WebSocket tab

# Verify namespace configuration
```

**Solutions**:
- Validate event payload format
- Check namespace subscriptions
- Review error handling logic
- Verify type definitions match

#### 3. Performance Issues

**Symptoms**:
- High memory usage
- Slow connection times
- Event processing delays

**Debug steps**:
```bash
# Monitor resource usage
docker stats <container-id>

# Check connection counts
# Review health endpoint metrics

# Profile frontend performance
# Use React DevTools Profiler
```

**Solutions**:
- Optimize event frequency
- Implement event batching
- Add connection pooling
- Reduce payload sizes

#### 4. Fallback Not Working

**Symptoms**:
- No HTTP fallback when WebSocket fails
- Stuck in connecting state
- Missing status updates

**Debug steps**:
```typescript
// Check fallback handler configuration
const fallbackHandler = new SocketFallbackHandler({
  enablePolling: true,
  pollingInterval: 10000,
  maxFailures: 3
});

// Verify fallback triggers
fallbackHandler.handleConnectionFailure();
```

**Solutions**:
- Review fallback configuration
- Check HTTP endpoint availability
- Validate error detection logic
- Test manual fallback trigger

## Rollback Plan

### Quick Rollback (< 5 minutes)

```bash
# Disable WebSocket via environment variable
export NEXT_PUBLIC_WEBSOCKET_ENABLED=false

# Restart frontend service
npm run build && npm run start

# Or use Docker restart
docker-compose restart frontend-dev
```

### Full Rollback (< 30 minutes)

```bash
# Restore backup files
cp components/rag-pipelines/RAGPipelineStatus.backup.tsx components/rag-pipelines/RAGPipelineStatus.tsx
cp app/api/rag-status/route.backup.ts app/api/rag-status/route.ts
cp rag_pipeline/status_server.backup.py rag_pipeline/status_server.py

# Remove WebSocket dependencies
npm uninstall socket.io-client
pip uninstall python-socketio

# Restart all services
python deploy.py --down --mode dev --with-rag
python deploy.py --mode dev --with-rag
```

## Post-Migration Validation

### Functional Testing

```bash
# Test WebSocket connection
curl -H "Upgrade: websocket" http://localhost:8103/socket.io/

# Test HTTP fallback
NEXT_PUBLIC_WEBSOCKET_ENABLED=false npm run dev

# Test pipeline events
# Upload test file and verify real-time updates

# Test error scenarios
# Kill WebSocket server and verify fallback
```

### Performance Testing

```bash
# Load test WebSocket connections
# Use tools like Artillery or custom scripts

# Monitor resource usage
# Check for memory leaks over time

# Test concurrent users
# Verify scalability improvements
```

### User Acceptance Testing

- Real-time status updates work correctly
- File processing progress is visible immediately
- Connection issues are handled gracefully
- Overall experience is improved over polling

This migration guide ensures a smooth transition with minimal risk and maximum reliability.