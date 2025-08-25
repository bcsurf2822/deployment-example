'use client';

interface FallbackConfig {
  enabled: boolean;
  httpFallbackUrl: string;
  retryAttempts: number;
  retryDelay: number;
  healthCheckInterval: number;
}

export class SocketFallbackHandler {
  private config: FallbackConfig;
  private isUsingFallback = false;
  private fallbackInterval?: NodeJS.Timeout;
  private retryAttempts = 0;
  private maxRetries = 3;
  private baseRetryDelay = 2000;

  constructor(config?: Partial<FallbackConfig>) {
    this.config = {
      enabled: true,
      httpFallbackUrl: '/api/rag-status',
      retryAttempts: 3,
      retryDelay: 5000,
      healthCheckInterval: 30000,
      ...config
    };
  }

  handleConnectionFailure(): void {
    if (!this.config.enabled) {
      console.log('[SOCKET-FALLBACK] Fallback disabled, not switching to HTTP polling');
      return;
    }

    this.retryAttempts++;
    
    if (this.retryAttempts >= this.maxRetries && !this.isUsingFallback) {
      console.log('[SOCKET-FALLBACK] Max reconnection attempts reached, switching to HTTP polling');
      this.switchToHttpFallback();
    } else {
      console.log(`[SOCKET-FALLBACK] Connection failed, attempt ${this.retryAttempts}/${this.maxRetries}`);
    }
  }

  handleConnectionSuccess(): void {
    if (this.isUsingFallback) {
      console.log('[SOCKET-FALLBACK] WebSocket connection restored, disabling HTTP fallback');
      this.disableFallback();
    }
    
    this.retryAttempts = 0;
  }

  private switchToHttpFallback(): void {
    console.log('[SOCKET-FALLBACK] Enabling HTTP polling fallback');
    this.isUsingFallback = true;

    // Start polling the HTTP endpoint
    this.startHttpPolling();

    // Notify application that fallback is active
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('rag-socket-fallback-active', {
        detail: { fallbackUrl: this.config.httpFallbackUrl }
      }));
    }
  }

  private disableFallback(): void {
    this.isUsingFallback = false;
    
    if (this.fallbackInterval) {
      clearInterval(this.fallbackInterval);
      this.fallbackInterval = undefined;
    }

    // Notify application that fallback is disabled
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('rag-socket-fallback-disabled'));
    }
  }

  private startHttpPolling(): void {
    if (this.fallbackInterval) return;

    this.fallbackInterval = setInterval(async () => {
      try {
        const response = await fetch(this.config.httpFallbackUrl);
        
        if (response.ok) {
          const data = await response.json();
          
          // Emit custom event with HTTP-fetched data
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('rag-status-http-update', {
              detail: data
            }));
          }
        } else {
          console.warn(`[SOCKET-FALLBACK] HTTP fallback request failed: ${response.status}`);
        }
      } catch (error) {
        console.error('[SOCKET-FALLBACK] HTTP fallback error:', error);
      }
    }, this.config.healthCheckInterval);
  }

  isActive(): boolean {
    return this.isUsingFallback;
  }

  getRetryAttempts(): number {
    return this.retryAttempts;
  }

  cleanup(): void {
    this.disableFallback();
  }

  // Update configuration
  updateConfig(newConfig: Partial<FallbackConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}