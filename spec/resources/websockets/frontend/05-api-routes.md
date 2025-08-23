# API Route Modifications for Socket.IO Integration

## 1. Update Existing RAG Status Route

### Modify `app/api/rag-status/route.ts`

The existing HTTP endpoint should be enhanced to work alongside Socket.IO:

```typescript
import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

interface PipelineState {
  pipeline_id: string;
  pipeline_type: string;
  server_status: string;
  last_heartbeat: string | null;
  status_details: Record<string, unknown> | null;
  last_check_time: string | null;
  known_files: Record<string, unknown> | null;
  last_run: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface FileInfo {
  name: string;
  id?: string;
  started_at: string;
  completed_at?: string;
}

interface ResponseData {
  status: string;
  pipelines: Array<{
    pipeline_id: string;
    pipeline_type: string;
    server_status: string;
    last_heartbeat: string | null;
    status_details: Record<string, unknown>;
    is_active: boolean;
  }>;
  serverTime: string;
  status_details?: Record<string, unknown>;
  last_activity?: string;
  files_processing?: FileInfo[];
  files_completed?: FileInfo[];
  files_failed?: FileInfo[];
  
  // New WebSocket integration fields
  websocket_available: boolean;
  websocket_url?: string;
  websocket_namespaces?: string[];
  fallback_mode: boolean;
}

// Enhanced in-memory cache with WebSocket info
interface CachedResponse {
  data: ResponseData;
  timestamp: number;
  websocket_status: 'available' | 'unavailable' | 'unknown';
}

let cache: CachedResponse | null = null;
const CACHE_TTL = 5000; // Reduced to 5 seconds since WebSocket provides real-time updates

// Check if Socket.IO server is available
async function checkSocketIOAvailability(): Promise<boolean> {
  try {
    const socketIOUrl = process.env.NEXT_PUBLIC_SOCKET_IO_URL || 'http://localhost:8103';
    const healthResponse = await fetch(`${socketIOUrl.replace('/socket.io', '')}/health`, {
      method: 'GET',
      timeout: 2000, // 2 second timeout
      signal: AbortSignal.timeout(2000)
    });
    return healthResponse.ok;
  } catch (error) {
    console.warn('[RAG-STATUS-API] Socket.IO server not available:', error);
    return false;
  }
}

export async function GET(request: NextRequest) {
  try {
    // Check cache first
    const currentTime = Date.now();
    if (cache && (currentTime - cache.timestamp < CACHE_TTL)) {
      return NextResponse.json(cache.data);
    }

    // Get pipeline_id from query params (optional)
    const url = new URL(request.url);
    const pipelineId = url.searchParams.get("pipeline_id");
    
    // Create Supabase client with service role key
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    
    if (!supabaseUrl || !supabaseServiceKey) {
      console.error("[RAG-STATUS-API] Missing Supabase configuration");
      return NextResponse.json(
        {
          error: "Configuration error", 
          status: "error",
          message: "Supabase configuration missing",
          websocket_available: false,
          fallback_mode: true
        },
        { status: 500 }
      );
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);
    
    // Check Socket.IO availability in parallel with database query
    const [socketIOAvailable, dbResult] = await Promise.allSettled([
      checkSocketIOAvailability(),
      supabase
        .from("rag_pipeline_state")
        .select("*")
        .then(result => pipelineId ? result.eq("pipeline_id", pipelineId) : result)
    ]);

    const websocketAvailable = socketIOAvailable.status === 'fulfilled' && socketIOAvailable.value;
    
    if (dbResult.status === 'rejected') {
      console.error("[RAG-STATUS-API] Supabase query error:", dbResult.reason);
      return NextResponse.json(
        {
          error: "Database error",
          status: "error",
          message: dbResult.reason?.message || "Database query failed",
          websocket_available: websocketAvailable,
          fallback_mode: !websocketAvailable
        },
        { status: 500 }
      );
    }

    const { data, error } = dbResult.value;
    
    if (error) {
      console.error("[RAG-STATUS-API] Supabase query error:", error);
      return NextResponse.json(
        {
          error: "Database error",
          status: "error",
          message: error.message,
          websocket_available: websocketAvailable,
          fallback_mode: !websocketAvailable
        },
        { status: 500 }
      );
    }
    
    // If no data, return offline status
    if (!data || data.length === 0) {
      const offlineResponse: ResponseData = {
        status: "offline",
        pipelines: [],
        message: "No RAG pipelines found",
        serverTime: new Date().toISOString(),
        websocket_available: websocketAvailable,
        websocket_url: websocketAvailable ? process.env.NEXT_PUBLIC_SOCKET_IO_URL : undefined,
        websocket_namespaces: websocketAvailable ? ['/google_drive', '/local_files'] : undefined,
        fallback_mode: !websocketAvailable
      };
      
      return NextResponse.json(offlineResponse);
    }
    
    // Type the data
    const pipelines = data as PipelineState[];
    
    // Check for any online pipelines
    const onlinePipelines = pipelines.filter((p: PipelineState) => p.server_status === "online");
    
    // Check for stale heartbeats (more than 2 minutes old)
    const now = new Date();
    const activeOnlinePipelines = onlinePipelines.filter((p: PipelineState) => {
      if (!p.last_heartbeat) return false;
      const lastHeartbeat = new Date(p.last_heartbeat);
      const timeDiff = now.getTime() - lastHeartbeat.getTime();
      return timeDiff < 120000; // 2 minutes
    });
    
    // Enhanced debug logging
    console.log("[RAG-STATUS-API] Debug:", {
      totalPipelines: pipelines.length,
      onlinePipelines: onlinePipelines.length,
      activeOnlinePipelines: activeOnlinePipelines.length,
      websocketAvailable,
      pipelineStatuses: pipelines.map(p => ({ 
        id: p.pipeline_id, 
        status: p.server_status, 
        heartbeat: p.last_heartbeat 
      }))
    });
    
    // Prepare enhanced response
    const response: ResponseData = {
      status: activeOnlinePipelines.length > 0 ? "online" : "offline",
      pipelines: pipelines.map((p: PipelineState) => ({
        pipeline_id: p.pipeline_id,
        pipeline_type: p.pipeline_type,
        server_status: p.server_status,
        last_heartbeat: p.last_heartbeat,
        status_details: p.status_details || {},
        is_active: activeOnlinePipelines.some((ap: PipelineState) => ap.pipeline_id === p.pipeline_id),
      })),
      serverTime: new Date().toISOString(),
      
      // WebSocket integration fields
      websocket_available: websocketAvailable,
      websocket_url: websocketAvailable ? process.env.NEXT_PUBLIC_SOCKET_IO_URL : undefined,
      websocket_namespaces: websocketAvailable ? ['/google_drive', '/local_files'] : undefined,
      fallback_mode: !websocketAvailable
    };
    
    // If there are any active pipelines, include their status details
    if (activeOnlinePipelines.length > 0) {
      const primaryPipeline = activeOnlinePipelines[0];
      response.status_details = primaryPipeline.status_details || {};
      response.last_activity = primaryPipeline.status_details?.last_activity as string;
      response.files_processing = (primaryPipeline.status_details?.files_processing as FileInfo[]) || [];
      response.files_completed = (primaryPipeline.status_details?.files_completed as FileInfo[]) || [];
      response.files_failed = (primaryPipeline.status_details?.files_failed as FileInfo[]) || [];
    }
    
    // Cache the response with WebSocket status
    cache = {
      data: response,
      timestamp: Date.now(),
      websocket_status: websocketAvailable ? 'available' : 'unavailable'
    };
    
    // Set appropriate cache headers based on WebSocket availability
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (websocketAvailable) {
      // Shorter cache when WebSocket is available since real-time updates are preferred
      headers['Cache-Control'] = 'public, max-age=5, stale-while-revalidate=10';
    } else {
      // Standard cache when WebSocket is not available (fallback mode)
      headers['Cache-Control'] = 'public, max-age=10, stale-while-revalidate=30';
    }
    
    return NextResponse.json(response, { headers });
    
  } catch (error) {
    console.error("[RAG-STATUS-API] Unexpected error:", error);
    return NextResponse.json(
      {
        error: "Internal server error",
        status: "error",
        message: "Failed to fetch RAG pipeline status",
        websocket_available: false,
        fallback_mode: true
      },
      { status: 500 }
    );
  }
}

// Handle CORS preflight (unchanged)
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}
```

