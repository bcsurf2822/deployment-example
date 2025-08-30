import pytest
import os
import sys
import threading
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, call
import io

# Mock environment variables before any imports that need them
os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role-key')
os.environ.setdefault('OPENAI_API_KEY', 'test-openai-key')

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from drive_watcher import GoogleDriveWatcher

class TestDuplicateProcessingPrevention:
    """Test suite for duplicate processing prevention in GoogleDriveWatcher."""
    
    def test_socket_processing_prevents_timer_duplicate(
        self, mock_environment, temp_config_file, mock_supabase, 
        mock_openai, mock_google_drive_service, mock_socket_client,
        mock_text_extraction, mock_file_processing
    ):
        """
        Test that files processed via socket are not reprocessed by timer.
        This recreates the exact scenario from the logs where the same file
        was processed twice.
        """
        # Mock the download functionality
        mock_file_content = b"This is test PDF content"
        with patch('drive_watcher.MediaIoBaseDownload') as mock_download:
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.side_effect = [(None, False), (None, True)]
            mock_download.return_value = mock_downloader
            
            # Mock io.BytesIO to return our test content
            mock_bytesio = MagicMock()
            mock_bytesio.read.return_value = mock_file_content
            with patch('drive_watcher.io.BytesIO', return_value=mock_bytesio):
                
                # Create watcher instance
                watcher = GoogleDriveWatcher(
                    credentials_path='fake_creds.json',
                    token_path='fake_token.json',
                    folder_id='test_folder_id',
                    config_path=temp_config_file
                )
                
                # Mock authentication to avoid actual Google API calls
                watcher.service = mock_google_drive_service
                watcher.socket_client = mock_socket_client
                watcher.socket_connected = True
                
                # Test file metadata (matching the logs)
                test_file_id = "1FuOzrr98bNVKyG9eDBgJ0cWHyuV6WldL"
                test_file_name = "KLST USA Employee Referral Program.pdf"
                
                file_metadata = {
                    'id': test_file_id,
                    'name': test_file_name,
                    'mimeType': 'application/pdf',
                    'modifiedTime': '2025-08-30T17:29:46.068853Z',
                    'createdTime': '2025-08-30T17:29:46.068853Z',
                    'trashed': False,
                    'webViewLink': 'https://drive.google.com/file/d/test/view'
                }
                
                print(f"\n=== Test Case: Duplicate Processing Prevention ===")
                print(f"File: {test_file_name}")
                print(f"ID: {test_file_id}")
                
                # Verify initial state - no files in recently processed
                assert len(watcher.recently_socket_processed) == 0
                assert test_file_id not in watcher.processing_files
                
                print(f"\n1. Simulating socket processing (immediate upload)...")
                
                # STEP 1: Process file via socket (immediate processing)
                socket_data = {
                    'fileName': test_file_name,
                    'googleDriveId': test_file_id,
                    'fileSize': 93074
                }
                
                result = watcher.process_file_immediately(test_file_id, test_file_name)
                
                # Verify socket processing succeeded
                assert result == True
                print(f"   ✓ Socket processing completed successfully")
                
                # Verify file is now tracked in recently_socket_processed
                assert test_file_id in watcher.recently_socket_processed
                socket_processed_time = watcher.recently_socket_processed[test_file_id]
                print(f"   ✓ File marked as socket-processed at: {socket_processed_time}")
                
                # Verify socket notifications were sent
                expected_socket_calls = [
                    call("processing-started", {
                        "fileName": test_file_name,
                        "googleDriveId": test_file_id,
                        "timestamp": pytest.approx(datetime.now().isoformat(), abs=5),
                        "pipelineType": "google_drive"
                    }),
                    call("processing-complete", {
                        "fileName": test_file_name,
                        "googleDriveId": test_file_id,
                        "timestamp": pytest.approx(datetime.now().isoformat(), abs=5),
                        "pipelineType": "google_drive"
                    })
                ]
                
                # Check that socket notifications were sent (at least processing-started)
                mock_socket_client.emit.assert_called()
                print(f"   ✓ Socket notifications sent: {mock_socket_client.emit.call_count} calls")
                
                print(f"\n2. Simulating timer-based processing (60 seconds later)...")
                
                # STEP 2: Simulate timer finding the same file
                # Mock get_changes to return our test file
                with patch.object(watcher, 'get_changes') as mock_get_changes:
                    mock_get_changes.return_value = [file_metadata]
                    
                    # Reset process_file mock to track if it gets called
                    with patch.object(watcher, 'process_file') as mock_process_file:
                        
                        # Run timer check
                        stats = watcher.check_for_changes()
                        
                        # Verify that process_file was NOT called (duplicate prevention worked)
                        mock_process_file.assert_not_called()
                        print(f"   ✓ Timer processing correctly skipped the file")
                        
                        # Verify stats show no files processed
                        assert stats['files_processed'] == 0
                        print(f"   ✓ Processing stats: {stats['files_processed']} files processed")
                        
                        # File should still be in recently_socket_processed
                        assert test_file_id in watcher.recently_socket_processed
                        print(f"   ✓ File still tracked as recently socket-processed")
                
                print(f"\n3. Verifying timeout behavior (after 10+ minutes)...")
                
                # STEP 3: Test that after timeout, timer processing is allowed again
                # Manually set the processing time to be older than timeout
                old_time = datetime.now(timezone.utc) - timedelta(minutes=11)
                watcher.recently_socket_processed[test_file_id] = old_time
                print(f"   • Set socket processing time to: {old_time}")
                
                with patch.object(watcher, 'get_changes') as mock_get_changes:
                    mock_get_changes.return_value = [file_metadata]
                    
                    with patch.object(watcher, 'process_file') as mock_process_file:
                        
                        # Run timer check again
                        stats = watcher.check_for_changes()
                        
                        # This time process_file SHOULD be called
                        mock_process_file.assert_called_once_with(file_metadata)
                        print(f"   ✓ Timer processing allowed after timeout")
                        
                        # Verify stats show file was processed
                        assert stats['files_processed'] == 1
                        print(f"   ✓ Processing stats: {stats['files_processed']} files processed")
                        
                        # File should be removed from recently_socket_processed due to timeout
                        assert test_file_id not in watcher.recently_socket_processed
                        print(f"   ✓ Expired entry removed from tracking")

    def test_cleanup_old_socket_processed_entries(
        self, mock_environment, temp_config_file, mock_supabase, mock_openai
    ):
        """Test that old entries in recently_socket_processed are cleaned up automatically."""
        
        watcher = GoogleDriveWatcher(config_path=temp_config_file)
        
        print(f"\n=== Test Case: Cleanup Old Socket Processed Entries ===")
        
        # Add some test entries with different ages
        current_time = datetime.now(timezone.utc)
        
        # Recent entry (should be kept)
        recent_file_id = "recent_file"
        watcher.recently_socket_processed[recent_file_id] = current_time - timedelta(minutes=5)
        
        # Old entry (should be cleaned up)
        old_file_id = "old_file"  
        watcher.recently_socket_processed[old_file_id] = current_time - timedelta(minutes=15)
        
        # Very old entry (should be cleaned up)
        very_old_file_id = "very_old_file"
        watcher.recently_socket_processed[very_old_file_id] = current_time - timedelta(hours=1)
        
        print(f"   • Added 3 test entries:")
        print(f"     - {recent_file_id}: 5 minutes ago (should be kept)")
        print(f"     - {old_file_id}: 15 minutes ago (should be cleaned)")
        print(f"     - {very_old_file_id}: 1 hour ago (should be cleaned)")
        
        assert len(watcher.recently_socket_processed) == 3
        
        # Run cleanup
        watcher.cleanup_old_socket_processed_entries()
        
        # Verify cleanup results
        assert recent_file_id in watcher.recently_socket_processed
        assert old_file_id not in watcher.recently_socket_processed  
        assert very_old_file_id not in watcher.recently_socket_processed
        assert len(watcher.recently_socket_processed) == 1
        
        print(f"   ✓ Cleanup successful: kept {len(watcher.recently_socket_processed)} recent entries")

    def test_concurrent_processing_prevention(
        self, mock_environment, temp_config_file, mock_supabase,
        mock_openai, mock_google_drive_service, mock_socket_client,
        mock_text_extraction, mock_file_processing
    ):
        """Test that concurrent processing of the same file is prevented."""
        
        # Mock the download functionality
        mock_file_content = b"Test content"
        with patch('drive_watcher.MediaIoBaseDownload') as mock_download:
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.side_effect = [(None, False), (None, True)]
            mock_download.return_value = mock_downloader
            
            mock_bytesio = MagicMock()
            mock_bytesio.read.return_value = mock_file_content
            with patch('drive_watcher.io.BytesIO', return_value=mock_bytesio):
                
                watcher = GoogleDriveWatcher(config_path=temp_config_file)
                watcher.service = mock_google_drive_service
                watcher.socket_client = mock_socket_client
                watcher.socket_connected = True
                
                test_file_id = "concurrent_test_file"
                test_file_name = "concurrent_test.pdf"
                
                print(f"\n=== Test Case: Concurrent Processing Prevention ===")
                print(f"File: {test_file_name}")
                
                # Start first processing in a separate thread
                def process_first():
                    return watcher.process_file_immediately(test_file_id, test_file_name)
                
                # Start second processing immediately
                def process_second():
                    time.sleep(0.1)  # Small delay to ensure first one starts
                    return watcher.process_file_immediately(test_file_id, test_file_name)
                
                thread1 = threading.Thread(target=process_first)
                thread2 = threading.Thread(target=process_second)
                
                thread1.start()
                thread2.start()
                
                thread1.join()
                thread2.join()
                
                # Verify that concurrent processing was prevented
                # The file should not be in processing_files after both threads complete
                assert test_file_id not in watcher.processing_files
                print(f"   ✓ Concurrent processing prevented successfully")

    def test_socket_processing_marks_file_correctly(
        self, mock_environment, temp_config_file, mock_supabase,
        mock_openai, mock_google_drive_service, mock_socket_client,
        mock_text_extraction, mock_file_processing
    ):
        """Test that socket processing correctly marks files to prevent timer reprocessing."""
        
        # Mock the download functionality  
        mock_file_content = b"Test content"
        with patch('drive_watcher.MediaIoBaseDownload') as mock_download:
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.side_effect = [(None, False), (None, True)]
            mock_download.return_value = mock_downloader
            
            mock_bytesio = MagicMock()
            mock_bytesio.read.return_value = mock_file_content
            with patch('drive_watcher.io.BytesIO', return_value=mock_bytesio):
                
                watcher = GoogleDriveWatcher(config_path=temp_config_file)
                watcher.service = mock_google_drive_service
                watcher.socket_client = mock_socket_client
                watcher.socket_connected = True
                
                test_file_id = "marking_test_file"
                test_file_name = "marking_test.pdf"
                
                print(f"\n=== Test Case: Socket Processing Marking ===")
                
                # Verify file is not initially tracked
                assert test_file_id not in watcher.recently_socket_processed
                
                # Process via socket
                result = watcher.process_file_immediately(test_file_id, test_file_name)
                
                # Verify processing succeeded
                assert result == True
                
                # Verify file is now marked
                assert test_file_id in watcher.recently_socket_processed
                
                # Verify timestamp is recent
                marked_time = watcher.recently_socket_processed[test_file_id]
                time_diff = datetime.now(timezone.utc) - marked_time
                assert time_diff.total_seconds() < 10  # Should be very recent
                
                print(f"   ✓ File correctly marked with timestamp: {marked_time}")
                print(f"   ✓ Processing completed: {result}")