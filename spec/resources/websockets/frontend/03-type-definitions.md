# TypeScript Type Definitions for Socket.IO

## Core Type Definitions

### 1. Create Socket Types File

Create `lib/types/socket.ts`:

```typescript
// Base interfaces for Socket.IO communication
export interface PipelineInfo {
  pipeline_id: string;
  pipeline_type: 'google_drive' | 'local_files';
  status: 'online' | 'offline' | 'error';
  started_at: string;
  check_interval?: number;
  watch_location?: string;
}

export interface FileInfo {
  name: string;
  id?: string;
  size?: number;
  mime_type?: string;
  started_at?: string;
  completed_at?: string;
}

export interface ProcessingResults {
  chunks_created: number;
  embeddings_generated: number;
  processing_duration: number;
  content_length: number;
}

export interface ProcessingError {
  type: string;
  message: string;
  stage: 'extraction' | 'chunking' | 'embedding' | 'storing';
  retryable: boolean;
}

export interface HeartbeatData {
  pipeline_id: string;
  timestamp: string;
  status: 'alive';
  uptime: number;
  memory_usage?: number;
  active_files: number;
}

// Server-to-Client Events (events the server sends to the client)
export interface ServerToClientEvents {
  // Pipeline lifecycle events
  'pipeline:online': (data: PipelineOnlineEvent) => void;
  'pipeline:offline': (data: PipelineOfflineEvent) => void;
  'pipeline:status': (data: PipelineStatusEvent) => void;

  // File processing events
  'file:processing': (data: FileProcessingEvent) => void;
  'file:progress': (data: FileProgressEvent) => void;
  'file:completed': (data: FileCompletedEvent) => void;
  'file:failed': (data: FileFailedEvent) => void;

  // Status updates
  'status:update': (data: StatusUpdateEvent) => void;
  'heartbeat': (data: HeartbeatData) => void;

  // Connection events
  'connect': () => void;
  'disconnect': (reason: string) => void;
  'connect_error': (error: Error) => void;
  'reconnect': (attemptNumber: number) => void;
  'reconnect_attempt': (attemptNumber: number) => void;
  'reconnect_error': (error: Error) => void;
  'reconnect_failed': () => void;
  'ping': () => void;
  'pong': (latency: number) => void;
}

// Client-to-Server Events (events the client sends to the server)  
export interface ClientToServerEvents {
  // Subscription management
  'subscribe': (data: SubscribeEvent) => void;
  'unsubscribe': (data: UnsubscribeEvent) => void;

  // Connection health
  'ping': (timestamp: number, callback?: (serverTime: number) => void) => void;
  'client:status': (data: ClientStatusEvent) => void;
}

// Event payload interfaces
export interface PipelineOnlineEvent {
  pipeline_id: string;
  pipeline_type: 'google_drive' | 'local_files';
  status: 'online';
  started_at: string;
  check_interval: number;
  watch_location: string;
}

export interface PipelineOfflineEvent {
  pipeline_id: string;
  pipeline_type: 'google_drive' | 'local_files';
  status: 'offline';
  shutdown_at: string;
  reason: 'normal_shutdown' | 'error' | 'timeout';
}

export interface PipelineStatusEvent {
  pipeline_id: string;
  pipeline_type: string;
  status: string;
  last_check_time: string | null;
  next_check_time: string | null;
  files_processing: FileInfo[];
  files_completed: FileInfo[];
  files_failed: FileInfo[];
  total_processed: number;
  total_failed: number;
  check_interval: number;
  is_checking: boolean;
  seconds_until_next_check?: number;
  last_activity: string;
}

export interface FileProcessingEvent {
  pipeline_id: string;
  file: FileInfo;
  processing_stage: 'extraction' | 'chunking' | 'embedding' | 'storing';
  estimated_duration?: number;
  timestamp: string;
}

export interface FileProgressEvent {
  pipeline_id: string;
  file: Pick<FileInfo, 'name' | 'id'>;
  processing_stage: 'extraction' | 'chunking' | 'embedding' | 'storing';
  progress: number; // 0.0 to 1.0
  timestamp: string;
}

export interface FileCompletedEvent {
  pipeline_id: string;
  file: FileInfo;
  results: ProcessingResults;
  success: true;
  timestamp: string;
}

export interface FileFailedEvent {
  pipeline_id: string;
  file: FileInfo;
  error: ProcessingError;
  success: false;
  timestamp: string;
}

export interface StatusUpdateEvent {
  pipeline_id: string;
  timestamp: string;
  changes: Record<string, unknown>;
  current_status: PipelineStatusEvent;
}

export interface SubscribeEvent {
  pipeline_type: 'google_drive' | 'local_files';
  client_info?: {
    user_agent: string;
    timestamp: string;
  };
}

export interface UnsubscribeEvent {
  pipeline_type: 'google_drive' | 'local_files';
}

export interface ClientStatusEvent {
  client_id: string;
  status: 'active' | 'idle' | 'background';
  timestamp: string;
}

// Union types for event data
export type RAGSocketEvent = 
  | PipelineOnlineEvent 
  | PipelineOfflineEvent
  | FileProcessingEvent
  | FileProgressEvent
  | FileCompletedEvent
  | FileFailedEvent
  | StatusUpdateEvent;

// Type guards for event data
export function isPipelineEvent(event: RAGSocketEvent): event is PipelineOnlineEvent | PipelineOfflineEvent {
  return 'pipeline_id' in event && 'pipeline_type' in event;
}

export function isFileEvent(event: RAGSocketEvent): event is FileProcessingEvent | FileProgressEvent | FileCompletedEvent | FileFailedEvent {
  return 'file' in event;
}

export function isFileCompletedEvent(event: RAGSocketEvent): event is FileCompletedEvent {
  return isFileEvent(event) && 'success' in event && event.success === true;
}

export function isFileFailedEvent(event: RAGSocketEvent): event is FileFailedEvent {
  return isFileEvent(event) && 'success' in event && event.success === false;
}

export function isFileProgressEvent(event: RAGSocketEvent): event is FileProgressEvent {
  return isFileEvent(event) && 'progress' in event;
}
```