## 2. Create Socket.IO Connection Info Route

### New Route: `app/api/socket/info/route.ts`

```typescript
import { NextRequest, NextResponse } from "next/server";

interface SocketIOInfo {
  available: boolean;
  url?: string;
  namespaces: string[];
  transports: string[];
  version: string;
  health: 'healthy' | 'degraded' | 'unavailable';
  latency?: number;
  features: {
    realtime_updates: boolean;
    file_progress: boolean;
    auto_reconnect: boolean;
    fallback_polling: boolean;
  };
  last_checked: string;
}

// Cache Socket.IO info for 30 seconds
let socketInfoCache: { data: SocketIOInfo; timestamp: number } | null = null;
const SOCKET_INFO_CACHE_TTL = 30000; // 30 seconds

async function checkSocketIOHealth(): Promise<SocketIOInfo> {
  const baseUrl = process.env.NEXT_PUBLIC_SOCKET_IO_URL || 'http://localhost:8103';
  const healthUrl = baseUrl.replace('/socket.io', '') + '/health';
  
  try {
    const startTime = Date.now();
    const response = await fetch(healthUrl, {
      method: 'GET',
      signal: AbortSignal.timeout(5000), // 5 second timeout
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'NextJS-SocketIO-Client/1.0'
      }
    });
    
    const latency = Date.now() - startTime;
    
    if (response.ok) {
      let healthData;
      try {
        healthData = await response.json();
      } catch {
        healthData = { status: 'healthy' };
      }
      
      return {
        available: true,
        url: baseUrl,
        namespaces: ['/google_drive', '/local_files'],
        transports: ['websocket', 'polling'],
        version: '4.7.0', // Could be retrieved from server
        health: healthData.websocket_server === 'running' ? 'healthy' : 'degraded',
        latency,
        features: {
          realtime_updates: true,
          file_progress: true,
          auto_reconnect: true,
          fallback_polling: true
        },
        last_checked: new Date().toISOString()
      };
    } else {
      throw new Error(`Health check failed: ${response.status}`);
    }
  } catch (error) {
    console.warn('[SOCKET-INFO] Health check failed:', error);
    return {
      available: false,
      namespaces: [],
      transports: [],
      version: 'unknown',
      health: 'unavailable',
      features: {
        realtime_updates: false,
        file_progress: false,
        auto_reconnect: false,
        fallback_polling: true
      },
      last_checked: new Date().toISOString()
    };
  }
}

export async function GET(request: NextRequest) {
  try {
    // Check cache first
    const currentTime = Date.now();
    if (socketInfoCache && (currentTime - socketInfoCache.timestamp < SOCKET_INFO_CACHE_TTL)) {
      return NextResponse.json(socketInfoCache.data);
    }

    // Get fresh Socket.IO info
    const socketInfo = await checkSocketIOHealth();
    
    // Cache the result
    socketInfoCache = {
      data: socketInfo,
      timestamp: currentTime
    };
    
    // Set cache headers
    const headers = {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=30, stale-while-revalidate=60',
      'X-Socket-Health': socketInfo.health
    };
    
    return NextResponse.json(socketInfo, { headers });
    
  } catch (error) {
    console.error('[SOCKET-INFO] Error:', error);
    return NextResponse.json(
      {
        available: false,
        namespaces: [],
        transports: [],
        version: 'unknown',
        health: 'unavailable',
        features: {
          realtime_updates: false,
          file_progress: false,
          auto_reconnect: false,
          fallback_polling: true
        },
        last_checked: new Date().toISOString(),
        error: 'Failed to check Socket.IO availability'
      },
      { status: 503 }
    );
  }
}
```

