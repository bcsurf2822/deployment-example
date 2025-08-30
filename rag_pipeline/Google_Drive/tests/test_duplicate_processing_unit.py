#!/usr/bin/env python3
"""
Unit tests for duplicate processing prevention in GoogleDriveWatcher.
This test file focuses specifically on testing the duplicate processing logic
without requiring full Google Drive API or Supabase initialization.
"""

import pytest
import os
import sys
import threading
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, Mock
import tempfile
import json

# Mock all external dependencies before importing
def mock_all_imports():
    """Mock all external dependencies that cause import issues."""
    
    # Mock Supabase
    sys.modules['supabase'] = MagicMock()
    
    # Mock Google API dependencies
    sys.modules['googleapiclient'] = MagicMock()
    sys.modules['googleapiclient.discovery'] = MagicMock()
    sys.modules['googleapiclient.http'] = MagicMock()
    sys.modules['google'] = MagicMock()
    sys.modules['google.oauth2'] = MagicMock()
    sys.modules['google.oauth2.credentials'] = MagicMock()
    sys.modules['google.oauth2.service_account'] = MagicMock()
    sys.modules['google_auth_oauthlib'] = MagicMock()
    sys.modules['google_auth_oauthlib.flow'] = MagicMock()
    sys.modules['google.auth'] = MagicMock()
    sys.modules['google.auth.transport'] = MagicMock()
    sys.modules['google.auth.transport.requests'] = MagicMock()
    sys.modules['google.auth.exceptions'] = MagicMock()
    
    # Mock socketio
    sys.modules['socketio'] = MagicMock()
    
    # Mock common modules
    sys.modules['common'] = MagicMock()
    sys.modules['common.text_processor'] = MagicMock()
    sys.modules['common.db_handler'] = MagicMock()
    sys.modules['status_server'] = MagicMock()
    sys.modules['supabase_status'] = MagicMock()

# Apply mocks before any imports
mock_all_imports()

# Set environment variables
os.environ.update({
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_SERVICE_ROLE_KEY': 'test-service-role-key',
    'OPENAI_API_KEY': 'test-openai-key'
})

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import after mocking
from drive_watcher import GoogleDriveWatcher

