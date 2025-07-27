import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import MagicMock, patch

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
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key',
        'OPENAI_API_KEY': 'test-openai-key'
    }):
        yield

@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)