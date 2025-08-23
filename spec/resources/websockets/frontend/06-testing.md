# Frontend Testing for Socket.IO Integration

## Testing Strategy Overview

The frontend testing approach covers Socket.IO client functionality, React component behavior with real-time updates, and fallback scenarios.

## 1. Unit Tests for Socket.IO Client

### Test Socket.IO Client Module

Create `__tests__/lib/socket.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { io } from 'socket.io-client';
import { getSocketClient, connectToRAGPipeline, disconnectFromRAGPipeline } from '@/lib/socket';

// Mock socket.io-client
vi.mock('socket.io-client', () => ({
  io: vi.fn()
}));

describe('Socket.IO Client', () => {
  let mockSocket: any;
  
  beforeEach(() => {
    mockSocket = {
      connected: false,
      id: 'test-socket-id',
      io: { engine: { transport: { name: 'websocket' } } },
      on: vi.fn(),
      off: vi.fn(),
      once: vi.fn(),
      emit: vi.fn(),
      connect: vi.fn(),
      disconnect: vi.fn()
    };
    
    (io as Mock).mockReturnValue(mockSocket);
    
    // Reset environment variables
    process.env.NEXT_PUBLIC_SOCKET_IO_URL = 'http://localhost:8103';
    process.env.NEXT_PUBLIC_SOCKET_TIMEOUT = '5000';
  });
  
  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('getSocketClient', () => {
    it('should return singleton instance', () => {
      const client1 = getSocketClient();
      const client2 = getSocketClient();
      
      expect(client1).toBe(client2);
    });
  });

  describe('connect', () => {
    it('should create socket with correct configuration', () => {
      const client = getSocketClient();
      const socket = client.connect('google_drive');
      
      expect(io).toHaveBeenCalledWith('http://localhost:8103/google_drive', {
        timeout: 5000,
        retries: 3,
        transports: ['websocket', 'polling'],
        upgrade: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 10000,
        randomizationFactor: 0.5,
        extraHeaders: {
          'X-Pipeline-Type': 'google_drive'
        },
        query: {
          clientType: 'frontend',
          version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'
        },
        autoConnect: true,
        forceNew: false
      });
      
      expect(socket).toBe(mockSocket);
    });
    
    it('should set up event handlers', () => {
      const client = getSocketClient();
      client.connect('google_drive');
      
      expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('connect_error', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('reconnect', expect.any(Function));
      expect(mockSocket.on).toHaveBeenCalledWith('reconnect_attempt', expect.any(Function));
    });
    
    it('should return existing socket if already connected', () => {
      mockSocket.connected = true;
      
      const client = getSocketClient();
      const socket1 = client.connect('google_drive');
      const socket2 = client.connect('google_drive');
      
      expect(socket1).toBe(socket2);
      expect(io).toHaveBeenCalledTimes(1);
    });
  });

  describe('connection management', () => {
    it('should handle successful connection', () => {
      const client = getSocketClient();
      client.connect('google_drive');
      
      const connectHandler = mockSocket.on.mock.calls.find(call => call[0] === 'connect')[1];
      
      // Mock console.log to verify logging
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      connectHandler();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Connected to /google_drive')
      );
      
      consoleSpy.mockRestore();
    });
    
    it('should handle connection errors', () => {
      const client = getSocketClient();
      client.connect('google_drive');
      
      const errorHandler = mockSocket.on.mock.calls.find(call => call[0] === 'connect_error')[1];
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      const error = new Error('Connection failed');
      errorHandler(error);
      
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Connection error:'), error
      );
      
      consoleErrorSpy.mockRestore();
    });
  });

  describe('subscribe/unsubscribe', () => {
    it('should emit subscribe event when connected', () => {
      mockSocket.connected = true;
      
      const client = getSocketClient();
      client.connect('google_drive');
      client.subscribe('google_drive');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('subscribe', {
        pipeline_type: 'google_drive'
      });
    });
    
    it('should not emit subscribe when disconnected', () => {
      mockSocket.connected = false;
      
      const client = getSocketClient();
      client.connect('google_drive');
      client.subscribe('google_drive');
      
      expect(mockSocket.emit).not.toHaveBeenCalled();
    });
  });

  describe('utility functions', () => {
    it('connectToRAGPipeline should connect and subscribe', () => {
      const socket = connectToRAGPipeline('google_drive');
      
      expect(io).toHaveBeenCalled();
      expect(socket).toBe(mockSocket);
    });
    
    it('disconnectFromRAGPipeline should disconnect socket', () => {
      const client = getSocketClient();
      client.connect('google_drive');
      
      disconnectFromRAGPipeline();
      
      expect(mockSocket.disconnect).toHaveBeenCalled();
    });
  });
});
```