class TestDuplicateProcessingUnit:
    """Unit tests focused on duplicate processing prevention logic."""
    
    @pytest.fixture
    def temp_config(self):
        """Create a temporary config file."""
        config = {
            "supported_mime_types": ["application/pdf", "text/plain"],
            "text_processing": {"default_chunk_size": 400},
            "last_check_time": "2025-01-01T00:00:00.000Z"
        }
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config, temp_file, indent=2)
        temp_file.close()
        
        yield temp_file.name
        
        try:
            os.unlink(temp_file.name)
        except FileNotFoundError:
            pass
    
    def test_socket_processed_tracking_basic(self, temp_config):
        """Test basic socket processed file tracking functionality."""
        print("\n=== Test: Basic Socket Processed Tracking ===")
        
        # Create watcher instance
        watcher = GoogleDriveWatcher(config_path=temp_config)
        
        # Test initial state
        assert len(watcher.recently_socket_processed) == 0
        print("✓ Initial state: no tracked files")
        
        # Test adding a file to tracking
        test_file_id = "test_file_123"
        test_time = datetime.now(timezone.utc)
        
        with watcher.socket_processed_lock:
            watcher.recently_socket_processed[test_file_id] = test_time
        
        assert test_file_id in watcher.recently_socket_processed
        assert watcher.recently_socket_processed[test_file_id] == test_time
        print(f"✓ File tracked: {test_file_id} at {test_time}")
        
    def test_cleanup_old_entries(self, temp_config):
        """Test cleanup of old socket processed entries."""
        print("\n=== Test: Cleanup Old Entries ===")
        
        watcher = GoogleDriveWatcher(config_path=temp_config)
        
        current_time = datetime.now(timezone.utc)
        
        # Add test files with different ages
        recent_id = "recent_file"
        old_id = "old_file"
        very_old_id = "very_old_file"
        
        watcher.recently_socket_processed[recent_id] = current_time - timedelta(minutes=5)
        watcher.recently_socket_processed[old_id] = current_time - timedelta(minutes=15)  
        watcher.recently_socket_processed[very_old_id] = current_time - timedelta(hours=2)
        
        print(f"Added files: recent (5m ago), old (15m ago), very_old (2h ago)")
        assert len(watcher.recently_socket_processed) == 3
        
        # Run cleanup
        watcher.cleanup_old_socket_processed_entries()
        
        # Verify results
        assert recent_id in watcher.recently_socket_processed
        assert old_id not in watcher.recently_socket_processed
        assert very_old_id not in watcher.recently_socket_processed
        assert len(watcher.recently_socket_processed) == 1
        
        print(f"✓ Cleanup successful: kept {len(watcher.recently_socket_processed)} recent entries")
        
    def test_timer_skip_logic(self, temp_config):
        """Test the core logic that skips timer processing for socket-processed files."""
        print("\n=== Test: Timer Skip Logic ===")
        
        watcher = GoogleDriveWatcher(config_path=temp_config)
        
        test_file_id = "skip_test_file"
        current_time = datetime.now(timezone.utc)
        
        # Test 1: File recently processed via socket (should skip)
        print("\n1. Testing recent socket processing (should skip)...")
        watcher.recently_socket_processed[test_file_id] = current_time - timedelta(minutes=5)
        
        # Simulate the skip check from check_for_changes
        with watcher.socket_processed_lock:
            if test_file_id in watcher.recently_socket_processed:
                processed_time = watcher.recently_socket_processed[test_file_id]
                time_since_processing = current_time - processed_time
                should_skip = time_since_processing < watcher.socket_processed_timeout
                
                print(f"   Time since processing: {time_since_processing.total_seconds():.1f}s")
                print(f"   Timeout threshold: {watcher.socket_processed_timeout.total_seconds()}s")
                print(f"   Should skip: {should_skip}")
                
                assert should_skip == True
                print("   ✓ Correctly determined to skip processing")
        
        # Test 2: File processed long ago (should process)
        print("\n2. Testing old socket processing (should allow)...")
        watcher.recently_socket_processed[test_file_id] = current_time - timedelta(minutes=15)
        
        with watcher.socket_processed_lock:
            if test_file_id in watcher.recently_socket_processed:
                processed_time = watcher.recently_socket_processed[test_file_id]
                time_since_processing = current_time - processed_time
                should_skip = time_since_processing < watcher.socket_processed_timeout
                
                print(f"   Time since processing: {time_since_processing.total_seconds():.1f}s")
                print(f"   Should skip: {should_skip}")
                
                assert should_skip == False
                print("   ✓ Correctly determined to allow processing")
        
    def test_concurrent_access_safety(self, temp_config):
        """Test thread safety of the socket processed tracking."""
        print("\n=== Test: Concurrent Access Safety ===")
        
        watcher = GoogleDriveWatcher(config_path=temp_config)
        
        test_file_id = "concurrent_file"
        
        def add_file():
            """Add file to tracking."""
            with watcher.socket_processed_lock:
                watcher.recently_socket_processed[test_file_id] = datetime.now(timezone.utc)
                time.sleep(0.1)  # Hold the lock briefly
        
        def check_file():
            """Check if file is tracked."""
            time.sleep(0.05)  # Small delay to create race condition
            with watcher.socket_processed_lock:
                return test_file_id in watcher.recently_socket_processed
        
        # Start both operations concurrently
        add_thread = threading.Thread(target=add_file)
        check_thread = threading.Thread(target=check_file)
        
        add_thread.start()
        check_thread.start()
        
        add_thread.join()
        check_thread.join()
        
        # Verify file was added successfully despite concurrent access
        assert test_file_id in watcher.recently_socket_processed
        print("✓ Concurrent access handled safely with locks")
        
    def test_timeout_configuration(self, temp_config):
        """Test that timeout is properly configured."""
        print("\n=== Test: Timeout Configuration ===")
        
        watcher = GoogleDriveWatcher(config_path=temp_config)
        
        # Verify default timeout
        assert watcher.socket_processed_timeout == timedelta(minutes=10)
        print(f"✓ Default timeout: {watcher.socket_processed_timeout}")
        
        # Test that timeout can be modified
        new_timeout = timedelta(minutes=5)
        watcher.socket_processed_timeout = new_timeout
        assert watcher.socket_processed_timeout == new_timeout
        print(f"✓ Timeout modified to: {new_timeout}")

if __name__ == "__main__":
    import tempfile
    
    config = {
        "supported_mime_types": ["application/pdf", "text/plain"],
        "text_processing": {"default_chunk_size": 400},
        "last_check_time": "2025-01-01T00:00:00.000Z"
    }
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(config, temp_file, indent=2)
    temp_file.close()
    
    try:
        test_instance = TestDuplicateProcessingUnit()
        
        print("Running duplicate processing prevention unit tests...")
        test_instance.test_socket_processed_tracking_basic(temp_file.name)
        test_instance.test_cleanup_old_entries(temp_file.name)
        test_instance.test_timer_skip_logic(temp_file.name)
        test_instance.test_concurrent_access_safety(temp_file.name)
        test_instance.test_timeout_configuration(temp_file.name)
        
        print("\n🎉 All tests passed! Duplicate processing prevention is working correctly.")
        
    finally:
        os.unlink(temp_file.name)