### 2. Extended Types for React Components

Create `lib/types/rag-status.ts`:

```typescript
import { FileInfo, ProcessingResults, ProcessingError } from './socket';

// Enhanced types for React components
export interface EnhancedFileInfo extends FileInfo {
  processing_duration?: number;
  progress?: number;
  stage?: 'extraction' | 'chunking' | 'embedding' | 'storing';
  error?: ProcessingError;
  results?: ProcessingResults;
}

export interface RAGPipelineState {
  // Connection status
  isConnected: boolean;
  isConnecting: boolean;
  connectionError?: string;
  lastConnected?: Date;
  
  // Pipeline info
  pipeline_id?: string;
  pipeline_type?: 'google_drive' | 'local_files';
  status: 'online' | 'offline' | 'error' | 'connecting';
  
  // File processing
  files_processing: EnhancedFileInfo[];
  files_completed: EnhancedFileInfo[];
  files_failed: EnhancedFileInfo[];
  
  // Statistics
  total_processed: number;
  total_failed: number;
  
  // Timing
  last_check_time?: string;
  next_check_time?: string;
  check_interval: number;
  seconds_until_next_check?: number;
  is_checking: boolean;
  
  // Activity
  last_activity?: string;
  
  // Health monitoring
  connection_latency?: number;
  reconnect_attempts: number;
}

export interface RAGPipelineActions {
  // Connection management
  connect: (pipelineType: 'google_drive' | 'local_files') => void;
  disconnect: () => void;
  
  // Subscription management  
  subscribe: (pipelineType: 'google_drive' | 'local_files') => void;
  unsubscribe: (pipelineType: 'google_drive' | 'local_files') => void;
  
  // State updates (internal)
  updateConnectionStatus: (status: 'connected' | 'disconnected' | 'error', error?: string) => void;
  updatePipelineStatus: (status: Partial<RAGPipelineState>) => void;
  addProcessingFile: (file: EnhancedFileInfo) => void;
  updateFileProgress: (filename: string, progress: number, stage: string) => void;
  completeFile: (filename: string, results: ProcessingResults) => void;
  failFile: (filename: string, error: ProcessingError) => void;
}

// Context type for React
export interface RAGSocketContextType {
  state: RAGPipelineState;
  actions: RAGPipelineActions;
  
  // Direct socket access (advanced usage)
  socket?: Socket<ServerToClientEvents, ClientToServerEvents>;
  
  // Health monitoring
  connectionHealth: {
    isHealthy: boolean;
    latency?: number;
    transport?: string;
    reconnectAttempts: number;
  };
}

// Hook return types
export interface UseRAGSocketReturn {
  state: RAGPipelineState;
  actions: RAGPipelineActions;
  connectionHealth: RAGSocketContextType['connectionHealth'];
}

export interface UseFileProcessingReturn {
  processingFiles: EnhancedFileInfo[];
  completedFiles: EnhancedFileInfo[];
  failedFiles: EnhancedFileInfo[];
  isProcessing: boolean;
  processingStats: {
    totalProcessed: number;
    totalFailed: number;
    successRate: number;
    averageProcessingTime: number;
  };
}
```

