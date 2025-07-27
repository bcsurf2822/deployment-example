import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import json

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from file_watcher import LocalFilesWatcher

class TestLocalFilesWatcher:
    """Test suite for LocalFilesWatcher."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.json')
        
        # Create a test configuration
        self.test_config = {
            "supported_mime_types": [
                "text/plain",
                "application/pdf",
                "text/csv"
            ],
            "tabular_mime_types": [
                "text/csv"
            ],
            "text_processing": {
                "chunk_size": 1000,
                "default_chunk_overlap": 0
            },
            "last_check_time": "2025-01-01T00:00:00Z",
            "watch_directory": self.test_dir
        }
        
        # Write test config
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_init_with_config(self):
        """Test LocalFilesWatcher initialization with config file."""
        # Temporarily remove env var to test constructor parameter
        with patch.dict(os.environ, {}, clear=False):
            if 'RAG_WATCH_DIRECTORY' in os.environ:
                del os.environ['RAG_WATCH_DIRECTORY']
            
            watcher = LocalFilesWatcher(
                watch_directory=self.test_dir,
                config_path=self.config_path
            )
            
            assert watcher.watch_directory == self.test_dir
            assert watcher.config_path == self.config_path
            assert watcher.config == self.test_config
            assert not watcher.initialized
            assert watcher.known_files == {}
    
    def test_init_without_config(self):
        """Test LocalFilesWatcher initialization without config file."""
        # Remove config file
        os.remove(self.config_path)
        
        watcher = LocalFilesWatcher(watch_directory=self.test_dir)
        
        assert watcher.watch_directory == self.test_dir
        # Should use default config
        assert "supported_mime_types" in watcher.config
        assert watcher.config["supported_mime_types"] is not None
    
    def test_get_file_id(self):
        """Test file ID generation."""
        watcher = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        test_file = os.path.join(self.test_dir, "test.txt")
        file_id = watcher.get_file_id(test_file)
        
        # Should return a consistent hash
        assert isinstance(file_id, str)
        assert len(file_id) == 32  # MD5 hash length
        
        # Should be consistent
        file_id2 = watcher.get_file_id(test_file)
        assert file_id == file_id2
    
    def test_get_file_mime_type(self):
        """Test MIME type detection."""
        watcher = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        assert watcher.get_file_mime_type("test.txt") == "text/plain"
        assert watcher.get_file_mime_type("test.pdf") == "application/pdf"
        assert watcher.get_file_mime_type("test.csv") == "text/csv"
        assert watcher.get_file_mime_type("test.unknown") == "text/plain"  # default
    
    def test_is_supported_file(self):
        """Test file support checking."""
        watcher = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        assert watcher.is_supported_file("test.txt") == True
        assert watcher.is_supported_file("test.pdf") == True
        assert watcher.is_supported_file("test.csv") == True
        assert watcher.is_supported_file("test.exe") == False  # not in supported types
    
    def test_scan_directory_empty(self):
        """Test scanning an empty directory."""
        watcher = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        files = watcher.scan_directory()
        assert files == []
    
    def test_scan_directory_with_files(self):
        """Test scanning directory with files."""
        # Temporarily remove env var to test constructor parameter
        with patch.dict(os.environ, {}, clear=False):
            if 'RAG_WATCH_DIRECTORY' in os.environ:
                del os.environ['RAG_WATCH_DIRECTORY']
            
            watcher = LocalFilesWatcher(
                watch_directory=self.test_dir,
                config_path=self.config_path
            )
        
            # Create test files
            test_file1 = os.path.join(self.test_dir, "test1.txt")
            test_file2 = os.path.join(self.test_dir, "test2.pdf")
            test_file3 = os.path.join(self.test_dir, "test3.exe")  # unsupported
            
            with open(test_file1, 'w') as f:
                f.write("Test content 1")
            with open(test_file2, 'w') as f:
                f.write("Test content 2")
            with open(test_file3, 'w') as f:
                f.write("Test content 3")
            
            files = watcher.scan_directory()
            
            # Should find 2 supported files
            assert len(files) == 2
            
            # Check file properties
            file_names = [f['name'] for f in files]
            assert 'test1.txt' in file_names
            assert 'test2.pdf' in file_names
            assert 'test3.exe' not in file_names
            
            # Check required properties exist
            for file in files:
                assert 'id' in file
                assert 'name' in file
                assert 'path' in file
                assert 'mimeType' in file
                assert 'modifiedTime' in file
                assert 'size' in file
    
    def test_save_and_load_config(self):
        """Test configuration saving and loading."""
        watcher = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        # Update last check time
        new_time = datetime.now(timezone.utc)
        watcher.last_check_time = new_time
        
        # Save config
        watcher.save_config()
        
        # Create new watcher and verify it loaded the updated time
        watcher2 = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        # Times should be close (within a few seconds)
        time_diff = abs((watcher2.last_check_time - new_time).total_seconds())
        assert time_diff < 2  # Allow 2 seconds difference for processing time
    
    @patch('file_watcher.process_file_for_rag')
    def test_process_file_success(self, mock_process_file):
        """Test successful file processing."""
        watcher = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        # Create test file
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        file_info = {
            'id': watcher.get_file_id(test_file),
            'name': 'test.txt',
            'path': test_file,
            'mimeType': 'text/plain',
            'size': 12,
            'modifiedTime': datetime.now(timezone.utc).isoformat()
        }
        
        # Mock successful processing
        mock_process_file.return_value = True
        
        result = watcher.process_file(file_info)
        
        assert result == True
        assert file_info['id'] in watcher.known_files
        mock_process_file.assert_called_once()
    
    @patch('file_watcher.process_file_for_rag')
    def test_process_file_failure(self, mock_process_file):
        """Test file processing failure."""
        watcher = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        # Create test file
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        file_info = {
            'id': watcher.get_file_id(test_file),
            'name': 'test.txt',
            'path': test_file,
            'mimeType': 'text/plain',
            'size': 12,
            'modifiedTime': datetime.now(timezone.utc).isoformat()
        }
        
        # Mock processing failure
        mock_process_file.side_effect = Exception("Processing failed")
        
        result = watcher.process_file(file_info)
        
        assert result == False
        mock_process_file.assert_called_once()
    
    @patch('file_watcher.process_file_for_rag')
    @patch('file_watcher.delete_document_by_file_id')
    def test_check_for_changes_no_changes(self, mock_delete, mock_process):
        """Test check_for_changes with no changes."""
        watcher = LocalFilesWatcher(
            watch_directory=self.test_dir,
            config_path=self.config_path
        )
        
        stats = watcher.check_for_changes()
        
        assert stats['files_processed'] == 0
        assert stats['files_deleted'] == 0
        assert stats['errors'] == 0
        assert stats['duration'] >= 0
        
        mock_process.assert_not_called()
        mock_delete.assert_not_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])