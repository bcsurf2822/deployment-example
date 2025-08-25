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