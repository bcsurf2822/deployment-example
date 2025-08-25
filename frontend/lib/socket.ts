'use client';

import { io } from 'socket.io-client';
import { TypedSocket, SocketConfig, SocketConnectionOptions } from '@/lib/types/socket-utils';
import { ServerToClientEvents, ClientToServerEvents } from '@/lib/types/socket';

class SocketClient {
  private static instance: SocketClient;
  private sockets: Map<string, TypedSocket> = new Map();
  private currentPipelineType?: 'google_drive' | 'local_files';
  private config: SocketConfig;

  private constructor() {
    this.config = {
      url: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:8004',
      timeout: 10000,
      retries: 3,
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
      transports: ['websocket', 'polling'],
      autoConnect: false,
      forceNew: false
    };
  }

  static getInstance(): SocketClient {
    if (!SocketClient.instance) {
      SocketClient.instance = new SocketClient();
    }
    return SocketClient.instance;
  }

  connect(pipelineType: 'google_drive' | 'local_files', options?: SocketConnectionOptions): TypedSocket {
    console.log(`[SOCKET-CLIENT] Connecting to ${pipelineType} namespace`);
    
    const namespace = `/${pipelineType}`;
    const socketKey = `${this.config.url}${namespace}`;
    
    // If already connected to this pipeline type, return existing socket
    if (this.sockets.has(socketKey) && this.sockets.get(socketKey)?.connected) {
      console.log(`[SOCKET-CLIENT] Reusing existing connection to ${pipelineType}`);
      return this.sockets.get(socketKey)!;
    }

    // Disconnect from other pipeline types if switching
    if (this.currentPipelineType && this.currentPipelineType !== pipelineType) {
      this.disconnect();
    }

    try {
      const socket = io(`${this.config.url}${namespace}`, {
        timeout: this.config.timeout,
        retries: this.config.retries,
        reconnectionAttempts: this.config.reconnectionAttempts,
        reconnectionDelay: this.config.reconnectionDelay,
        transports: this.config.transports,
        autoConnect: true,
        forceNew: options?.debug || false,
        auth: {
          client_type: 'web_frontend',
          user_agent: typeof window !== 'undefined' ? window.navigator.userAgent : 'SSR'
        }
      }) as TypedSocket;

      // Store the socket
      this.sockets.set(socketKey, socket);
      this.currentPipelineType = pipelineType;

      // Set up connection event logging
      socket.on('connect', () => {
        console.log(`[SOCKET-CLIENT] Connected to ${pipelineType} (${socket.id})`);
      });

      socket.on('disconnect', (reason) => {
        console.log(`[SOCKET-CLIENT] Disconnected from ${pipelineType}:`, reason);
      });

      socket.on('connect_error', (error) => {
        console.error(`[SOCKET-CLIENT] Connection error for ${pipelineType}:`, error);
      });

      socket.on('reconnect', (attemptNumber) => {
        console.log(`[SOCKET-CLIENT] Reconnected to ${pipelineType} after ${attemptNumber} attempts`);
      });

      socket.on('reconnect_attempt', (attemptNumber) => {
        console.log(`[SOCKET-CLIENT] Reconnection attempt ${attemptNumber} for ${pipelineType}`);
      });

      // Auto-subscribe if enabled
      if (options?.autoSubscribe !== false) {
        socket.on('connect', () => {
          this.subscribe(pipelineType);
        });
      }

      return socket;
    } catch (error) {
      console.error(`[SOCKET-CLIENT] Failed to create socket for ${pipelineType}:`, error);
      throw error;
    }
  }

  disconnect(): void {
    console.log('[SOCKET-CLIENT] Disconnecting all sockets');
    
    this.sockets.forEach((socket, key) => {
      if (socket.connected) {
        socket.disconnect();
      }
    });
    
    this.sockets.clear();
    this.currentPipelineType = undefined;
  }

  subscribe(pipelineType: 'google_drive' | 'local_files'): void {
    const namespace = `/${pipelineType}`;
    const socketKey = `${this.config.url}${namespace}`;
    const socket = this.sockets.get(socketKey);

    if (socket?.connected) {
      console.log(`[SOCKET-CLIENT] Subscribing to ${pipelineType} events`);
      socket.emit('subscribe', {
        pipeline_type: pipelineType,
        client_info: {
          user_agent: typeof window !== 'undefined' ? window.navigator.userAgent : 'SSR',
          timestamp: new Date().toISOString()
        }
      });
    } else {
      console.warn(`[SOCKET-CLIENT] Cannot subscribe - not connected to ${pipelineType}`);
    }
  }

  unsubscribe(pipelineType: 'google_drive' | 'local_files'): void {
    const namespace = `/${pipelineType}`;
    const socketKey = `${this.config.url}${namespace}`;
    const socket = this.sockets.get(socketKey);

    if (socket?.connected) {
      console.log(`[SOCKET-CLIENT] Unsubscribing from ${pipelineType} events`);
      socket.emit('unsubscribe', {
        pipeline_type: pipelineType
      });
    }
  }

  get socket(): TypedSocket | undefined {
    if (!this.currentPipelineType) return undefined;
    
    const namespace = `/${this.currentPipelineType}`;
    const socketKey = `${this.config.url}${namespace}`;
    return this.sockets.get(socketKey);
  }

  get isConnected(): boolean {
    return this.socket?.connected || false;
  }

  get currentPipeline(): 'google_drive' | 'local_files' | undefined {
    return this.currentPipelineType;
  }

  // Health check
  ping(): Promise<number> {
    return new Promise((resolve, reject) => {
      const socket = this.socket;
      if (!socket?.connected) {
        reject(new Error('Socket not connected'));
        return;
      }

      const startTime = Date.now();
      socket.emit('ping', startTime, (serverTime: number) => {
        const latency = Date.now() - startTime;
        resolve(latency);
      });
    });
  }

  // Update configuration
  updateConfig(newConfig: Partial<SocketConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

// Export singleton functions
export function getSocketClient(): SocketClient {
  return SocketClient.getInstance();
}

// Convenience functions for direct usage
export function connectToRAGPipeline(pipelineType: 'google_drive' | 'local_files', options?: SocketConnectionOptions): TypedSocket {
  return getSocketClient().connect(pipelineType, options);
}

export function disconnectFromRAGPipeline(): void {
  getSocketClient().disconnect();
}

export function subscribeToRAGEvents(pipelineType: 'google_drive' | 'local_files'): void {
  getSocketClient().subscribe(pipelineType);
}

export function unsubscribeFromRAGEvents(pipelineType: 'google_drive' | 'local_files'): void {
  getSocketClient().unsubscribe(pipelineType);
}