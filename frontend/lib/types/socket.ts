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
}

interface ClientToServerEvents {
  message: (data: unknown) => void;
  broadcast: (data: { message: string; userId?: string }) => void;
}

export type {
  ServerToClientEvents,
  ClientToServerEvents
};