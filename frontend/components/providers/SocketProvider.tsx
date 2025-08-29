'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io } from 'socket.io-client';
import type { Socket } from 'socket.io-client';
import { ServerToClientEvents, ClientToServerEvents } from '@/lib/types/socket';

type SocketContextType = {
  socket: Socket<ServerToClientEvents, ClientToServerEvents> | null;
  isConnected: boolean;
};

const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false,
});

interface SocketProviderProps {
  children: ReactNode;
}

export function SocketProvider({ children }: SocketProviderProps) {
  const [socket, setSocket] = useState<Socket<ServerToClientEvents, ClientToServerEvents> | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socketInstance = io(process.env.NEXT_PUBLIC_RAG_SOCKET_URL || 'http://localhost:8002', {
      autoConnect: true,
    });

    socketInstance.on('connect', () => {
      console.log('[SOCKET-PROVIDER-connect] Connected to socket server with ID:', socketInstance.id);
      setIsConnected(true);
      
      // Identify this client as frontend for proper message routing
      socketInstance.emit('message', {
        type: 'identify',
        client: 'frontend',
        message: 'Frontend client connected and ready for processing notifications'
      });
      console.log('[SOCKET-PROVIDER-connect] Sent frontend client identification for ID:', socketInstance.id);
    });

    socketInstance.on('disconnect', () => {
      console.log('[SOCKET-PROVIDER-disconnect] Disconnected from socket server');
      setIsConnected(false);
    });

    socketInstance.on('connect_error', (error) => {
      console.error('[SOCKET-PROVIDER-connect_error] Connection error:', error);
      setIsConnected(false);
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
}

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};