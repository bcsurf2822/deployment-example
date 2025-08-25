'use client';

import { getSocketClient } from './socket';

interface HealthMetrics {
  isConnected: boolean;
  latency?: number;
  transport?: string;
  reconnectAttempts: number;
  lastError?: Error;
  connectionUptime?: number;
}

type HealthChangeListener = (health: HealthMetrics) => void;

class SocketHealthMonitor {
  private static instance: SocketHealthMonitor;
  private healthCheckInterval?: NodeJS.Timeout;
  private listeners: HealthChangeListener[] = [];
  private currentHealth: HealthMetrics = {
    isConnected: false,
    reconnectAttempts: 0
  };
  private startTime?: number;
  private isMonitoring = false;

  private constructor() {}

  static getInstance(): SocketHealthMonitor {
    if (!SocketHealthMonitor.instance) {
      SocketHealthMonitor.instance = new SocketHealthMonitor();
    }
    return SocketHealthMonitor.instance;
  }

  startMonitoring(intervalMs: number = 30000): void {
    if (this.isMonitoring) return;

    console.log('[SOCKET-HEALTH] Starting health monitoring');
    this.isMonitoring = true;
    this.startTime = Date.now();

    // Initial health check
    this.checkHealth();

    // Set up periodic health checks
    this.healthCheckInterval = setInterval(() => {
      this.checkHealth();
    }, intervalMs);
  }

  stopMonitoring(): void {
    if (!this.isMonitoring) return;

    console.log('[SOCKET-HEALTH] Stopping health monitoring');
    this.isMonitoring = false;

    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = undefined;
    }
  }

  private async checkHealth(): Promise<void> {
    const socketClient = getSocketClient();
    const socket = socketClient.socket;

    const newHealth: HealthMetrics = {
      isConnected: socketClient.isConnected,
      reconnectAttempts: this.currentHealth.reconnectAttempts,
      connectionUptime: this.startTime ? Date.now() - this.startTime : undefined
    };

    if (socket?.connected) {
      // Check latency with ping
      try {
        const latency = await socketClient.ping();
        newHealth.latency = latency;
        newHealth.transport = socket.io.engine.transport.name;
        
        // Reset reconnect attempts on successful ping
        newHealth.reconnectAttempts = 0;
      } catch (error) {
        console.warn('[SOCKET-HEALTH] Ping failed:', error);
        newHealth.lastError = error instanceof Error ? error : new Error('Ping failed');
      }

      // Listen for reconnection attempts
      if (!this.hasEventListener(socket, 'reconnect_attempt')) {
        socket.on('reconnect_attempt', (attemptNumber) => {
          this.currentHealth.reconnectAttempts = attemptNumber;
          this.notifyListeners();
        });
      }

      if (!this.hasEventListener(socket, 'reconnect')) {
        socket.on('reconnect', () => {
          this.currentHealth.reconnectAttempts = 0;
          this.notifyListeners();
        });
      }
    }

    // Update and notify if health changed
    if (this.hasHealthChanged(newHealth)) {
      this.currentHealth = newHealth;
      this.notifyListeners();
    }
  }

  private hasEventListener(socket: any, eventName: string): boolean {
    return socket.listeners(eventName).length > 0;
  }

  private hasHealthChanged(newHealth: HealthMetrics): boolean {
    const current = this.currentHealth;
    
    return (
      current.isConnected !== newHealth.isConnected ||
      current.latency !== newHealth.latency ||
      current.transport !== newHealth.transport ||
      current.reconnectAttempts !== newHealth.reconnectAttempts ||
      current.lastError?.message !== newHealth.lastError?.message
    );
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.currentHealth);
      } catch (error) {
        console.error('[SOCKET-HEALTH] Error in health change listener:', error);
      }
    });
  }

  onHealthChange(listener: HealthChangeListener): () => void {
    this.listeners.push(listener);
    
    // Immediately call listener with current health
    listener(this.currentHealth);

    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  getHealth(): HealthMetrics {
    return { ...this.currentHealth };
  }

  isHealthy(): boolean {
    const health = this.currentHealth;
    return (
      health.isConnected &&
      (health.latency === undefined || health.latency < 5000) && // Less than 5 second latency
      health.reconnectAttempts < 3 // Less than 3 reconnection attempts
    );
  }
}

export function getSocketHealthMonitor(): SocketHealthMonitor {
  return SocketHealthMonitor.getInstance();
}