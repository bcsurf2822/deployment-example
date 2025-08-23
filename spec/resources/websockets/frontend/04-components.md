# React Component Updates for Socket.IO Integration

## 1. Socket.IO Context Provider

### Create Socket Context

Create `components/providers/SocketProvider.tsx`:

```typescript
'use client';

import React, { createContext, useContext, useEffect, useReducer, useCallback } from 'react';
import { getSocketClient } from '@/lib/socket';
import { getSocketHealthMonitor } from '@/lib/socket-health';
import { SocketFallbackHandler } from '@/lib/socket-fallback';
import {
  RAGSocketContextType,
  RAGPipelineState,
  RAGPipelineActions,
  EnhancedFileInfo
} from '@/lib/types/rag-status';
import {
  ServerToClientEvents,
  FileProcessingEvent,
  FileCompletedEvent,
  FileFailedEvent,
  PipelineStatusEvent
} from '@/lib/types/socket';

// Initial state
const initialState: RAGPipelineState = {
  isConnected: false,
  isConnecting: false,
  status: 'offline',
  files_processing: [],
  files_completed: [],
  files_failed: [],
  total_processed: 0,
  total_failed: 0,
  check_interval: 60,
  is_checking: false,
  reconnect_attempts: 0
};

// Action types
type SocketAction = 
  | { type: 'SET_CONNECTING'; payload: boolean }
  | { type: 'SET_CONNECTED'; payload: boolean }
  | { type: 'SET_CONNECTION_ERROR'; payload: string }
  | { type: 'UPDATE_PIPELINE_STATUS'; payload: Partial<RAGPipelineState> }
  | { type: 'ADD_PROCESSING_FILE'; payload: EnhancedFileInfo }
  | { type: 'UPDATE_FILE_PROGRESS'; payload: { filename: string; progress: number; stage: string } }
  | { type: 'COMPLETE_FILE'; payload: { filename: string; results: any } }
  | { type: 'FAIL_FILE'; payload: { filename: string; error: any } }
  | { type: 'SET_RECONNECT_ATTEMPTS'; payload: number }
  | { type: 'RESET_STATE' };

// Reducer
function socketReducer(state: RAGPipelineState, action: SocketAction): RAGPipelineState {
  switch (action.type) {
    case 'SET_CONNECTING':
      return { ...state, isConnecting: action.payload, connectionError: undefined };
    
    case 'SET_CONNECTED':
      return { 
        ...state, 
        isConnected: action.payload,
        isConnecting: false,
        connectionError: action.payload ? undefined : state.connectionError,
        lastConnected: action.payload ? new Date() : state.lastConnected
      };
    
    case 'SET_CONNECTION_ERROR':
      return { 
        ...state, 
        connectionError: action.payload,
        isConnecting: false,
        isConnected: false
      };
    
    case 'UPDATE_PIPELINE_STATUS':
      return { ...state, ...action.payload };
    
    case 'ADD_PROCESSING_FILE':
      return {
        ...state,
        files_processing: [...state.files_processing, action.payload]
      };
    
    case 'UPDATE_FILE_PROGRESS':
      return {
        ...state,
        files_processing: state.files_processing.map(file => 
          file.name === action.payload.filename
            ? { ...file, progress: action.payload.progress, stage: action.payload.stage as any }
            : file
        )
      };
    
    case 'COMPLETE_FILE':
      const completingFile = state.files_processing.find(f => f.name === action.payload.filename);
      if (!completingFile) return state;
      
      const completedFile = { 
        ...completingFile, 
        completed_at: new Date().toISOString(),
        results: action.payload.results
      };
      
      return {
        ...state,
        files_processing: state.files_processing.filter(f => f.name !== action.payload.filename),
        files_completed: [completedFile, ...state.files_completed].slice(0, 10), // Keep last 10
        total_processed: state.total_processed + 1
      };
    
    case 'FAIL_FILE':
      const failingFile = state.files_processing.find(f => f.name === action.payload.filename);
      if (!failingFile) return state;
      
      const failedFile = {
        ...failingFile,
        completed_at: new Date().toISOString(),
        error: action.payload.error
      };
      
      return {
        ...state,
        files_processing: state.files_processing.filter(f => f.name !== action.payload.filename),
        files_failed: [failedFile, ...state.files_failed].slice(0, 5), // Keep last 5
        total_failed: state.total_failed + 1
      };
    
    case 'SET_RECONNECT_ATTEMPTS':
      return { ...state, reconnect_attempts: action.payload };
    
    case 'RESET_STATE':
      return { ...initialState };
    
    default:
      return state;
  }
}

// Context
const SocketContext = createContext<RAGSocketContextType | undefined>(undefined);

// Provider props
interface SocketProviderProps {
  children: React.ReactNode;
  pipelineType?: 'google_drive' | 'local_files';
  autoConnect?: boolean;
  fallbackEnabled?: boolean;
}

// Provider component
export function SocketProvider({ 
  children, 
  pipelineType, 
  autoConnect = true,
  fallbackEnabled = true 
}: SocketProviderProps) {
  const [state, dispatch] = useReducer(socketReducer, initialState);
  const socketClient = getSocketClient();
  const healthMonitor = getSocketHealthMonitor();
  const fallbackHandler = new SocketFallbackHandler();

  // Connection management
  const connect = useCallback((type: 'google_drive' | 'local_files') => {
    dispatch({ type: 'SET_CONNECTING', payload: true });
    
    try {
      const socket = socketClient.connect(type);
      
      // Set up event listeners
      socket.on('connect', () => {
        dispatch({ type: 'SET_CONNECTED', payload: true });
        fallbackHandler.handleConnectionSuccess();
      });
      
      socket.on('disconnect', (reason) => {
        dispatch({ type: 'SET_CONNECTED', payload: false });
        if (reason === 'io server disconnect') {
          fallbackHandler.handleConnectionFailure();
        }
      });
      
      socket.on('connect_error', (error) => {
        dispatch({ type: 'SET_CONNECTION_ERROR', payload: error.message });
        fallbackHandler.handleConnectionFailure();
      });
      
      socket.on('reconnect_attempt', (attemptNumber) => {
        dispatch({ type: 'SET_RECONNECT_ATTEMPTS', payload: attemptNumber });
      });
      
      // Pipeline events
      socket.on('pipeline:status', (data: PipelineStatusEvent) => {
        dispatch({ type: 'UPDATE_PIPELINE_STATUS', payload: {
          pipeline_id: data.pipeline_id,
          pipeline_type: data.pipeline_type as any,
          status: data.status as any,
          files_processing: data.files_processing,
          files_completed: data.files_completed,
          files_failed: data.files_failed,
          total_processed: data.total_processed,
          total_failed: data.total_failed,
          last_check_time: data.last_check_time,
          next_check_time: data.next_check_time,
          check_interval: data.check_interval,
          is_checking: data.is_checking,
          seconds_until_next_check: data.seconds_until_next_check,
          last_activity: data.last_activity
        }});
      });
      
      socket.on('file:processing', (data: FileProcessingEvent) => {
        dispatch({ type: 'ADD_PROCESSING_FILE', payload: {
          ...data.file,
          stage: data.processing_stage
        }});
      });
      
      socket.on('file:progress', (data) => {
        dispatch({ type: 'UPDATE_FILE_PROGRESS', payload: {
          filename: data.file.name,
          progress: data.progress,
          stage: data.processing_stage
        }});
      });
      
      socket.on('file:completed', (data: FileCompletedEvent) => {
        dispatch({ type: 'COMPLETE_FILE', payload: {
          filename: data.file.name,
          results: data.results
        }});
      });
      
      socket.on('file:failed', (data: FileFailedEvent) => {
        dispatch({ type: 'FAIL_FILE', payload: {
          filename: data.file.name,
          error: data.error
        }});
      });
      
      // Subscribe to pipeline updates
      socketClient.subscribe(type);
      
    } catch (error) {
      dispatch({ type: 'SET_CONNECTION_ERROR', payload: (error as Error).message });
    }
  }, [socketClient, fallbackHandler]);

  const disconnect = useCallback(() => {
    socketClient.disconnect();
    dispatch({ type: 'RESET_STATE' });
  }, [socketClient]);

  const subscribe = useCallback((type: 'google_drive' | 'local_files') => {
    socketClient.subscribe(type);
  }, [socketClient]);

  const unsubscribe = useCallback((type: 'google_drive' | 'local_files') => {
    socketClient.unsubscribe(type);
  }, [socketClient]);

  // Actions object
  const actions: RAGPipelineActions = {
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    updateConnectionStatus: useCallback((status, error) => {
      if (status === 'connected') {
        dispatch({ type: 'SET_CONNECTED', payload: true });
      } else if (status === 'disconnected') {
        dispatch({ type: 'SET_CONNECTED', payload: false });
      } else if (status === 'error' && error) {
        dispatch({ type: 'SET_CONNECTION_ERROR', payload: error });
      }
    }, []),
    updatePipelineStatus: useCallback((status) => {
      dispatch({ type: 'UPDATE_PIPELINE_STATUS', payload: status });
    }, []),
    addProcessingFile: useCallback((file) => {
      dispatch({ type: 'ADD_PROCESSING_FILE', payload: file });
    }, []),
    updateFileProgress: useCallback((filename, progress, stage) => {
      dispatch({ type: 'UPDATE_FILE_PROGRESS', payload: { filename, progress, stage } });
    }, []),
    completeFile: useCallback((filename, results) => {
      dispatch({ type: 'COMPLETE_FILE', payload: { filename, results } });
    }, []),
    failFile: useCallback((filename, error) => {
      dispatch({ type: 'FAIL_FILE', payload: { filename, error } });
    }, [])
  };

  // Health monitoring
  const [connectionHealth, setConnectionHealth] = React.useState({
    isHealthy: false,
    reconnectAttempts: 0
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
        reconnectAttempts: health.reconnectAttempts
      });
    });

    return () => {
      healthMonitor.stopMonitoring();
      unsubscribeHealth();
      fallbackHandler.cleanup();
    };
  }, [autoConnect, pipelineType, connect, healthMonitor, fallbackHandler]);

  const contextValue: RAGSocketContextType = {
    state,
    actions,
    socket: socketClient.socket,
    connectionHealth
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
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
}

// Specific hooks for common use cases
export function useRAGStatus() {
  const { state, connectionHealth } = useSocket();
  return {
    isOnline: state.isConnected && state.status === 'online',
    isProcessing: state.is_checking || state.files_processing.length > 0,
    processingFiles: state.files_processing,
    completedFiles: state.files_completed,
    failedFiles: state.files_failed,
    stats: {
      totalProcessed: state.total_processed,
      totalFailed: state.total_failed,
      successRate: state.total_processed / (state.total_processed + state.total_failed) || 0
    },
    connectionHealth,
    nextCheckIn: state.seconds_until_next_check
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
        started_at: new Date().toISOString()
      });
    },
    updateProgress: actions.updateFileProgress,
    completeFile: actions.completeFile,
    failFile: actions.failFile
  };
}
```

