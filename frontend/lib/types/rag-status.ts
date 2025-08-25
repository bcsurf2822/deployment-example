import {
  FileInfo,
  ProcessingResults,
  ProcessingError,
  ServerToClientEvents,
  ClientToServerEvents,
} from "./socket";
import { Socket } from "socket.io-client";

export interface EnhancedFileInfo extends FileInfo {
  processing_duration?: number;
  progress?: number;
  stage?: "extraction" | "chunking" | "embedding" | "storing";
  error?: ProcessingError;
  results?: ProcessingResults;
}

export interface RAGPipelineState {
  isConnected: boolean;
  isConnecting: boolean;
  connectionError?: string;
  lastConnected?: Date;

  pipeline_id?: string;
  pipeline_type?: "google_drive" | "local_files";
  status: "online" | "offline" | "error" | "connecting";


  files_processing: EnhancedFileInfo[];
  files_completed: EnhancedFileInfo[];
  files_failed: EnhancedFileInfo[];

  total_processed: number;
  total_failed: number;

 
  last_check_time?: string;
  next_check_time?: string;
  check_interval: number;
  seconds_until_next_check?: number;
  is_checking: boolean;

  last_activity?: string;


  connection_latency?: number;
  reconnect_attempts: number;
}

export interface RAGPipelineActions {

  connect: (pipelineType: "google_drive" | "local_files") => void;
  disconnect: () => void;

  subscribe: (pipelineType: "google_drive" | "local_files") => void;
  unsubscribe: (pipelineType: "google_drive" | "local_files") => void;

  // State updates (internal)
  updateConnectionStatus: (
    status: "connected" | "disconnected" | "error",
    error?: string
  ) => void;
  updatePipelineStatus: (status: Partial<RAGPipelineState>) => void;
  addProcessingFile: (file: EnhancedFileInfo) => void;
  updateFileProgress: (
    filename: string,
    progress: number,
    stage: "extraction" | "chunking" | "embedding" | "storing"
  ) => void;
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
  connectionHealth: RAGSocketContextType["connectionHealth"];
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
