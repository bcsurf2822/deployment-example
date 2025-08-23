# Testing Strategy for Socket.IO RAG Pipeline

## Testing Approach Overview

The testing strategy ensures Socket.IO integration works correctly while maintaining compatibility with existing functionality.

## Unit Tests

### 1. Socket.IO Event Emission Tests

**Test File**: `tests/test_socketio_events.py`

```python
import pytest
import asyncio
import socketio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from status_server import SocketIOEventHandler, pipeline_status
from status_server import sio

class TestSocketIOEventHandler:
    @pytest.fixture
    def mock_sio_server(self):
        """Mock Socket.IO server for testing."""
        server = Mock(spec=socketio.AsyncServer)
        server.emit = AsyncMock()
        return server
    
    @pytest.fixture
    def event_handler(self, mock_sio_server):
        """Create event handler with mocked server."""
        return SocketIOEventHandler(mock_sio_server, "test-pipeline", "test_service")
    
    @pytest.mark.asyncio
    async def test_emit_file_processing(self, event_handler, mock_sio_server):
        """Test file processing event emission."""
        filename = "test.pdf"
        file_id = "test123"
        file_info = {"size": 1024, "mime_type": "application/pdf"}
        
        await event_handler.emit_file_processing(filename, file_id, file_info)
        
        # Verify emit was called with correct parameters
        mock_sio_server.emit.assert_called_once()
        call_args = mock_sio_server.emit.call_args
        
        assert call_args[0][0] == 'file:processing'  # Event name
        assert call_args[0][1]['file']['name'] == filename
        assert call_args[0][1]['file']['id'] == file_id
        assert call_args[1]['namespace'] == '/test_service'
    
    @pytest.mark.asyncio
    async def test_emit_file_completed(self, event_handler, mock_sio_server):
        """Test file completion event emission."""
        filename = "test.pdf"
        file_id = "test123" 
        stats = {"chunks": 5, "embeddings": 5, "duration": 10.5}
        
        await event_handler.emit_file_completed(filename, file_id, stats)
        
        mock_sio_server.emit.assert_called_once()
        call_args = mock_sio_server.emit.call_args
        
        assert call_args[0][0] == 'file:completed'
        assert call_args[0][1]['results']['chunks_created'] == 5
        assert call_args[0][1]['success'] is True
    
    @pytest.mark.asyncio
    async def test_emit_with_error_handling(self, event_handler, mock_sio_server):
        """Test error handling during event emission."""
        # Setup mock to raise exception
        mock_sio_server.emit.side_effect = Exception("Connection failed")
        
        filename = "test.pdf"
        file_id = "test123"
        
        # Should not raise exception, but handle gracefully
        result = await event_handler.emit_file_processing(filename, file_id, {})
        
        # Verify error was handled
        assert event_handler.failed_emit_count > 0
        mock_sio_server.emit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, event_handler, mock_sio_server):
        """Test that too many failures disable Socket.IO events."""
        # Setup mock to always fail
        mock_sio_server.emit.side_effect = Exception("Always fails")
        
        # Exceed max failures
        for i in range(12):  # More than max_failed_emits (10)
            await event_handler.emit_file_processing(f"test{i}.pdf", f"id{i}", {})
        
        # Verify Socket.IO emission is disabled
        assert event_handler.failed_emit_count > 10
```

### 2. PipelineStatus Integration Tests

**Test File**: `tests/test_pipeline_status_socketio.py`

