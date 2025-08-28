interface ServerToClientEvents {
  message: (data: unknown) => void;
  broadcast: (data: { message: string; timestamp: number; userId?: string }) => void;
  'broadcast-received': (data: { 
    type: string; 
    original_message: string; 
    message: string; 
    timestamp: string; 
    from_server: boolean 
  }) => void;
  'upload-complete': (data: {
    fileName: string;
    googleDriveId: string;
    fileSize: number;
    timestamp: string;
    from_server: boolean;
  }) => void;
  'processing-started': (data: {
    fileName: string;
    googleDriveId: string;
    pipelineType: string;
    timestamp: string;
    from_server: boolean;
  }) => void;
  'processing-complete': (data: {
    fileName: string;
    googleDriveId: string;
    pipelineType: string;
    timestamp: string;
    from_server: boolean;
  }) => void;
  'processing-failed': (data: {
    fileName: string;
    googleDriveId: string;
    pipelineType: string;
    error: string;
    timestamp: string;
    from_server: boolean;
  }) => void;
}

interface ClientToServerEvents {
  message: (data: unknown) => void;
  broadcast: (data: { message: string; userId?: string }) => void;
  'upload-complete': (data: { fileName: string; googleDriveId: string; fileSize: number }) => void;
  'processing-started': (data: {
    fileName: string;
    googleDriveId: string;
    pipelineType: string;
    timestamp: string;
  }) => void;
  'processing-complete': (data: {
    fileName: string;
    googleDriveId: string;
    pipelineType: string;
    timestamp: string;
  }) => void;
  'processing-failed': (data: {
    fileName: string;
    googleDriveId: string;
    pipelineType: string;
    error: string;
    timestamp: string;
  }) => void;
}

export type {
  ServerToClientEvents,
  ClientToServerEvents
};