## 2. React Component Tests

### Test Socket Context Provider

Create `__tests__/components/providers/SocketProvider.test.tsx`:

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { SocketProvider, useSocket, useRAGStatus } from '@/components/providers/SocketProvider';
import { getSocketClient } from '@/lib/socket';

// Mock the socket client
vi.mock('@/lib/socket', () => ({
  getSocketClient: vi.fn()
}));

// Mock socket health monitor
vi.mock('@/lib/socket-health', () => ({
  getSocketHealthMonitor: vi.fn(() => ({
    startMonitoring: vi.fn(),
    stopMonitoring: vi.fn(),
    onHealthChange: vi.fn(() => () => {}) // Return unsubscribe function
  }))
}));

// Mock fallback handler
vi.mock('@/lib/socket-fallback', () => ({
  SocketFallbackHandler: vi.fn(() => ({
    handleConnectionSuccess: vi.fn(),
    handleConnectionFailure: vi.fn(),
    cleanup: vi.fn()
  }))
}));

describe('SocketProvider', () => {
  let mockSocketClient: any;
  let mockSocket: any;
  
  beforeEach(() => {
    mockSocket = {
      connected: false,
      id: 'test-socket-id',
      on: vi.fn(),
      off: vi.fn(),
      emit: vi.fn()
    };
    
    mockSocketClient = {
      connect: vi.fn(() => mockSocket),
      disconnect: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      isConnected: vi.fn(() => mockSocket.connected),
      getConnectionId: vi.fn(() => mockSocket.id),
      getTransport: vi.fn(() => 'websocket'),
      socket: mockSocket
    };
    
    (getSocketClient as any).mockReturnValue(mockSocketClient);
  });
  
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should provide socket context to children', () => {
    function TestComponent() {
      const { state } = useSocket();
      return <div data-testid="status">{state.status}</div>;
    }
    
    render(
      <SocketProvider>
        <TestComponent />
      </SocketProvider>
    );
    
    expect(screen.getByTestId('status')).toHaveTextContent('offline');
  });
  
  it('should auto-connect when pipelineType provided', async () => {
    function TestComponent() {
      return <div data-testid="test">Test</div>;
    }
    
    render(
      <SocketProvider pipelineType="google_drive" autoConnect={true}>
        <TestComponent />
      </SocketProvider>
    );
    
    await waitFor(() => {
      expect(mockSocketClient.connect).toHaveBeenCalledWith('google_drive');
      expect(mockSocketClient.subscribe).toHaveBeenCalledWith('google_drive');
    });
  });
  
  it('should handle connection events', async () => {
    function TestComponent() {
      const { state } = useSocket();
      return <div data-testid="connected">{state.isConnected.toString()}</div>;
    }
    
    render(
      <SocketProvider>
        <TestComponent />
      </SocketProvider>
    );
    
    // Simulate connection
    act(() => {
      const connectHandler = mockSocket.on.mock.calls.find(call => call[0] === 'connect')[1];
      connectHandler();
    });
    
    await waitFor(() => {
      expect(screen.getByTestId('connected')).toHaveTextContent('true');
    });
  });

  it('should handle pipeline status events', async () => {
    function TestComponent() {
      const { state } = useSocket();
      return <div data-testid="pipeline-id">{state.pipeline_id || 'none'}</div>;
    }
    
    render(
      <SocketProvider>
        <TestComponent />
      </SocketProvider>
    );
    
    // Simulate pipeline status event
    act(() => {
      const statusHandler = mockSocket.on.mock.calls.find(call => call[0] === 'pipeline:status')[1];
      statusHandler({
        pipeline_id: 'test-pipeline',
        pipeline_type: 'google_drive',
        status: 'online',
        files_processing: [],
        files_completed: [],
        files_failed: [],
        total_processed: 5,
        total_failed: 1,
        last_check_time: null,
        next_check_time: null,
        check_interval: 60,
        is_checking: false,
        last_activity: new Date().toISOString()
      });
    });
    
    await waitFor(() => {
      expect(screen.getByTestId('pipeline-id')).toHaveTextContent('test-pipeline');
    });
  });

  it('should handle file processing events', async () => {
    function TestComponent() {
      const { state } = useSocket();
      return <div data-testid="processing-count">{state.files_processing.length}</div>;
    }
    
    render(
      <SocketProvider>
        <TestComponent />
      </SocketProvider>
    );
    
    // Simulate file processing event
    act(() => {
      const processingHandler = mockSocket.on.mock.calls.find(call => call[0] === 'file:processing')[1];
      processingHandler({
        pipeline_id: 'test-pipeline',
        file: {
          name: 'test.pdf',
          id: 'file123',
          started_at: new Date().toISOString()
        },
        processing_stage: 'extraction',
        timestamp: new Date().toISOString()
      });
    });
    
    await waitFor(() => {
      expect(screen.getByTestId('processing-count')).toHaveTextContent('1');
    });
  });
});

