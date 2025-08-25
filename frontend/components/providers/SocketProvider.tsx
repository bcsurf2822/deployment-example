"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useReducer,
  useCallback,
  useMemo,
} from "react";
import { getSocketClient } from "@/lib/socket";
import { getSocketHealthMonitor } from "@/lib/socket-health";
import { SocketFallbackHandler } from "@/lib/socket-fallback";
import {
  RAGSocketContextType,
  RAGPipelineState,
  RAGPipelineActions,
  EnhancedFileInfo,
} from "@/lib/types/rag-status";
import {
  FileProcessingEvent,
  FileCompletedEvent,
  FileFailedEvent,
  PipelineStatusEvent,
  FileProgressEvent,
  ProcessingResults,
  ProcessingError,
} from "@/lib/types/socket";

// Initial state
const initialState: RAGPipelineState = {
  isConnected: false,
  isConnecting: false,
  status: "offline",
  files_processing: [],
  files_completed: [],
  files_failed: [],
  total_processed: 0,
  total_failed: 0,
  check_interval: 60,
  is_checking: false,
  reconnect_attempts: 0,
};

// Action types
type SocketAction =
  | { type: "SET_CONNECTING"; payload: boolean }
  | { type: "SET_CONNECTED"; payload: boolean }
  | { type: "SET_CONNECTION_ERROR"; payload: string }
  | { type: "UPDATE_PIPELINE_STATUS"; payload: Partial<RAGPipelineState> }
  | { type: "ADD_PROCESSING_FILE"; payload: EnhancedFileInfo }
  | {
      type: "UPDATE_FILE_PROGRESS";
      payload: {
        filename: string;
        progress: number;
        stage: "extraction" | "chunking" | "embedding" | "storing";
      };
    }
  | {
      type: "COMPLETE_FILE";
      payload: { filename: string; results: ProcessingResults };
    }
  | { type: "FAIL_FILE"; payload: { filename: string; error: ProcessingError } }
  | { type: "SET_RECONNECT_ATTEMPTS"; payload: number }
  | { type: "RESET_STATE" };

// Reducer
function socketReducer(
  state: RAGPipelineState,
  action: SocketAction
): RAGPipelineState {
  switch (action.type) {
    case "SET_CONNECTING":
      return {
        ...state,
        isConnecting: action.payload,
        connectionError: undefined,
      };

    case "SET_CONNECTED":
      return {
        ...state,
        isConnected: action.payload,
        isConnecting: false,
        connectionError: action.payload ? undefined : state.connectionError,
        lastConnected: action.payload ? new Date() : state.lastConnected,
      };

    case "SET_CONNECTION_ERROR":
      return {
        ...state,
        connectionError: action.payload,
        isConnecting: false,
        isConnected: false,
      };

    case "UPDATE_PIPELINE_STATUS":
      return { ...state, ...action.payload };

    case "ADD_PROCESSING_FILE":
      return {
        ...state,
        files_processing: [...state.files_processing, action.payload],
      };

    case "UPDATE_FILE_PROGRESS":
      return {
        ...state,
        files_processing: state.files_processing.map((file) =>
          file.name === action.payload.filename
            ? {
                ...file,
                progress: action.payload.progress,
                stage: action.payload.stage,
              }
            : file
        ),
      };

    case "COMPLETE_FILE":
      const completingFile = state.files_processing.find(
        (f) => f.name === action.payload.filename
      );
      if (!completingFile) return state;

      const completedFile = {
        ...completingFile,
        completed_at: new Date().toISOString(),
        results: action.payload.results,
      };

      return {
        ...state,
        files_processing: state.files_processing.filter(
          (f) => f.name !== action.payload.filename
        ),
        files_completed: [completedFile, ...state.files_completed].slice(0, 10), // Keep last 10
        total_processed: state.total_processed + 1,
      };

    case "FAIL_FILE":
      const failingFile = state.files_processing.find(
        (f) => f.name === action.payload.filename
      );
      if (!failingFile) return state;

      const failedFile = {
        ...failingFile,
        completed_at: new Date().toISOString(),
        error: action.payload.error,
      };

      return {
        ...state,
        files_processing: state.files_processing.filter(
          (f) => f.name !== action.payload.filename
        ),
        files_failed: [failedFile, ...state.files_failed].slice(0, 5), // Keep last 5
        total_failed: state.total_failed + 1,
      };

    case "SET_RECONNECT_ATTEMPTS":
      return { ...state, reconnect_attempts: action.payload };

    case "RESET_STATE":
      return { ...initialState };

    default:
      return state;
  }
}

// Context
const SocketContext = createContext<RAGSocketContextType | undefined>(
  undefined
);

// Provider props
interface SocketProviderProps {
  children: React.ReactNode;
  pipelineType?: "google_drive" | "local_files";
  autoConnect?: boolean;
  fallbackEnabled?: boolean;
}

