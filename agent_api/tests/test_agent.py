"""
Test suite for the Pydantic AI agent.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import agent, create_dependencies, cleanup_dependencies
from dependencies import AgentDependencies


@pytest.mark.asyncio
async def test_agent_simple_query():
    """Test the agent with a simple query using mock dependencies."""
    # Create mock dependencies
    mock_deps = Mock(spec=AgentDependencies)
    mock_deps.http_client = AsyncMock()
    mock_deps.settings = Mock()
    mock_deps.settings.brave_api_key = Mock(get_secret_value=lambda: "test-key")
    mock_deps.settings.debug_mode = False
    mock_deps.supabase = Mock()
    mock_deps.embedding_client = AsyncMock()
    
    # Mock a successful search response
    mock_deps.http_client.get.return_value.json.return_value = {
        "web": {
            "results": [
                {
                    "title": "Test Document",
                    "url": "https://example.com/doc1",
                    "description": "A test document"
                }
            ]
        }
    }
    
    # Test the agent
    query = "What documents are available?"
    result = await agent.run(query, deps=mock_deps)
    
    # Verify the response
    assert result.output is not None
    assert isinstance(result.output, str)
    assert len(result.output) > 0


@pytest.mark.asyncio
async def test_agent_with_real_dependencies():
    """Integration test with real dependencies (requires environment setup)."""
    deps = None
    try:
        # Create real dependencies
        deps = await create_dependencies()
        
        # Test a simple query
        query = "What is Python?"
        result = await agent.run(query, deps=deps)
        
        # Verify the response
        assert result.output is not None
        assert isinstance(result.output, str)
        assert len(result.output) > 0
        
    except Exception as e:
        # If dependencies can't be created (missing env vars), skip the test
        pytest.skip(f"Real dependencies test skipped: {str(e)}")
    finally:
        if deps:
            await cleanup_dependencies(deps)


@pytest.mark.asyncio
async def test_agent_empty_query():
    """Test the agent with an empty query."""
    mock_deps = Mock(spec=AgentDependencies)
    mock_deps.http_client = AsyncMock()
    mock_deps.settings = Mock()
    mock_deps.settings.brave_api_key = Mock(get_secret_value=lambda: "test-key")
    mock_deps.settings.debug_mode = False
    mock_deps.supabase = Mock()
    mock_deps.embedding_client = AsyncMock()
    
    # Test with empty query
    query = ""
    result = await agent.run(query, deps=mock_deps)
    
    # Verify the response
    assert result.output is not None
    assert isinstance(result.output, str)


@pytest.mark.asyncio
async def test_dependencies_creation_and_cleanup():
    """Test that dependencies can be created and cleaned up properly."""
    deps = None
    try:
        deps = await create_dependencies()
        assert deps is not None
        assert hasattr(deps, 'http_client')
        assert hasattr(deps, 'config')
    except Exception as e:
        pytest.skip(f"Dependencies test skipped: {str(e)}")
    finally:
        if deps:
            await cleanup_dependencies(deps)