## 2. Updated RAGPipelineStatus Component

Update `components/rag-pipelines/RAGPipelineStatus.tsx`:

```typescript
'use client';

import React, { useEffect, useState } from 'react';
import { useSocket, useRAGStatus } from '@/components/providers/SocketProvider';
import { EnhancedFileInfo } from '@/lib/types/rag-status';

// Connection status indicator component
function ConnectionStatus({ isConnected, connectionHealth, className = '' }: {
  isConnected: boolean;
  connectionHealth: any;
  className?: string;
}) {
  const getStatusColor = () => {
    if (isConnected && connectionHealth.isHealthy) return 'bg-green-500';
    if (isConnected) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getStatusText = () => {
    if (isConnected && connectionHealth.isHealthy) return 'Connected';
    if (isConnected) return 'Connected (degraded)';
    if (connectionHealth.reconnectAttempts > 0) return `Reconnecting... (${connectionHealth.reconnectAttempts})`;
    return 'Disconnected';
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
      <span className="text-sm font-medium">{getStatusText()}</span>
      {connectionHealth.latency && (
        <span className="text-xs text-gray-500">
          {connectionHealth.latency}ms
        </span>
      )}
      {connectionHealth.transport && (
        <span className="text-xs text-gray-400 uppercase">
          {connectionHealth.transport}
        </span>
      )}
    </div>
  );
}

// File processing item component
function FileProcessingItem({ file, type }: { 
  file: EnhancedFileInfo; 
  type: 'processing' | 'completed' | 'failed';
}) {
  const getStatusIcon = () => {
    switch (type) {
      case 'processing':
        return (
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        );
      case 'completed':
        return <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">✓</div>;
      case 'failed':
        return <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">✗</div>;
    }
  };

  const getProgressBar = () => {
    if (type !== 'processing' || !file.progress) return null;
    
    return (
      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
        <div 
          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${file.progress * 100}%` }}
        />
      </div>
    );
  };

  const getFileDetails = () => {
    if (type === 'completed' && file.results) {
      return (
        <div className="text-xs text-gray-600 mt-1">
          {file.results.chunks_created} chunks, {file.results.embeddings_generated} embeddings
          {file.processing_duration && ` (${(file.processing_duration / 1000).toFixed(1)}s)`}
        </div>
      );
    }
    
    if (type === 'failed' && file.error) {
      return (
        <div className="text-xs text-red-600 mt-1">
          {file.error.message} ({file.error.stage})
        </div>
      );
    }
    
    if (type === 'processing' && file.stage) {
      return (
        <div className="text-xs text-blue-600 mt-1">
          {file.stage}...
        </div>
      );
    }
    
    return null;
  };

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="flex items-start space-x-3 p-3 border-b border-gray-100">
      {getStatusIcon()}
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-900">{file.name}</span>
          <span className="text-xs text-gray-500">
            {formatTime(file.started_at || file.completed_at)}
          </span>
        </div>
        {getFileDetails()}
        {getProgressBar()}
      </div>
    </div>
  );
}