```python
import pytest
import threading
import time
from unittest.mock import Mock, AsyncMock, patch

from status_server import PipelineStatus

class TestPipelineStatusSocketIO:
    @pytest.fixture
    def mock_event_handler(self):
        """Mock event handler for testing."""
        handler = Mock()
        handler.emit_file_processing = AsyncMock()
        handler.emit_file_completed = AsyncMock() 
        handler.emit_file_failed = AsyncMock()
        handler.emit_status_update = AsyncMock()
        return handler
    
    @pytest.fixture
    def pipeline_status(self, mock_event_handler):
        """Create PipelineStatus with mocked Socket.IO."""
        status = PipelineStatus()
        status.event_handler = mock_event_handler
        return status
    
    def test_add_processing_file_emits_event(self, pipeline_status, mock_event_handler):
        """Test that adding a processing file emits Socket.IO event."""
        filename = "test.pdf"
        file_id = "test123"
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_async:
            pipeline_status.add_processing_file(filename, file_id)
        
        # Verify Socket.IO event was scheduled
        mock_async.assert_called_once()
        
        # Verify file was added to processing list
        assert len(pipeline_status.data["files_processing"]) == 1
        assert pipeline_status.data["files_processing"][0]["name"] == filename
    
    def test_complete_file_success_emits_event(self, pipeline_status, mock_event_handler):
        """Test successful file completion emits correct event."""
        filename = "test.pdf"
        file_id = "test123"
        
        # Add file to processing first
        pipeline_status.add_processing_file(filename, file_id)
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_async:
            pipeline_status.complete_file(filename, success=True, stats={"chunks": 5})
        
        # Verify file moved to completed list
        assert len(pipeline_status.data["files_processing"]) == 0
        assert len(pipeline_status.data["files_completed"]) == 1
        assert pipeline_status.data["total_processed"] == 1
        
        # Verify Socket.IO event was scheduled
        mock_async.assert_called()
    
    def test_complete_file_failure_emits_event(self, pipeline_status, mock_event_handler):
        """Test failed file completion emits correct event."""
        filename = "test.pdf"
        file_id = "test123"
        
        pipeline_status.add_processing_file(filename, file_id)
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_async:
            pipeline_status.complete_file(filename, success=False, stats={"error": "Parse failed"})
        
        # Verify file moved to failed list
        assert len(pipeline_status.data["files_processing"]) == 0
        assert len(pipeline_status.data["files_failed"]) == 1
        assert pipeline_status.data["total_failed"] == 1
    
    def test_thread_safety_with_socketio(self, pipeline_status):
        """Test that Socket.IO events work with threading."""
        def add_files():
            for i in range(10):
                pipeline_status.add_processing_file(f"file{i}.pdf", f"id{i}")
                time.sleep(0.01)
        
        def complete_files():
            time.sleep(0.05)  # Let some files be added first
            for i in range(5):
                pipeline_status.complete_file(f"file{i}.pdf", success=True)
                time.sleep(0.01)
        
        # Run in parallel threads
        thread1 = threading.Thread(target=add_files)
        thread2 = threading.Thread(target=complete_files)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Verify state is consistent
        total_files = (len(pipeline_status.data["files_processing"]) + 
                      len(pipeline_status.data["files_completed"]))
        assert total_files == 10  # All files accounted for
```

## Integration Tests

### 3. End-to-End Socket.IO Tests

**Test File**: `tests/test_socketio_integration.py`

```python
import pytest
import asyncio
import socketio
from unittest.mock import patch
import threading
import time
import json

from status_server import start_status_server, pipeline_status, sio

class TestSocketIOIntegration:
    @pytest.fixture(scope="function")
    def socketio_server(self):
        """Start a test Socket.IO server.""" 
        with patch.dict('os.environ', {
            'RAG_SERVICE': 'test_pipeline',
            'RAG_PIPELINE_ID': 'test-integration-123'
        }):
            server = start_status_server(port=8005)  # Use different port for tests
            yield server
            server.shutdown()
    
    @pytest.fixture
    async def socketio_client(self):
        """Create a test Socket.IO client."""
        client = socketio.AsyncClient()
        yield client
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_client_connection(self, socketio_server, socketio_client):
        """Test that clients can connect to Socket.IO server."""
        events_received = []
        
        @socketio_client.event
        def connect():
            events_received.append('connected')
        
        @socketio_client.event
        def pipeline_status(data):
            events_received.append(('status', data))
        
        # Connect to server
        await socketio_client.connect('http://localhost:8105')  # Socket.IO port
        await asyncio.sleep(0.1)  # Allow connection to establish
        
        assert 'connected' in events_received
        
        # Should receive initial status
        status_events = [e for e in events_received if e[0] == 'status']
        assert len(status_events) > 0
    
    @pytest.mark.asyncio
    async def test_file_processing_events(self, socketio_server, socketio_client):
        """Test that file processing triggers Socket.IO events."""
        events_received = []
        
        @socketio_client.event
        def file_processing(data):
            events_received.append(('file:processing', data))
        
        @socketio_client.event  
        def file_completed(data):
            events_received.append(('file:completed', data))
        
        # Connect client
        await socketio_client.connect('http://localhost:8105')
        await asyncio.sleep(0.1)
        
        # Simulate file processing
        pipeline_status.add_processing_file("test.pdf", "test123")
        await asyncio.sleep(0.1)
        
        pipeline_status.complete_file("test.pdf", success=True, stats={"chunks": 3})
        await asyncio.sleep(0.1)
        
        # Verify events were received
        processing_events = [e for e in events_received if e[0] == 'file:processing']
        completed_events = [e for e in events_received if e[0] == 'file:completed']
        
        assert len(processing_events) >= 1
        assert len(completed_events) >= 1
        
        # Verify event data
        processing_data = processing_events[0][1]
        assert processing_data['file']['name'] == 'test.pdf'
        assert processing_data['file']['id'] == 'test123'
        
        completed_data = completed_events[0][1]
        assert completed_data['success'] is True
        assert completed_data['results']['chunks_created'] == 3
    
    @pytest.mark.asyncio
    async def test_namespace_isolation(self, socketio_server):
        """Test that different pipeline types use separate namespaces."""
        google_drive_events = []
        local_files_events = []
        
        # Create clients for different namespaces
        gd_client = socketio.AsyncClient()
        lf_client = socketio.AsyncClient()
        
        @gd_client.event
        def file_processing(data):
            google_drive_events.append(data)
        
        @lf_client.event
        def file_processing(data):
            local_files_events.append(data)
        
        try:
            # Connect to different namespaces
            await gd_client.connect('http://localhost:8105', namespace='/google_drive')
            await lf_client.connect('http://localhost:8105', namespace='/local_files')
            await asyncio.sleep(0.1)
            
            # Emit events to specific namespace
            await sio.emit('file:processing', {
                'pipeline_type': 'google_drive',
                'file': {'name': 'gdrive_file.pdf'}
            }, namespace='/google_drive')
            
            await sio.emit('file:processing', {
                'pipeline_type': 'local_files', 
                'file': {'name': 'local_file.pdf'}
            }, namespace='/local_files')
            
            await asyncio.sleep(0.1)
            
            # Verify namespace isolation
            assert len(google_drive_events) == 1
            assert len(local_files_events) == 1
            assert google_drive_events[0]['file']['name'] == 'gdrive_file.pdf'
            assert local_files_events[0]['file']['name'] == 'local_file.pdf'
            
        finally:
            await gd_client.disconnect()
            await lf_client.disconnect()
```

