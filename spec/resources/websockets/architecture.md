# WebSocket Architecture for RAG Pipeline

## Architecture Overview

This document describes the complete WebSocket architecture for real-time communication between RAG pipeline components and the frontend application.

## System Architecture Diagram

```
┌─────────────────┐    WebSocket     ┌─────────────────┐    Events    ┌─────────────────┐
│                 │ ◄─────────────► │                 │ ◄─────────► │                 │
│   Frontend      │    Socket.IO    │  Status Server  │   Direct    │  RAG Pipeline   │
│   (Next.js)     │                 │   (Python)      │   Calls     │   Components    │
│                 │                 │                 │             │                 │
└─────────────────┘                 └─────────────────┘             └─────────────────┘
         │                                   │                               │
         │ HTTP Fallback                     │ Database                      │ File Events
         ▼                                   ▼                               ▼
┌─────────────────┐                 ┌─────────────────┐             ┌─────────────────┐
│                 │                 │                 │             │                 │
│  /api/rag-status│                 │   Supabase      │             │  Drive Watcher  │
│  (HTTP Endpoint)│                 │   Database      │             │  Local Watcher  │
│                 │                 │                 │             │                 │
└─────────────────┘                 └─────────────────┘             └─────────────────┘
```

## Component Responsibilities

### 1. Frontend (Next.js Application)

**Primary Role**: User interface with real-time status updates

**Key Components**:
- Socket.IO client manager
- React context for state management  
- Real-time UI components
- HTTP fallback handling
- Connection health monitoring

**Technologies**:
- Next.js 15 with App Router
- React 19 with hooks and context
- Socket.IO client v4.7+
- TypeScript for type safety

### 2. Status Server (Python)

**Primary Role**: WebSocket communication hub and HTTP bridge

**Key Components**:
- Socket.IO AsyncServer for WebSocket handling
- HTTP server for legacy support and health checks
- Event routing between pipeline components and clients
- Connection management and namespace handling
- Health monitoring and metrics

**Technologies**:
- Python 3.11+ with asyncio
- python-socketio for WebSocket server
- Threading for HTTP/WebSocket coexistence
- JSON for message serialization

### 3. RAG Pipeline Components

**Primary Role**: File processing and event generation

**Key Components**:
- Google Drive file watcher
- Local files watcher
- Database integration layer
- Event emission on processing lifecycle
- Status persistence and recovery

**Technologies**:
- Python asyncio for non-blocking operations
- Supabase for state persistence
- OpenAI API for embeddings
- File processing libraries (pypdf, etc.)

### 4. Database Layer (Supabase)

**Primary Role**: Persistent state and fallback data source

**Key Components**:
- Pipeline state tracking
- File processing history
- Heartbeat monitoring
- Known files registry
- Real-time subscriptions (if needed)

## Communication Patterns

### 1. Real-Time Event Flow

```
File Change Detection → RAG Component → Status Server → Frontend UI
                                           │
                                           ▼
                                      Database Update
```

**Event Types**:
- `pipeline:online` - Pipeline startup
- `pipeline:offline` - Pipeline shutdown
- `file:processing` - File processing started
- `file:progress` - Processing progress update
- `file:completed` - File successfully processed
- `file:failed` - File processing failed
- `status:update` - General status changes
- `heartbeat` - Keep-alive signals

### 2. HTTP Fallback Pattern

```
Frontend Request → /api/rag-status → Supabase Query → JSON Response
      ▲                                                      │
      └──────────────── Polling Loop ◄────────────────────────┘
```

**Fallback Triggers**:
- WebSocket connection failure
- Server unavailability
- Network restrictions
- User preference/configuration

### 3. Connection Management

```
Frontend App Start
       │
       ▼
Check WebSocket Availability (/api/socket/info)
       │
       ├─ Available ──► Connect Socket.IO ──► Subscribe to Events
       │                       │
       │                       ├─ Success ──► Real-time Updates
       │                       └─ Failure ──► Fallback to HTTP
       │
       └─ Unavailable ──► HTTP Polling Mode
```

## Namespace Architecture

### Pipeline-Specific Namespaces

```
Socket.IO Server
├─ /google_drive (namespace)
│  ├─ pipeline:online
│  ├─ file:processing  
│  ├─ file:completed
│  └─ file:failed
│
└─ /local_files (namespace)
   ├─ pipeline:online
   ├─ file:processing
   ├─ file:completed  
   └─ file:failed
```

**Benefits**:
- Isolated event streams per pipeline type
- Selective subscription capabilities
- Reduced noise and improved performance
- Independent scaling and monitoring

### Room-Based Organization

```
Namespace: /google_drive
├─ Room: pipeline:gdrive-prod-001
├─ Room: pipeline:gdrive-dev-002  
└─ Room: admin:monitoring
```

**Use Cases**:
- Multiple pipeline instances
- Development vs production separation
- Admin monitoring and debugging
- Client-specific filtering

## Data Flow Architecture

### 1. File Processing Lifecycle

