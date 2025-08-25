import { Socket } from 'socket.io-client';
import { ServerToClientEvents, ClientToServerEvents } from './socket';
import React from 'react';

// Typed Socket.IO client
export type TypedSocket = Socket<ServerToClientEvents, ClientToServerEvents>;

// Event handler types
export type SocketEventHandler<T extends keyof ServerToClientEvents> = ServerToClientEvents[T];

// Event listener management
export interface SocketEventListener {
  event: keyof ServerToClientEvents;
  handler: Function;
  once?: boolean;
}

// Configuration types
export interface SocketConfig {
  url: string;
  namespace?: string;
  timeout?: number;
  retries?: number;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
  transports?: ('websocket' | 'polling')[];
  autoConnect?: boolean;
  forceNew?: boolean;
}

export interface SocketConnectionOptions {
  pipelineType?: 'google_drive' | 'local_files';
  autoSubscribe?: boolean;
  enableFallback?: boolean;
  debug?: boolean;
}

// Error types
export interface SocketError extends Error {
  type: 'connection' | 'timeout' | 'protocol' | 'transport';
  code?: string | number;
  description?: string;
  context?: Record<string, unknown>;
}

export interface ConnectionError extends SocketError {
  type: 'connection';
  attempt: number;
  maxAttempts: number;
}

export interface TimeoutError extends SocketError {
  type: 'timeout';
  operation: 'connect' | 'emit' | 'response';
  duration: number;
}

// Status types
export type ConnectionStatus = 
  | 'disconnected'
  | 'connecting' 
  | 'connected'
  | 'reconnecting'
  | 'failed';

export type PipelineStatus = 
  | 'initializing'
  | 'idle'
  | 'checking'
  | 'processing'
  | 'offline'
  | 'error';

// Event tracking types
export interface EventMetrics {
  eventType: keyof ServerToClientEvents;
  count: number;
  lastReceived: Date;
  averageLatency?: number;
}

export interface SocketMetrics {
  connectionTime?: Date;
  disconnectionTime?: Date;
  totalConnections: number;
  totalDisconnections: number;
  events: Map<keyof ServerToClientEvents, EventMetrics>;
  errors: SocketError[];
  latencyHistory: number[];
}

// Namespace-specific types
export interface NamespaceConfig {
  'google_drive': {
    folderId: string;
    authType: 'service_account' | 'oauth';
  };
  'local_files': {
    watchDirectory: string;
    recursive: boolean;
  };
}

// React component prop types
export interface SocketProviderProps {
  children: React.ReactNode;
  config?: Partial<SocketConfig>;
  options?: SocketConnectionOptions;
  fallbackEnabled?: boolean;
  debug?: boolean;
}

export interface ConnectionStatusProps {
  showDetails?: boolean;
  className?: string;
  onConnectionChange?: (status: ConnectionStatus) => void;
}

export interface FileProcessingProps {
  pipelineType?: 'google_drive' | 'local_files';
  showProgress?: boolean;
  maxItems?: number;
  className?: string;
}

// Validation types
export interface EventValidationSchema {
  [K in keyof ServerToClientEvents]: {
    required: (keyof Parameters<ServerToClientEvents[K]>[0])[];
    optional?: (keyof Parameters<ServerToClientEvents[K]>[0])[];
    validate?: (data: Parameters<ServerToClientEvents[K]>[0]) => boolean;
  };
}

// Helper function types
export type EventValidator<T extends keyof ServerToClientEvents> = 
  (data: unknown) => data is Parameters<ServerToClientEvents[T]>[0];

export type EventTransformer<T extends keyof ServerToClientEvents> = 
  (data: Parameters<ServerToClientEvents[T]>[0]) => Parameters<ServerToClientEvents[T]>[0];

// Advanced socket management types
export interface SocketManager {
  connect: (options?: SocketConnectionOptions) => Promise<TypedSocket>;
  disconnect: () => Promise<void>;
  reconnect: () => Promise<TypedSocket>;
  subscribe: (pipelineType: string) => Promise<void>;
  unsubscribe: (pipelineType: string) => Promise<void>;
  getMetrics: () => SocketMetrics;
  isHealthy: () => boolean;
  cleanup: () => Promise<void>;
}