// Statistics component
function ProcessingStats({ stats, nextCheckIn }: {
  stats: { totalProcessed: number; totalFailed: number; successRate: number };
  nextCheckIn?: number;
}) {
  const [timeRemaining, setTimeRemaining] = useState(nextCheckIn || 0);

  useEffect(() => {
    if (!nextCheckIn) return;
    
    setTimeRemaining(nextCheckIn);
    const interval = setInterval(() => {
      setTimeRemaining(prev => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(interval);
  }, [nextCheckIn]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
      <div className="text-center">
        <div className="text-2xl font-bold text-green-600">{stats.totalProcessed}</div>
        <div className="text-sm text-gray-600">Processed</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-red-600">{stats.totalFailed}</div>
        <div className="text-sm text-gray-600">Failed</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-blue-600">
          {(stats.successRate * 100).toFixed(1)}%
        </div>
        <div className="text-sm text-gray-600">Success Rate</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-gray-600">
          {timeRemaining > 0 ? formatTime(timeRemaining) : '--:--'}
        </div>
        <div className="text-sm text-gray-600">Next Check</div>
      </div>
    </div>
  );
}

// Main component
export default function RAGPipelineStatus() {
  const { state, actions, connectionHealth } = useSocket();
  const { 
    isOnline, 
    isProcessing, 
    processingFiles, 
    completedFiles, 
    failedFiles, 
    stats, 
    nextCheckIn 
  } = useRAGStatus();

  // Auto-connect on mount (if not already connected)
  useEffect(() => {
    if (!state.isConnected && !state.isConnecting) {
      // Default to google_drive, but this could be configurable
      actions.connect('google_drive');
    }
  }, [state.isConnected, state.isConnecting, actions]);

  // Connection controls
  const handleConnect = (pipelineType: 'google_drive' | 'local_files') => {
    actions.connect(pipelineType);
  };

  const handleDisconnect = () => {
    actions.disconnect();
  };

  if (state.connectionError) {
    return (
      <div className="p-6 bg-red-50 rounded-lg">
        <h2 className="text-lg font-semibold text-red-800 mb-2">Connection Error</h2>
        <p className="text-red-700 mb-4">{state.connectionError}</p>
        <div className="flex space-x-2">
          <button
            onClick={() => handleConnect('google_drive')}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry Google Drive
          </button>
          <button
            onClick={() => handleConnect('local_files')}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry Local Files
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with connection status */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">RAG Pipeline Status</h2>
        <ConnectionStatus 
          isConnected={state.isConnected}
          connectionHealth={connectionHealth}
        />
      </div>

      {/* Processing statistics */}
      <ProcessingStats stats={stats} nextCheckIn={nextCheckIn} />

      {/* Pipeline controls */}
      <div className="flex space-x-2">
        <button
          onClick={() => handleConnect('google_drive')}
          disabled={state.isConnected && state.pipeline_type === 'google_drive'}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          Google Drive
        </button>
        <button
          onClick={() => handleConnect('local_files')}
          disabled={state.isConnected && state.pipeline_type === 'local_files'}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
        >
          Local Files
        </button>
        <button
          onClick={handleDisconnect}
          disabled={!state.isConnected}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-400"
        >
          Disconnect
        </button>
      </div>

      {/* File processing sections */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Currently Processing */}
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b">
            <h3 className="font-medium text-gray-900">
              Processing ({processingFiles.length})
            </h3>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {processingFiles.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                {isOnline ? 'No files processing' : 'Pipeline offline'}
              </div>
            ) : (
              processingFiles.map((file, index) => (
                <FileProcessingItem key={`processing-${file.name}-${index}`} file={file} type="processing" />
              ))
            )}
          </div>
        </div>

        {/* Recently Completed */}
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b">
            <h3 className="font-medium text-gray-900">
              Completed ({completedFiles.length})
            </h3>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {completedFiles.length === 0 ? (
              <div className="p-4 text-center text-gray-500">No completed files</div>
            ) : (
              completedFiles.map((file, index) => (
                <FileProcessingItem key={`completed-${file.name}-${index}`} file={file} type="completed" />
              ))
            )}
          </div>
        </div>

        {/* Recently Failed */}
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b">
            <h3 className="font-medium text-gray-900">
              Failed ({failedFiles.length})
            </h3>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {failedFiles.length === 0 ? (
              <div className="p-4 text-center text-gray-500">No failed files</div>
            ) : (
              failedFiles.map((file, index) => (
                <FileProcessingItem key={`failed-${file.name}-${index}`} file={file} type="failed" />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Debug information (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <details className="p-4 bg-gray-100 rounded">
          <summary className="cursor-pointer font-medium">Debug Information</summary>
          <pre className="mt-2 text-xs overflow-auto">
            {JSON.stringify({ state, connectionHealth }, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}
```

## 3. App Layout Integration

Update `app/layout.tsx` to include the SocketProvider:

```typescript
import { SocketProvider } from '@/components/providers/SocketProvider';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <SocketProvider autoConnect={true} fallbackEnabled={true}>
          {children}
        </SocketProvider>
      </body>
    </html>
  );
}
```

## 4. RAG Pipeline Page Integration

Update `app/rag-pipelines/page.tsx`:

```typescript
import { Suspense } from 'react';
import RAGPipelineStatus from '@/components/rag-pipelines/RAGPipelineStatus';

function RAGPipelineLoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-6 w-48 bg-gray-200 rounded" />
        <div className="h-4 w-32 bg-gray-200 rounded" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="p-4 bg-gray-100 rounded-lg">
            <div className="h-8 w-16 bg-gray-200 rounded mb-2" />
            <div className="h-4 w-20 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RAGPipelinesPage() {
  return (
    <div className="container mx-auto p-6">
      <Suspense fallback={<RAGPipelineLoadingSkeleton />}>
        <RAGPipelineStatus />
      </Suspense>
    </div>
  );
}
```

This component architecture provides a complete real-time interface for monitoring RAG pipeline status with Socket.IO integration, including connection management, file processing visualization, and fallback handling.