// Provider component
export function SocketProvider({
  children,
  pipelineType,
  autoConnect = true,
  fallbackEnabled = true,
}: SocketProviderProps) {
  const [state, dispatch] = useReducer(socketReducer, initialState);
  const socketClient = getSocketClient();
  const healthMonitor = getSocketHealthMonitor();
  const fallbackHandler = useMemo(
    () => new SocketFallbackHandler({ enabled: fallbackEnabled }),
    [fallbackEnabled]
  );

  // Connection management
  const connect = useCallback(
    (type: "google_drive" | "local_files") => {
      console.log(`[SOCKET-PROVIDER] Connecting to ${type}`);
      dispatch({ type: "SET_CONNECTING", payload: true });

      try {
        const socket = socketClient.connect(type);

        // Set up event listeners
        socket.on("connect", () => {
          console.log(`[SOCKET-PROVIDER] Connected to ${type}`);
          dispatch({ type: "SET_CONNECTED", payload: true });
          fallbackHandler.handleConnectionSuccess();
        });

        socket.on("disconnect", (reason: string) => {
          console.log(`[SOCKET-PROVIDER] Disconnected from ${type}:`, reason);
          dispatch({ type: "SET_CONNECTED", payload: false });
          if (reason === "io server disconnect") {
            fallbackHandler.handleConnectionFailure();
          }
        });

        socket.on("connect_error", (error: Error) => {
          console.error(
            `[SOCKET-PROVIDER] Connection error for ${type}:`,
            error
          );
          dispatch({ type: "SET_CONNECTION_ERROR", payload: error.message });
          fallbackHandler.handleConnectionFailure();
        });

        socket.on("reconnect_attempt", (attemptNumber: number) => {
          console.log(
            `[SOCKET-PROVIDER] Reconnection attempt ${attemptNumber} for ${type}`
          );
          dispatch({ type: "SET_RECONNECT_ATTEMPTS", payload: attemptNumber });
        });

        // Pipeline events
        socket.on("pipeline:status", (data: PipelineStatusEvent) => {
          console.log(`[SOCKET-PROVIDER] Pipeline status update:`, data);
          dispatch({
            type: "UPDATE_PIPELINE_STATUS",
            payload: {
              pipeline_id: data.pipeline_id,
              pipeline_type: data.pipeline_type as
                | "google_drive"
                | "local_files",
              status: data.status as
                | "online"
                | "offline"
                | "error"
                | "connecting",
              files_processing: data.files_processing,
              files_completed: data.files_completed,
              files_failed: data.files_failed,
              total_processed: data.total_processed,
              total_failed: data.total_failed,
              last_check_time: data.last_check_time || undefined,
              next_check_time: data.next_check_time || undefined,
              check_interval: data.check_interval,
              is_checking: data.is_checking,
              seconds_until_next_check: data.seconds_until_next_check,
              last_activity: data.last_activity,
            },
          });
        });

        socket.on("file:processing", (data: FileProcessingEvent) => {
          console.log(
            `[SOCKET-PROVIDER] File processing started:`,
            data.file.name
          );
          dispatch({
            type: "ADD_PROCESSING_FILE",
            payload: {
              ...data.file,
              stage: data.processing_stage,
            },
          });
        });

        socket.on("file:progress", (data: FileProgressEvent) => {
          console.log(
            `[SOCKET-PROVIDER] File progress update:`,
            data.file.name,
            `${(data.progress * 100).toFixed(1)}%`
          );
          dispatch({
            type: "UPDATE_FILE_PROGRESS",
            payload: {
              filename: data.file.name,
              progress: data.progress,
              stage: data.processing_stage,
            },
          });
        });

        socket.on("file:completed", (data: FileCompletedEvent) => {
          console.log(`[SOCKET-PROVIDER] File completed:`, data.file.name);
          dispatch({
            type: "COMPLETE_FILE",
            payload: {
              filename: data.file.name,
              results: data.results,
            },
          });
        });

        socket.on("file:failed", (data: FileFailedEvent) => {
          console.log(
            `[SOCKET-PROVIDER] File failed:`,
            data.file.name,
            data.error.message
          );
          dispatch({
            type: "FAIL_FILE",
            payload: {
              filename: data.file.name,
              error: data.error,
            },
          });
        });

        // Subscribe to pipeline updates
        socketClient.subscribe(type);
      } catch (error) {
        console.error(`[SOCKET-PROVIDER] Failed to connect:`, error);
        dispatch({
          type: "SET_CONNECTION_ERROR",
          payload: (error as Error).message,
        });
      }
    },
    [socketClient, fallbackHandler]
  );

  const disconnect = useCallback(() => {
    console.log("[SOCKET-PROVIDER] Disconnecting");
    socketClient.disconnect();
    dispatch({ type: "RESET_STATE" });
  }, [socketClient]);

  const subscribe = useCallback(
    (type: "google_drive" | "local_files") => {
      socketClient.subscribe(type);
    },
    [socketClient]
  );

  const unsubscribe = useCallback(
    (type: "google_drive" | "local_files") => {
      socketClient.unsubscribe(type);
    },
    [socketClient]
  );

  // Actions object
  const actions: RAGPipelineActions = {
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    updateConnectionStatus: useCallback((status, error) => {
      if (status === "connected") {
        dispatch({ type: "SET_CONNECTED", payload: true });
      } else if (status === "disconnected") {
        dispatch({ type: "SET_CONNECTED", payload: false });
      } else if (status === "error" && error) {
        dispatch({ type: "SET_CONNECTION_ERROR", payload: error });
      }
    }, []),
    updatePipelineStatus: useCallback((status) => {
      dispatch({ type: "UPDATE_PIPELINE_STATUS", payload: status });
    }, []),
    addProcessingFile: useCallback((file) => {
      dispatch({ type: "ADD_PROCESSING_FILE", payload: file });
    }, []),
    updateFileProgress: useCallback(
      (
        filename: string,
        progress: number,
        stage: "extraction" | "chunking" | "embedding" | "storing"
      ) => {
        dispatch({
          type: "UPDATE_FILE_PROGRESS",
          payload: { filename, progress, stage },
        });
      },
      []
    ),
    completeFile: useCallback((filename, results) => {
      dispatch({ type: "COMPLETE_FILE", payload: { filename, results } });
    }, []),
    failFile: useCallback((filename, error) => {
      dispatch({ type: "FAIL_FILE", payload: { filename, error } });
    }, []),
  };

  // Health monitoring
  const [connectionHealth, setConnectionHealth] = React.useState({
    isHealthy: false,
    reconnectAttempts: 0,
    latency: undefined as number | undefined,
    transport: undefined as string | undefined,
  });

  useEffect(() => {
    if (autoConnect && pipelineType) {
      connect(pipelineType);
    }

    // Start health monitoring
    healthMonitor.startMonitoring();
    const unsubscribeHealth = healthMonitor.onHealthChange((health) => {
      setConnectionHealth({
        isHealthy: health.isConnected,
        latency: health.latency,
        transport: health.transport,
        reconnectAttempts: health.reconnectAttempts,
      });
    });

    // Set up HTTP fallback event listeners
    const handleHttpUpdate = (event: CustomEvent) => {
      if (fallbackHandler.isActive()) {
        console.log("[SOCKET-PROVIDER] Received HTTP fallback data");
        // Transform HTTP data to match WebSocket events
        const data = event.detail;
        dispatch({ type: "UPDATE_PIPELINE_STATUS", payload: data });
      }
    };

    const handleFallbackActive = () => {
      console.log("[SOCKET-PROVIDER] HTTP fallback is now active");
    };

    const handleFallbackDisabled = () => {
      console.log(
        "[SOCKET-PROVIDER] HTTP fallback disabled, WebSocket restored"
      );
    };

    if (typeof window !== "undefined") {
      window.addEventListener(
        "rag-status-http-update",
        handleHttpUpdate as EventListener
      );
      window.addEventListener(
        "rag-socket-fallback-active",
        handleFallbackActive
      );
      window.addEventListener(
        "rag-socket-fallback-disabled",
        handleFallbackDisabled
      );
    }

    return () => {
      healthMonitor.stopMonitoring();
      unsubscribeHealth();
      fallbackHandler.cleanup();

      if (typeof window !== "undefined") {
        window.removeEventListener(
          "rag-status-http-update",
          handleHttpUpdate as EventListener
        );
        window.removeEventListener(
          "rag-socket-fallback-active",
          handleFallbackActive
        );
        window.removeEventListener(
          "rag-socket-fallback-disabled",
          handleFallbackDisabled
        );
      }
    };
  }, [autoConnect, pipelineType, connect, healthMonitor, fallbackHandler]);

  const contextValue: RAGSocketContextType = {
    state,
    actions,
    socket: socketClient.socket,
    connectionHealth,
  };

  return (
    <SocketContext.Provider value={contextValue}>
      {children}
    </SocketContext.Provider>
  );
}

// Hook to use the socket context
export function useSocket(): RAGSocketContextType {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error("useSocket must be used within a SocketProvider");
  }
  return context;
}

// Specific hooks for common use cases
export function useRAGStatus() {
  const { state, connectionHealth } = useSocket();
  return {
    isOnline: state.isConnected && state.status === "online",
    isProcessing: state.is_checking || state.files_processing.length > 0,
    processingFiles: state.files_processing,
    completedFiles: state.files_completed,
    failedFiles: state.files_failed,
    stats: {
      totalProcessed: state.total_processed,
      totalFailed: state.total_failed,
      successRate:
        state.total_processed / (state.total_processed + state.total_failed) ||
        0,
    },
    connectionHealth,
    nextCheckIn: state.seconds_until_next_check,
  };
}

export function useFileProcessing() {
  const { state, actions } = useSocket();

  return {
    processingFiles: state.files_processing,
    isProcessing: state.files_processing.length > 0,
    addFile: (filename: string, fileId?: string) => {
      actions.addProcessingFile({
        name: filename,
        id: fileId,
        started_at: new Date().toISOString(),
      });
    },
    updateProgress: actions.updateFileProgress,
    completeFile: actions.completeFile,
    failFile: actions.failFile,
  };
}