```sequence
participant FC as File Component
participant SS as Status Server  
participant FE as Frontend
participant DB as Database

FC->>SS: file:processing event
SS->>FE: WebSocket broadcast
SS->>DB: Status update
FC->>SS: file:progress (20%)
SS->>FE: Progress update
FC->>SS: file:progress (50%)  
SS->>FE: Progress update
FC->>SS: file:completed
SS->>FE: Completion event
SS->>DB: Final status
```

### 2. Connection Health Monitoring

```sequence
participant FE as Frontend
participant SS as Status Server
participant HM as Health Monitor

FE->>SS: Connect WebSocket
SS-->>FE: Connection established
loop Every 30 seconds
    SS->>FE: heartbeat event
    FE->>HM: Update health metrics
end
Note over FE,HM: Track latency, reconnects, errors
```

### 3. Error Handling and Recovery

```sequence
participant FE as Frontend
participant SS as Status Server
participant FB as Fallback Handler

FE->>SS: WebSocket connection
SS--xFE: Connection fails
FE->>FB: Trigger fallback
FB->>FE: Enable HTTP polling
loop Until WebSocket available
    FB->>FE: HTTP status updates
    FB->>SS: Check availability
end
SS-->>FB: WebSocket restored
FB->>FE: Switch back to WebSocket
```

## Scalability Considerations

### 1. Horizontal Scaling

**Status Server Scaling**:
- Multiple Socket.IO server instances
- Load balancer with sticky sessions
- Redis adapter for cross-instance communication
- Database connection pooling

**Frontend Scaling**:
- CDN for static assets
- Multiple Next.js instances
- Shared WebSocket connection pools
- Client-side connection management

### 2. Performance Optimization

**Backend Optimizations**:
- Event batching for high-frequency updates
- Connection pooling and reuse
- Efficient JSON serialization
- Memory usage monitoring

**Frontend Optimizations**:
- Event debouncing and throttling
- Selective component re-rendering
- Connection health monitoring
- Lazy loading of status components

### 3. Resource Management

**Memory Management**:
- Event listener cleanup
- Connection garbage collection
- State normalization
- Cache size limits

**Network Optimization**:
- Message compression
- Transport selection (WebSocket vs polling)
- Connection keep-alive tuning
- Bandwidth usage monitoring

## Security Architecture

### 1. Authentication and Authorization

```
Frontend Authentication
       │
       ▼
JWT Token Validation
       │
       ▼
WebSocket Handshake with Token
       │
       ▼
Pipeline-Specific Authorization
       │
       ▼
Event Subscription Permissions
```

### 2. Data Validation

**Input Validation**:
- Event payload schema validation
- Message size limits
- Rate limiting per connection
- Sanitization of user inputs

**Output Filtering**:
- User-specific data filtering
- Permission-based event routing
- Sensitive data redaction
- Audit logging

### 3. Network Security

**Transport Security**:
- WSS (WebSocket Secure) in production
- Certificate validation
- CORS configuration
- Origin verification

**Application Security**:
- Event injection prevention
- DoS protection via rate limiting
- Connection timeout management
- Resource usage limits

## Monitoring and Observability

### 1. Metrics Collection

**Connection Metrics**:
- Active connection count
- Connection duration statistics
- Reconnection frequency
- Transport type distribution

**Event Metrics**:
- Event emission rates
- Event processing latency
- Failed event delivery count
- Queue depth monitoring

**Performance Metrics**:
- Memory usage per connection
- CPU utilization patterns
- Network bandwidth usage
- Database query performance

### 2. Health Checks

**System Health**:
- WebSocket server availability
- Database connectivity
- Pipeline component health
- Overall system status

**API Endpoints**:
- `/api/health` - Overall system health
- `/api/socket/info` - WebSocket availability
- `/api/socket/test` - Connection testing
- Status server `/health` - Component health

### 3. Alerting and Logging

**Critical Alerts**:
- WebSocket server unavailability
- High connection failure rates
- Database connectivity issues
- Pipeline processing failures

**Logging Strategy**:
- Structured JSON logging
- Request/response correlation
- Error context preservation
- Performance timing logs

## Deployment Architecture

### 1. Development Environment

```
Local Development
├─ Frontend (localhost:3000)
├─ Status Server (localhost:8103)  
├─ RAG Components (localhost:8004-8005)
└─ Database (Supabase Cloud)
```

### 2. Production Environment

```
Production Deployment
├─ Frontend (CDN + Next.js servers)
├─ Load Balancer (WebSocket support)
├─ Status Server Cluster (multiple instances)
├─ RAG Pipeline Containers
└─ Database Cluster (High Availability)
```

### 3. Container Configuration

**Docker Compose Integration**:
- WebSocket port exposure (8103)
- Health check configuration
- Environment variable management
- Service dependency declaration

**Kubernetes Deployment** (Future):
- StatefulSet for status servers
- Service mesh for internal communication
- Ingress controller with WebSocket support
- Horizontal Pod Autoscaler

This architecture provides a robust, scalable foundation for real-time RAG pipeline monitoring with graceful fallback capabilities and comprehensive observability.