describe('useRAGStatus hook', () => {
  let mockSocketClient: any;
  let mockSocket: any;
  
  beforeEach(() => {
    mockSocket = {
      connected: true,
      on: vi.fn(),
      off: vi.fn(),
      emit: vi.fn()
    };
    
    mockSocketClient = {
      connect: vi.fn(() => mockSocket),
      disconnect: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      socket: mockSocket
    };
    
    (getSocketClient as any).mockReturnValue(mockSocketClient);
  });
  
  it('should calculate processing statistics correctly', async () => {
    function TestComponent() {
      const { stats } = useRAGStatus();
      return (
        <div>
          <span data-testid="total-processed">{stats.totalProcessed}</span>
          <span data-testid="success-rate">{stats.successRate.toFixed(2)}</span>
        </div>
      );
    }
    
    // Create provider with initial state
    const TestWrapper = ({ children }: { children: React.ReactNode }) => (
      <SocketProvider>{children}</SocketProvider>
    );
    
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );
    
    // Initial state should show 0 processed
    expect(screen.getByTestId('total-processed')).toHaveTextContent('0');
    expect(screen.getByTestId('success-rate')).toHaveTextContent('0.00');
  });
});
```

## 3. Integration Tests

### Test Real-Time Updates

Create `__tests__/integration/websocket-integration.test.tsx`:

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SocketProvider } from '@/components/providers/SocketProvider';
import RAGPipelineStatus from '@/components/rag-pipelines/RAGPipelineStatus';

// Mock fetch for API calls
global.fetch = vi.fn();

describe('WebSocket Integration', () => {
  beforeEach(() => {
    // Mock successful Socket.IO info fetch
    (fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        available: true,
        url: 'http://localhost:8103',
        namespaces: ['/google_drive', '/local_files'],
        health: 'healthy'
      })
    });
  });
  
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should display real-time file processing updates', async () => {
    // Mock Socket.IO client
    const mockSocket = {
      connected: true,
      on: vi.fn(),
      off: vi.fn(),
      emit: vi.fn()
    };
    
    const mockClient = {
      connect: vi.fn(() => mockSocket),
      subscribe: vi.fn(),
      disconnect: vi.fn(),
      isConnected: vi.fn(() => true),
      socket: mockSocket
    };
    
    // Mock the socket client module
    vi.doMock('@/lib/socket', () => ({
      getSocketClient: () => mockClient,
      connectToRAGPipeline: vi.fn(() => mockSocket),
      disconnectFromRAGPipeline: vi.fn()
    }));
    
    render(
      <SocketProvider autoConnect={false}>
        <RAGPipelineStatus />
      </SocketProvider>
    );
    
    // Initially should show no files processing
    expect(screen.getByText(/Processing \(0\)/)).toBeInTheDocument();
    
    // Simulate file processing event
    act(() => {
      const processingHandler = mockSocket.on.mock.calls.find(call => call[0] === 'file:processing')[1];
      if (processingHandler) {
        processingHandler({
          pipeline_id: 'test-pipeline',
          file: {
            name: 'document.pdf',
            id: 'doc123',
            started_at: new Date().toISOString()
          },
          processing_stage: 'extraction',
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // Should now show 1 file processing
    await waitFor(() => {
      expect(screen.getByText(/Processing \(1\)/)).toBeInTheDocument();
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
      expect(screen.getByText('extraction...')).toBeInTheDocument();
    });
    
    // Simulate file completion
    act(() => {
      const completedHandler = mockSocket.on.mock.calls.find(call => call[0] === 'file:completed')[1];
      if (completedHandler) {
        completedHandler({
          pipeline_id: 'test-pipeline',
          file: {
            name: 'document.pdf',
            id: 'doc123',
            completed_at: new Date().toISOString()
          },
          results: {
            chunks_created: 5,
            embeddings_generated: 5,
            processing_duration: 2500,
            content_length: 1024
          },
          success: true,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // Should now show 0 processing, 1 completed
    await waitFor(() => {
      expect(screen.getByText(/Processing \(0\)/)).toBeInTheDocument();
      expect(screen.getByText(/Completed \(1\)/)).toBeInTheDocument();
      expect(screen.getByText('5 chunks, 5 embeddings')).toBeInTheDocument();
    });
  });
  
  it('should handle connection failures gracefully', async () => {
    const mockSocket = {
      connected: false,
      on: vi.fn(),
      off: vi.fn(),
      emit: vi.fn()
    };
    
    const mockClient = {
      connect: vi.fn(() => {
        throw new Error('Connection failed');
      }),
      subscribe: vi.fn(),
      disconnect: vi.fn(),
      isConnected: vi.fn(() => false),
      socket: null
    };
    
    vi.doMock('@/lib/socket', () => ({
      getSocketClient: () => mockClient
    }));
    
    render(
      <SocketProvider>
        <RAGPipelineStatus />
      </SocketProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Connection Error/)).toBeInTheDocument();
      expect(screen.getByText('Connection failed')).toBeInTheDocument();
    });
  });

  it('should allow manual connection switching', async () => {
    const user = userEvent.setup();
    
    const mockSocket = {
      connected: true,
      on: vi.fn(),
      off: vi.fn(),
      emit: vi.fn()
    };
    
    const mockClient = {
      connect: vi.fn(() => mockSocket),
      subscribe: vi.fn(),
      disconnect: vi.fn(),
      isConnected: vi.fn(() => true),
      socket: mockSocket
    };
    
    vi.doMock('@/lib/socket', () => ({
      getSocketClient: () => mockClient
    }));
    
    render(
      <SocketProvider autoConnect={false}>
        <RAGPipelineStatus />
      </SocketProvider>
    );
    
    // Click Google Drive button
    await user.click(screen.getByRole('button', { name: /Google Drive/ }));
    
    await waitFor(() => {
      expect(mockClient.connect).toHaveBeenCalledWith('google_drive');
      expect(mockClient.subscribe).toHaveBeenCalledWith('google_drive');
    });
    
    // Click Local Files button
    await user.click(screen.getByRole('button', { name: /Local Files/ }));
    
    await waitFor(() => {
      expect(mockClient.connect).toHaveBeenCalledWith('local_files');
    });
  });
});
```