## Load Testing

### 4. Socket.IO Performance Tests

**Test File**: `tests/test_socketio_performance.py`

```python
import pytest
import asyncio
import socketio
import time
from concurrent.futures import ThreadPoolExecutor

class TestSocketIOPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test handling multiple concurrent Socket.IO connections."""
        num_clients = 50
        clients = []
        connection_times = []
        
        async def create_client():
            start_time = time.time()
            client = socketio.AsyncClient()
            await client.connect('http://localhost:8105')
            connect_time = time.time() - start_time
            connection_times.append(connect_time)
            clients.append(client)
        
        try:
            # Create connections concurrently
            await asyncio.gather(*[create_client() for _ in range(num_clients)])
            
            # Verify all connections succeeded
            assert len(clients) == num_clients
            
            # Verify reasonable connection times (< 1 second each)
            avg_connection_time = sum(connection_times) / len(connection_times)
            assert avg_connection_time < 1.0
            
            print(f"Average connection time: {avg_connection_time:.3f}s")
            
        finally:
            # Cleanup
            for client in clients:
                await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_high_frequency_events(self):
        """Test handling high-frequency event emission."""
        client = socketio.AsyncClient()
        events_received = []
        
        @client.event
        def file_processing(data):
            events_received.append(time.time())
        
        try:
            await client.connect('http://localhost:8105')
            
            # Emit events rapidly
            start_time = time.time()
            num_events = 1000
            
            for i in range(num_events):
                await sio.emit('file:processing', {
                    'pipeline_id': 'test',
                    'file': {'name': f'file{i}.pdf', 'id': f'id{i}'}
                })
            
            # Wait for all events to be received
            await asyncio.sleep(2.0)
            end_time = time.time()
            
            # Verify event throughput
            total_time = end_time - start_time
            events_per_second = len(events_received) / total_time
            
            print(f"Events per second: {events_per_second:.1f}")
            print(f"Events sent: {num_events}, Events received: {len(events_received)}")
            
            # Should handle at least 100 events/second
            assert events_per_second > 100
            
            # Should receive most events (allow for some loss in high-frequency scenario)
            assert len(events_received) > num_events * 0.95
            
        finally:
            await client.disconnect()
```

## Test Execution

### Running Tests

```bash
# Install test dependencies
cd rag_pipeline
pip install pytest pytest-asyncio

# Run all Socket.IO tests
python -m pytest tests/test_socketio_*.py -v

# Run specific test categories
python -m pytest tests/test_socketio_events.py -v          # Unit tests
python -m pytest tests/test_socketio_integration.py -v    # Integration tests
python -m pytest tests/test_socketio_performance.py -v    # Load tests

# Run with coverage
python -m pytest tests/test_socketio_*.py --cov=status_server --cov-report=html

# Run in parallel for faster execution
python -m pytest tests/test_socketio_*.py -n auto
```

### Test Environment Setup

```bash
# Set test environment variables
export RAG_SERVICE=test_pipeline
export RAG_PIPELINE_ID=test-123
export SOCKET_IO_CORS_ORIGIN=*
export SOCKET_IO_LOG_LEVEL=DEBUG

# Use test database (optional)
export SUPABASE_URL=http://localhost:54321
export SUPABASE_SERVICE_ROLE_KEY=test-key
```

### Continuous Integration

```yaml
# .github/workflows/socketio-tests.yml
name: Socket.IO Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        cd rag_pipeline
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run Socket.IO tests
      run: |
        cd rag_pipeline
        python -m pytest tests/test_socketio_*.py -v --cov=status_server
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./rag_pipeline/coverage.xml
```

This comprehensive testing strategy ensures Socket.IO integration works reliably under various conditions while maintaining the existing functionality.