## 3. Create WebSocket Connection Test Route

### New Route: `app/api/socket/test/route.ts`

```typescript
import { NextRequest, NextResponse } from "next/server";

interface ConnectionTestResult {
  success: boolean;
  latency?: number;
  transport?: string;
  error?: string;
  timestamp: string;
  server_info?: {
    version?: string;
    connected_clients?: number;
    uptime?: number;
  };
}

export async function POST(request: NextRequest) {
  try {
    const { pipelineType } = await request.json();
    const socketIOUrl = process.env.NEXT_PUBLIC_SOCKET_IO_URL || 'http://localhost:8103';
    
    // This would be a server-side Socket.IO connection test
    // In a real implementation, you'd use socket.io-client here
    const startTime = Date.now();
    
    // For now, simulate a connection test with HTTP health check
    const testUrl = socketIOUrl.replace('/socket.io', '') + '/health';
    const response = await fetch(testUrl, {
      method: 'GET',
      signal: AbortSignal.timeout(10000), // 10 second timeout
      headers: {
        'X-Test-Request': 'true',
        'X-Pipeline-Type': pipelineType || 'unknown'
      }
    });
    
    const latency = Date.now() - startTime;
    
    if (response.ok) {
      const healthData = await response.json();
      
      const result: ConnectionTestResult = {
        success: true,
        latency,
        transport: 'http', // Would be 'websocket' in real Socket.IO test
        timestamp: new Date().toISOString(),
        server_info: {
          version: healthData.version,
          connected_clients: healthData.connected_clients,
          uptime: healthData.uptime
        }
      };
      
      return NextResponse.json(result);
    } else {
      throw new Error(`Connection test failed: ${response.status}`);
    }
    
  } catch (error) {
    const result: ConnectionTestResult = {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    };
    
    return NextResponse.json(result, { status: 500 });
  }
}
```

## 4. Enhanced Health Check Route

### New Route: `app/api/health/route.ts`

