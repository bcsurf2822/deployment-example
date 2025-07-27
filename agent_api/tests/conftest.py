"""
Pytest configuration and shared fixtures for the Pydantic AI agent tests.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dependencies import AgentDependencies


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for testing."""
    deps = Mock(spec=AgentDependencies)
    deps.http_client = AsyncMock()
    deps.settings = Mock()
    deps.settings.brave_api_key = Mock(get_secret_value=lambda: "test-key")
    deps.settings.searxng_base_url = None
    deps.settings.debug_mode = False
    return deps


@pytest.fixture
def sample_brave_search_response():
    """Sample Brave search API response."""
    return {
        "web": {
            "results": [
                {
                    "title": "Test Result 1",
                    "url": "https://example.com/doc1",
                    "description": "A test document about Python programming"
                },
                {
                    "title": "Test Result 2", 
                    "url": "https://example.com/doc2",
                    "description": "Another test document about AI"
                }
            ]
        }
    }


@pytest.fixture
def sample_empty_search_response():
    """Sample empty Brave search API response."""
    return {
        "web": {
            "results": []
        }
    }


@pytest.fixture
def mock_http_error():
    """Mock HTTP error response."""
    from httpx import HTTPStatusError, Response, Request
    
    request = Request("GET", "https://api.search.brave.com/res/v1/web/search")
    response = Response(status_code=500, request=request)
    return HTTPStatusError("Internal Server Error", request=request, response=response)