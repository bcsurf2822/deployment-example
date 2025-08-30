import pytest
import os
import sys
import tempfile
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch('common.db_handler.supabase') as mock_client:
        # Mock table operations
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        
        # Mock delete operations
        mock_delete = MagicMock()
        mock_delete.execute.return_value = MagicMock(data=[])
        mock_table.delete.return_value = mock_delete
        
        # Mock insert operations
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock(data=[])
        mock_table.insert.return_value = mock_insert
        
        yield mock_client

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('common.text_processor.get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        
        # Mock embeddings
        mock_embedding = MagicMock()
        mock_embedding.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_embedding
        
        mock_get_client.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_google_drive_service():
    """Mock Google Drive API service for testing."""
    with patch('drive_watcher.build') as mock_build:
        mock_service = MagicMock()
        
        # Mock files().get() for metadata
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            'id': 'test_file_id',
            'name': 'test_file.pdf',
            'mimeType': 'application/pdf',
            'modifiedTime': '2025-08-30T17:29:46.068853Z',
            'createdTime': '2025-08-30T17:29:46.068853Z',
            'trashed': False,
            'webViewLink': 'https://drive.google.com/test'
        }
        mock_service.files().get.return_value = mock_get
        
        # Mock files().list() for change detection
        mock_list = MagicMock()
        mock_list.execute.return_value = {'files': []}
        mock_service.files().list.return_value = mock_list
        
        # Mock files().get_media() for download
        mock_get_media = MagicMock()
        mock_service.files().get_media.return_value = mock_get_media
        
        mock_build.return_value = mock_service
        yield mock_service

@pytest.fixture
def mock_socket_client():
    """Mock socket.io client for testing."""
    with patch('drive_watcher.socketio.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client.connected = True
        mock_client_class.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_SERVICE_ROLE_KEY': 'test-service-role-key',
        'OPENAI_API_KEY': 'test-openai-key',
        'GOOGLE_DRIVE_CREDENTIALS_JSON': '{"type": "service_account", "client_email": "test@test.iam.gserviceaccount.com"}',
        'RAG_WATCH_FOLDER_ID': 'test_folder_id'
    }):
        yield

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    config = {
        "supported_mime_types": [
            "application/pdf",
            "text/plain",
            "text/csv"
        ],
        "export_mime_types": {
            "application/vnd.google-apps.document": "text/plain"
        },
        "text_processing": {
            "default_chunk_size": 400,
            "default_chunk_overlap": 0
        },
        "last_check_time": "2025-01-01T00:00:00.000Z",
        "watch_folder_id": "test_folder_id"
    }
    
    json.dump(config, temp_file, indent=2)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass

@pytest.fixture
def mock_text_extraction():
    """Mock text extraction functions."""
    with patch('common.text_processor.extract_text_from_file') as mock_extract:
        mock_extract.return_value = "This is extracted test content from the file."
        yield mock_extract

@pytest.fixture
def mock_file_processing():
    """Mock RAG file processing."""
    with patch('common.db_handler.process_file_for_rag') as mock_process:
        mock_process.return_value = True
        yield mock_process