### 3. Utility Types

Create `lib/types/socket-utils.ts`:

```typescript
import { Socket } from 'socket.io-client';
import { ServerToClientEvents, ClientToServerEvents } from './socket';

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
```

### 4. Type Validation and Runtime Checking

Create `lib/types/socket-validation.ts`:

```typescript
import { z } from 'zod';
import { 
  PipelineOnlineEvent,
  FileProcessingEvent,
  FileCompletedEvent,
  FileFailedEvent,
  StatusUpdateEvent
} from './socket';

// Zod schemas for runtime validation
export const FileInfoSchema = z.object({
  name: z.string(),
  id: z.string().optional(),
  size: z.number().optional(),
  mime_type: z.string().optional(),
  started_at: z.string().optional(),
  completed_at: z.string().optional()
});

export const ProcessingResultsSchema = z.object({
  chunks_created: z.number(),
  embeddings_generated: z.number(),
  processing_duration: z.number(),
  content_length: z.number()
});

export const ProcessingErrorSchema = z.object({
  type: z.string(),
  message: z.string(),
  stage: z.enum(['extraction', 'chunking', 'embedding', 'storing']),
  retryable: z.boolean()
});

export const PipelineOnlineEventSchema = z.object({
  pipeline_id: z.string(),
  pipeline_type: z.enum(['google_drive', 'local_files']),
  status: z.literal('online'),
  started_at: z.string(),
  check_interval: z.number(),
  watch_location: z.string()
});

export const FileProcessingEventSchema = z.object({
  pipeline_id: z.string(),
  file: FileInfoSchema,
  processing_stage: z.enum(['extraction', 'chunking', 'embedding', 'storing']),
  estimated_duration: z.number().optional(),
  timestamp: z.string()
});

export const FileCompletedEventSchema = z.object({
  pipeline_id: z.string(),
  file: FileInfoSchema,
  results: ProcessingResultsSchema,
  success: z.literal(true),
  timestamp: z.string()
});

export const FileFailedEventSchema = z.object({
  pipeline_id: z.string(),
  file: FileInfoSchema,
  error: ProcessingErrorSchema,
  success: z.literal(false),
  timestamp: z.string()
});

// Validation functions
export function validatePipelineOnlineEvent(data: unknown): data is PipelineOnlineEvent {
  try {
    PipelineOnlineEventSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

export function validateFileProcessingEvent(data: unknown): data is FileProcessingEvent {
  try {
    FileProcessingEventSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

export function validateFileCompletedEvent(data: unknown): data is FileCompletedEvent {
  try {
    FileCompletedEventSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

export function validateFileFailedEvent(data: unknown): data is FileFailedEvent {
  try {
    FileFailedEventSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

// Generic event validator
export function createEventValidator<T>(schema: z.ZodSchema<T>) {
  return (data: unknown): data is T => {
    try {
      schema.parse(data);
      return true;
    } catch (error) {
      console.warn('[SOCKET-VALIDATION] Invalid event data:', error);
      return false;
    }
  };
}

// Event sanitization
export function sanitizeEventData<T>(data: T, allowedFields: (keyof T)[]): Partial<T> {
  const sanitized: Partial<T> = {};
  
  allowedFields.forEach(field => {
    if (field in data) {
      sanitized[field] = data[field];
    }
  });
  
  return sanitized;
}
```

This comprehensive type system provides full TypeScript support for Socket.IO integration with runtime validation and type safety throughout the application.