```typescript
import { NextRequest, NextResponse } from "next/server";

interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: {
    database: {
      status: 'up' | 'down';
      latency?: number;
      error?: string;
    };
    websocket: {
      status: 'up' | 'down' | 'degraded';
      url?: string;
      latency?: number;
      connected_clients?: number;
      error?: string;
    };
    rag_pipelines: {
      google_drive: {
        status: 'online' | 'offline' | 'error';
        last_heartbeat?: string;
      };
      local_files: {
        status: 'online' | 'offline' | 'error';
        last_heartbeat?: string;
      };
    };
  };
  version: string;
  uptime: number;
}

const startTime = Date.now();

async function checkDatabaseHealth() {
  try {
    const startTime = Date.now();
    // Simple database connectivity test
    const response = await fetch(`${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/api/rag-status`);
    const latency = Date.now() - startTime;
    
    if (response.ok) {
      return { status: 'up' as const, latency };
    } else {
      throw new Error(`Database check failed: ${response.status}`);
    }
  } catch (error) {
    return { 
      status: 'down' as const, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

async function checkWebSocketHealth() {
  try {
    const socketIOUrl = process.env.NEXT_PUBLIC_SOCKET_IO_URL || 'http://localhost:8103';
    const startTime = Date.now();
    
    const response = await fetch(socketIOUrl.replace('/socket.io', '') + '/health', {
      signal: AbortSignal.timeout(5000)
    });
    
    const latency = Date.now() - startTime;
    
    if (response.ok) {
      const data = await response.json();
      return {
        status: data.websocket_server === 'running' ? 'up' as const : 'degraded' as const,
        url: socketIOUrl,
        latency,
        connected_clients: data.connected_clients
      };
    } else {
      throw new Error(`WebSocket health check failed: ${response.status}`);
    }
  } catch (error) {
    return {
      status: 'down' as const,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

async function checkRAGPipelineHealth() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/api/rag-status`);
    
    if (response.ok) {
      const data = await response.json();
      
      return {
        google_drive: {
          status: data.pipelines.find((p: any) => p.pipeline_type === 'google_drive')?.is_active ? 'online' as const : 'offline' as const,
          last_heartbeat: data.pipelines.find((p: any) => p.pipeline_type === 'google_drive')?.last_heartbeat
        },
        local_files: {
          status: data.pipelines.find((p: any) => p.pipeline_type === 'local_files')?.is_active ? 'online' as const : 'offline' as const,
          last_heartbeat: data.pipelines.find((p: any) => p.pipeline_type === 'local_files')?.last_heartbeat
        }
      };
    } else {
      throw new Error('Failed to fetch pipeline status');
    }
  } catch (error) {
    return {
      google_drive: { status: 'error' as const },
      local_files: { status: 'error' as const }
    };
  }
}

export async function GET(request: NextRequest) {
  try {
    // Run all health checks in parallel
    const [dbHealth, wsHealth, ragHealth] = await Promise.all([
      checkDatabaseHealth(),
      checkWebSocketHealth(),
      checkRAGPipelineHealth()
    ]);
    
    // Determine overall status
    let overallStatus: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    
    if (dbHealth.status === 'down') {
      overallStatus = 'unhealthy';
    } else if (wsHealth.status === 'down' || wsHealth.status === 'degraded') {
      overallStatus = 'degraded';
    } else if (ragHealth.google_drive.status === 'error' && ragHealth.local_files.status === 'error') {
      overallStatus = 'degraded';
    }
    
    const healthCheck: HealthCheck = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      services: {
        database: dbHealth,
        websocket: wsHealth,
        rag_pipelines: ragHealth
      },
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      uptime: Date.now() - startTime
    };
    
    const statusCode = overallStatus === 'unhealthy' ? 503 : 200;
    
    return NextResponse.json(healthCheck, { 
      status: statusCode,
      headers: {
        'Cache-Control': 'no-cache',
        'X-Health-Status': overallStatus
      }
    });
    
  } catch (error) {
    console.error('[HEALTH] Health check failed:', error);
    
    return NextResponse.json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      uptime: Date.now() - startTime
    }, { status: 503 });
  }
}
```

## 5. Integration with Existing Components

### Update Frontend to Use New API Fields

In your Socket.IO context provider, check for WebSocket availability:

```typescript
// In SocketProvider.tsx
useEffect(() => {
  // Check WebSocket availability before connecting
  fetch('/api/socket/info')
    .then(res => res.json())
    .then(info => {
      if (info.available && autoConnect) {
        connect(pipelineType);
      } else {
        console.log('[SOCKET] WebSocket not available, using HTTP polling fallback');
        // Enable fallback polling
        setFallbackMode(true);
      }
    })
    .catch(error => {
      console.error('[SOCKET] Failed to check WebSocket availability:', error);
      setFallbackMode(true);
    });
}, []);
```

These API routes provide comprehensive integration between HTTP fallback and WebSocket real-time communication, ensuring the frontend can gracefully handle both scenarios.