## 4. Performance Tests

### Test Connection and Event Performance

Create `__tests__/performance/websocket-performance.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { performance } from 'perf_hooks';
import { getSocketClient } from '@/lib/socket';

describe('WebSocket Performance', () => {
  let mockSocketClient: any;
  let mockSocket: any;
  
  beforeEach(() => {
    mockSocket = {
      connected: false,
      on: vi.fn(),
      off: vi.fn(),
      emit: vi.fn(),
      connect: vi.fn(() => {
        mockSocket.connected = true;
        // Simulate connection event with delay
        setTimeout(() => {
          const connectHandler = mockSocket.on.mock.calls.find(call => call[0] === 'connect')[1];
          if (connectHandler) connectHandler();
        }, 50); // 50ms connection time
      })
    };
    
    mockSocketClient = {
      connect: vi.fn(() => mockSocket),
      disconnect: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      socket: mockSocket
    };
    
    vi.mocked(getSocketClient).mockReturnValue(mockSocketClient);
  });

  it('should connect within reasonable time', async () => {
    const startTime = performance.now();
    
    const client = getSocketClient();
    const socket = client.connect('google_drive');
    
    // Wait for connection
    await new Promise(resolve => {
      socket.on('connect', resolve);
      socket.connect();
    });
    
    const connectionTime = performance.now() - startTime;
    
    expect(connectionTime).toBeLessThan(1000); // Should connect in under 1 second
    expect(socket.connected).toBe(true);
  });
  
  it('should handle high-frequency events efficiently', async () => {
    const client = getSocketClient();
    const socket = client.connect('google_drive');
    
    const eventCounts: Record<string, number> = {};
    const startTime = performance.now();
    
    // Set up event listeners that track counts
    const events = ['file:processing', 'file:progress', 'file:completed', 'status:update'];
    
    events.forEach(event => {
      eventCounts[event] = 0;
      socket.on(event, () => {
        eventCounts[event]++;
      });
    });
    
    // Simulate rapid event emission (1000 events)
    const numEvents = 1000;
    const eventsPerType = numEvents / events.length;
    
    for (let i = 0; i < eventsPerType; i++) {
      events.forEach(event => {
        const handler = socket.on.mock.calls.find(call => call[0] === event)[1];
        if (handler) {
          handler({ test: true, index: i });
        }
      });
    }
    
    const processingTime = performance.now() - startTime;
    
    // Should process 1000 events in under 100ms
    expect(processingTime).toBeLessThan(100);
    
    // All events should be processed
    events.forEach(event => {
      expect(eventCounts[event]).toBe(eventsPerType);
    });
  });
  
  it('should handle memory efficiently during long sessions', () => {
    const client = getSocketClient();
    const socket = client.connect('google_drive');
    
    const initialMemory = process.memoryUsage();
    
    // Simulate long session with many event registrations/removals
    for (let i = 0; i < 1000; i++) {
      const handler = vi.fn();
      socket.on('test:event', handler);
      socket.off('test:event', handler);
    }
    
    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }
    
    const finalMemory = process.memoryUsage();
    const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
    
    // Memory increase should be minimal (less than 10MB)
    expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
  });
});
```

