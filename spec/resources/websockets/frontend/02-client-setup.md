# Socket.IO Client Setup

## Client Configuration

### 1. Create Socket.IO Client Module

Create `lib/socket.ts`:

```typescript
import { io, Socket } from 'socket.io-client';
import { ServerToClientEvents, ClientToServerEvents } from './types/socket';

// Socket.IO client configuration
const SOCKET_IO_URL = process.env.NEXT_PUBLIC_SOCKET_IO_URL || 'http://localhost:8103';
const CONNECTION_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_SOCKET_TIMEOUT || '5000');

class SocketIOClient {
  private socket: Socket<ServerToClientEvents, ClientToServerEvents> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private isManuallyDisconnected = false;

  constructor() {
    // Don't initialize immediately - wait for explicit connect call
  }

  connect(pipelineType?: string): Socket<ServerToClientEvents, ClientToServerEvents> {
    if (this.socket?.connected) {
      return this.socket;
    }

    const namespace = pipelineType ? `/${pipelineType}` : '';
    const socketUrl = `${SOCKET_IO_URL}${namespace}`;

    this.socket = io(socketUrl, {
      timeout: CONNECTION_TIMEOUT,
      retries: 3,
      
      // Transport configuration
      transports: ['websocket', 'polling'], // Prefer WebSocket, fallback to polling
      upgrade: true,
      
      // Reconnection configuration
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 10000,
      randomizationFactor: 0.5,
      
      // Connection headers
      extraHeaders: {
        'X-Pipeline-Type': pipelineType || 'unknown'
      },
      
      // Query parameters
      query: {
        clientType: 'frontend',
        version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'
      },
      
      // Auto-connect
      autoConnect: true,
      
      // Force new connection
      forceNew: false
    });

    this.setupEventHandlers();
    this.isManuallyDisconnected = false;

    return this.socket;
  }

  private setupEventHandlers() {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      console.log(`[SOCKET-IO] Connected to ${this.socket?.nsp} (ID: ${this.socket?.id})`);
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000; // Reset delay
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`[SOCKET-IO] Disconnected: ${reason}`);
      
      if (reason === 'io server disconnect' && !this.isManuallyDisconnected) {
        // Server initiated disconnect, try to reconnect
        this.handleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error(`[SOCKET-IO] Connection error:`, error);
      this.handleReconnect();
    });

    // Reconnection events
    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`[SOCKET-IO] Reconnected after ${attemptNumber} attempts`);
      this.reconnectAttempts = 0;
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[SOCKET-IO] Reconnection attempt ${attemptNumber}`);
    });

    this.socket.on('reconnect_error', (error) => {
      console.error(`[SOCKET-IO] Reconnection failed:`, error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error(`[SOCKET-IO] Failed to reconnect after ${this.maxReconnectAttempts} attempts`);
      // Could emit a custom event here for UI to show "offline" state
    });

    // Handle ping/pong for connection health
    this.socket.on('ping', () => {
      console.debug('[SOCKET-IO] Received ping');
    });

    this.socket.on('pong', (latency) => {
      console.debug(`[SOCKET-IO] Pong received (latency: ${latency}ms)`);
    });
  }

  private handleReconnect() {
    if (this.isManuallyDisconnected) return;

    this.reconnectAttempts++;
    
    if (this.reconnectAttempts <= this.maxReconnectAttempts) {
      const delay = Math.min(
        this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
        10000
      );
      
      console.log(`[SOCKET-IO] Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        if (!this.socket?.connected && !this.isManuallyDisconnected) {
          this.socket?.connect();
        }
      }, delay);
    }
  }

  disconnect() {
    this.isManuallyDisconnected = true;
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  subscribe(pipelineType: string) {
    if (this.socket?.connected) {
      this.socket.emit('subscribe', { pipeline_type: pipelineType });
    }
  }

  unsubscribe(pipelineType: string) {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe', { pipeline_type: pipelineType });
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionId(): string | undefined {
    return this.socket?.id;
  }

  getTransport(): string | undefined {
    return this.socket?.io?.engine?.transport?.name;
  }

  // Event listener management
  on<K extends keyof ServerToClientEvents>(
    event: K, 
    handler: ServerToClientEvents[K]
  ) {
    this.socket?.on(event, handler);
  }

  off<K extends keyof ServerToClientEvents>(
    event: K, 
    handler?: ServerToClientEvents[K]
  ) {
    this.socket?.off(event, handler);
  }

  // One-time event listeners
  once<K extends keyof ServerToClientEvents>(
    event: K, 
    handler: ServerToClientEvents[K]
  ) {
    this.socket?.once(event, handler);
  }
}

// Singleton instance
let socketClient: SocketIOClient | null = null;

export function getSocketClient(): SocketIOClient {
  if (!socketClient) {
    socketClient = new SocketIOClient();
  }
  return socketClient;
}

// Utility functions for common operations
export function connectToRAGPipeline(pipelineType: 'google_drive' | 'local_files') {
  const client = getSocketClient();
  const socket = client.connect(pipelineType);
  client.subscribe(pipelineType);
  return socket;
}

export function disconnectFromRAGPipeline() {
  const client = getSocketClient();
  client.disconnect();
}

// Export the client instance for direct use if needed
export { SocketIOClient };
```

### 2. Environment Variables

Add to `.env.local`:

```bash
# Socket.IO Configuration
NEXT_PUBLIC_SOCKET_IO_URL=http://localhost:8103
NEXT_PUBLIC_SOCKET_TIMEOUT=5000
NEXT_PUBLIC_APP_VERSION=1.0.0

# Production settings
NEXT_PUBLIC_SOCKET_IO_URL=wss://yourdomain.com
```

Add to `.env.example`:

```bash
# Socket.IO Client Configuration
NEXT_PUBLIC_SOCKET_IO_URL=http://localhost:8103
NEXT_PUBLIC_SOCKET_TIMEOUT=5000
NEXT_PUBLIC_SOCKET_ENABLE_DEBUG=false
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### 3. Connection Health Monitoring

Create `lib/socket-health.ts`:

```typescript
import { getSocketClient } from './socket';

export interface ConnectionHealth {
  isConnected: boolean;
  connectionId?: string;
  transport?: string;
  latency?: number;
  reconnectAttempts: number;
  lastConnected?: Date;
  lastDisconnected?: Date;
}

class SocketHealthMonitor {
  private health: ConnectionHealth = {
    isConnected: false,
    reconnectAttempts: 0
  };
  
  private latencyInterval: NodeJS.Timeout | null = null;
  private healthCheckInterval: NodeJS.Timeout | null = null;
  private listeners: ((health: ConnectionHealth) => void)[] = [];

  startMonitoring() {
    const client = getSocketClient();
    const socket = client.connect();

    // Monitor connection status
    socket.on('connect', () => {
      this.health = {
        ...this.health,
        isConnected: true,
        connectionId: socket.id,
        transport: client.getTransport(),
        lastConnected: new Date(),
        reconnectAttempts: 0
      };
      this.notifyListeners();
      this.startLatencyCheck();
    });

    socket.on('disconnect', () => {
      this.health = {
        ...this.health,
        isConnected: false,
        lastDisconnected: new Date()
      };
      this.notifyListeners();
      this.stopLatencyCheck();
    });

    socket.on('reconnect_attempt', () => {
      this.health.reconnectAttempts++;
      this.notifyListeners();
    });

    // Health check every 30 seconds
    this.healthCheckInterval = setInterval(() => {
      this.checkHealth();
    }, 30000);
  }

  stopMonitoring() {
    if (this.latencyInterval) {
      clearInterval(this.latencyInterval);
      this.latencyInterval = null;
    }
    
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }

  private startLatencyCheck() {
    if (this.latencyInterval) return;

    this.latencyInterval = setInterval(() => {
      const client = getSocketClient();
      const start = Date.now();
      
      client.socket?.emit('ping', start, (serverTime: number) => {
        this.health.latency = Date.now() - start;
        this.notifyListeners();
      });
    }, 10000); // Check every 10 seconds
  }

  private stopLatencyCheck() {
    if (this.latencyInterval) {
      clearInterval(this.latencyInterval);
      this.latencyInterval = null;
    }
  }

  private checkHealth() {
    const client = getSocketClient();
    this.health = {
      ...this.health,
      isConnected: client.isConnected(),
      connectionId: client.getConnectionId(),
      transport: client.getTransport()
    };
    this.notifyListeners();
  }

  private notifyListeners() {
    this.listeners.forEach(listener => {
      try {
        listener(this.health);
      } catch (error) {
        console.error('[SOCKET-HEALTH] Error in listener:', error);
      }
    });
  }

  getHealth(): ConnectionHealth {
    return { ...this.health };
  }

  onHealthChange(listener: (health: ConnectionHealth) => void) {
    this.listeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }
}

// Singleton instance
let healthMonitor: SocketHealthMonitor | null = null;

export function getSocketHealthMonitor(): SocketHealthMonitor {
  if (!healthMonitor) {
    healthMonitor = new SocketHealthMonitor();
  }
  return healthMonitor;
}
```

### 4. Error Handling and Fallbacks

Create `lib/socket-fallback.ts`:

```typescript
import { getSocketClient } from './socket';

export interface FallbackConfig {
  enablePolling: boolean;
  pollingInterval: number;
  maxFailures: number;
  fallbackURL: string;
}

class SocketFallbackHandler {
  private config: FallbackConfig;
  private failureCount = 0;
  private isUsingFallback = false;
  private pollingInterval: NodeJS.Timeout | null = null;

  constructor(config: Partial<FallbackConfig> = {}) {
    this.config = {
      enablePolling: true,
      pollingInterval: 10000, // 10 seconds
      maxFailures: 3,
      fallbackURL: '/api/rag-status',
      ...config
    };
  }

  handleConnectionFailure() {
    this.failureCount++;
    
    if (this.failureCount >= this.config.maxFailures && !this.isUsingFallback) {
      this.enableFallback();
    }
  }

  handleConnectionSuccess() {
    if (this.isUsingFallback) {
      this.disableFallback();
    }
    this.failureCount = 0;
  }

  private enableFallback() {
    console.log('[SOCKET-FALLBACK] Enabling HTTP polling fallback');
    this.isUsingFallback = true;
    
    if (this.config.enablePolling) {
      this.startPolling();
    }

    // Emit custom event for UI to show fallback mode
    window.dispatchEvent(new CustomEvent('socket-fallback-enabled'));
  }

  private disableFallback() {
    console.log('[SOCKET-FALLBACK] Disabling fallback, returning to WebSocket');
    this.isUsingFallback = false;
    this.stopPolling();
    
    window.dispatchEvent(new CustomEvent('socket-fallback-disabled'));
  }

  private startPolling() {
    if (this.pollingInterval) return;

    this.pollingInterval = setInterval(async () => {
      try {
        const response = await fetch(this.config.fallbackURL);
        const data = await response.json();
        
        // Emit the data as if it came from Socket.IO
        window.dispatchEvent(new CustomEvent('rag-status-update', {
          detail: data
        }));
        
      } catch (error) {
        console.error('[SOCKET-FALLBACK] Polling error:', error);
      }
    }, this.config.pollingInterval);
  }

  private stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  isInFallbackMode(): boolean {
    return this.isUsingFallback;
  }

  cleanup() {
    this.stopPolling();
  }
}

export { SocketFallbackHandler };
```

### 5. Next.js Configuration

Update `next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable WebSocket support
  experimental: {
    serverComponentsExternalPackages: ['socket.io-client']
  },
  
  // Headers for WebSocket CORS
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: process.env.NEXT_PUBLIC_SOCKET_IO_URL || '*'
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, OPTIONS'
          },
          {
            key: 'Access-Control-Allow-Headers', 
            value: 'Content-Type, Authorization'
          }
        ]
      }
    ];
  },

  // Webpack configuration for Socket.IO client
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        net: false,
        tls: false,
        fs: false
      };
    }
    return config;
  }
};

module.exports = nextConfig;
```

This setup provides a robust, production-ready Socket.IO client with automatic reconnection, health monitoring, and fallback capabilities.