## 5. E2E Tests with Playwright

### Test End-to-End WebSocket Functionality

Create `e2e/websocket.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('WebSocket Integration E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to RAG pipeline page
    await page.goto('/rag-pipelines');
  });

  test('should establish WebSocket connection and show real-time updates', async ({ page }) => {
    // Wait for page to load
    await expect(page.locator('h2')).toContainText('RAG Pipeline Status');
    
    // Check for connection status indicator
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    
    // Should eventually show connected status
    await expect(connectionStatus).toContainText('Connected', { timeout: 10000 });
    
    // Check that pipeline controls are enabled
    const googleDriveButton = page.locator('button', { hasText: 'Google Drive' });
    const localFilesButton = page.locator('button', { hasText: 'Local Files' });
    
    await expect(googleDriveButton).toBeEnabled();
    await expect(localFilesButton).toBeEnabled();
  });

  test('should switch between pipeline types', async ({ page }) => {
    // Wait for connection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected', { timeout: 10000 });
    
    // Click Google Drive button
    await page.click('button:has-text("Google Drive")');
    
    // Should show Google Drive as active (disabled button indicates active connection)
    await expect(page.locator('button:has-text("Google Drive")')).toBeDisabled();
    
    // Click Local Files button
    await page.click('button:has-text("Local Files")');
    
    // Should show Local Files as active
    await expect(page.locator('button:has-text("Local Files")')).toBeDisabled();
    await expect(page.locator('button:has-text("Google Drive")')).toBeEnabled();
  });

  test('should display file processing updates in real-time', async ({ page }) => {
    // Wait for connection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected', { timeout: 10000 });
    
    // Connect to Google Drive pipeline
    await page.click('button:has-text("Google Drive")');
    
    // Initially should show 0 processing files
    await expect(page.locator('text=Processing (0)')).toBeVisible();
    
    // Simulate file processing by triggering a test file upload
    // This would typically be done through a test endpoint or mock
    await page.evaluate(() => {
      // Simulate Socket.IO event emission
      window.dispatchEvent(new CustomEvent('test:file-processing', {
        detail: {
          pipeline_id: 'test-pipeline',
          file: {
            name: 'test-document.pdf',
            id: 'test123',
            started_at: new Date().toISOString()
          },
          processing_stage: 'extraction'
        }
      }));
    });
    
    // Should show 1 processing file
    await expect(page.locator('text=Processing (1)')).toBeVisible();
    await expect(page.locator('text=test-document.pdf')).toBeVisible();
    
    // Simulate completion
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('test:file-completed', {
        detail: {
          pipeline_id: 'test-pipeline',
          file: {
            name: 'test-document.pdf',
            id: 'test123',
            completed_at: new Date().toISOString()
          },
          results: {
            chunks_created: 3,
            embeddings_generated: 3,
            processing_duration: 1500
          },
          success: true
        }
      }));
    });
    
    // Should show 0 processing, 1 completed
    await expect(page.locator('text=Processing (0)')).toBeVisible();
    await expect(page.locator('text=Completed (1)')).toBeVisible();
    await expect(page.locator('text=3 chunks, 3 embeddings')).toBeVisible();
  });

  test('should handle connection failures gracefully', async ({ page }) => {
    // Block WebSocket connections to simulate failure
    await page.route('**/socket.io/**', route => route.abort());
    
    // Reload page to trigger connection attempt
    await page.reload();
    
    // Should show connection error
    await expect(page.locator('text=Connection Error')).toBeVisible();
    await expect(page.locator('button:has-text("Retry")')).toBeVisible();
    
    // Unblock connections
    await page.unroute('**/socket.io/**');
    
    // Click retry
    await page.click('button:has-text("Retry Google Drive")');
    
    // Should eventually connect
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected', { timeout: 10000 });
  });

  test('should show connection health metrics', async ({ page }) => {
    // Wait for connection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected', { timeout: 10000 });
    
    // Should show latency information
    await expect(page.locator('text=/\\d+ms/')).toBeVisible();
    
    // Should show transport type
    await expect(page.locator('text=/WEBSOCKET|POLLING/i')).toBeVisible();
  });
});
```

## 6. Test Configuration

### Vitest Configuration

Create `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./test-setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/**',
        '**/*.d.ts',
        '**/*.config.{js,ts}',
        '**/coverage/**'
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './')
    }
  }
});
```

### Test Setup File

Create `test-setup.ts`:

```typescript
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Clean up after each test
afterEach(() => {
  cleanup();
});

// Mock WebSocket globally
Object.defineProperty(window, 'WebSocket', {
  writable: true,
  value: vi.fn(() => ({
    close: vi.fn(),
    send: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: 1, // OPEN
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3
  }))
});

// Mock performance.now for consistent timing in tests
Object.defineProperty(global, 'performance', {
  writable: true,
  value: {
    now: vi.fn(() => Date.now())
  }
});
```

### Package.json Test Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:all": "npm run test && npm run test:e2e"
  }
}
```

## 7. Running Tests

```bash
# Unit and integration tests
npm run test

# With coverage
npm run test:coverage

# E2E tests  
npm run test:e2e

# All tests
npm run test:all

# Watch mode for development
npm run test -- --watch

# UI mode for debugging
npm run test:ui
```

This comprehensive testing strategy ensures Socket.IO integration works correctly across all scenarios, from basic connection handling to complex real-time update scenarios.