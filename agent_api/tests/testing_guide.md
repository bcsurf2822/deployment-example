# Testing Guide for Pydantic AI Agent

This guide provides best practices for writing tests in our Pydantic AI agent project using pytest.

## Test Structure and Organization

### File Naming Convention
- Test files should be named `test_*.py` or `*_test.py`
- Place all tests in the `basic_pydantic_agent/tests/` directory
- Group related tests in the same file (e.g., `test_agent.py`, `test_tools.py`, `test_dependencies.py`)

### Basic Test Structure
```python
# Standard pytest test function
def test_function_name():
    # Arrange
    expected = "expected value"
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected
```

### Async Test Structure
Since our agent uses async/await patterns, we need pytest-asyncio:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    # Arrange
    deps = await create_test_dependencies()
    
    # Act
    result = await async_function(deps)
    
    # Assert
    assert result.status == "success"
```

## Writing Tests for Our Agent

### Testing the Agent
```python
import pytest
from unittest.mock import Mock, AsyncMock
from basic_pydantic_agent.agent import agent
from basic_pydantic_agent.dependencies import AgentDependencies

@pytest.mark.asyncio
async def test_agent_simple_query():
    # Create mock dependencies
    mock_deps = Mock(spec=AgentDependencies)
    mock_deps.http_client = AsyncMock()
    
    # Test the agent
    result = await agent.run("What is the weather?", deps=mock_deps)
    
    # Verify
    assert result.output is not None
    assert isinstance(result.output, str)
```

### Testing Tools
```python
import pytest
from unittest.mock import AsyncMock
from basic_pydantic_agent.tools import brave_search
from basic_pydantic_agent.dependencies import AgentDependencies

@pytest.mark.asyncio
async def test_brave_search_tool():
    # Mock dependencies
    mock_deps = Mock(spec=AgentDependencies)
    mock_deps.http_client = AsyncMock()
    mock_deps.http_client.get.return_value.json.return_value = {
        "results": [{"title": "Test", "url": "http://test.com"}]
    }
    
    # Test the tool
    result = await brave_search(mock_deps, "test query")
    
    # Verify
    assert "Test" in result
    assert "http://test.com" in result
```

## Fixtures

### Common Fixtures
Create reusable test fixtures in `conftest.py`:

```python
# basic_pydantic_agent/tests/conftest.py
import pytest
from unittest.mock import Mock, AsyncMock
from basic_pydantic_agent.dependencies import AgentDependencies

@pytest.fixture
async def mock_dependencies():
    """Create mock dependencies for testing."""
    deps = Mock(spec=AgentDependencies)
    deps.http_client = AsyncMock()
    deps.config = Mock()
    deps.config.brave_api_key = Mock(get_secret_value=lambda: "test-key")
    return deps

@pytest.fixture
def sample_search_response():
    """Sample Brave search API response."""
    return {
        "web": {
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "description": "Test description"
                }
            ]
        }
    }
```

### Using Fixtures
```python
@pytest.mark.asyncio
async def test_with_fixture(mock_dependencies, sample_search_response):
    mock_dependencies.http_client.get.return_value.json.return_value = sample_search_response
    # Test code here
```

## Testing Best Practices

### 1. Keep Tests Small and Focused
- One test should verify one behavior
- Use descriptive test names that explain what is being tested

### 2. Use Mocks for External Dependencies
```python
# Mock HTTP calls
mock_http_client = AsyncMock()
mock_http_client.get.return_value.json.return_value = {"data": "test"}

# Mock file operations
with patch("builtins.open", mock_open(read_data="test content")):
    result = read_file("test.txt")
```

### 3. Test Error Cases
```python
@pytest.mark.asyncio
async def test_agent_handles_error():
    mock_deps = Mock(spec=AgentDependencies)
    mock_deps.http_client.get.side_effect = Exception("Network error")
    
    with pytest.raises(Exception):
        await agent.run("test query", deps=mock_deps)
```

### 4. Use Parametrize for Multiple Test Cases
```python
@pytest.mark.parametrize("query,expected", [
    ("What is Python?", "programming language"),
    ("Tell me about AI", "artificial intelligence"),
    ("", "empty query"),
])
@pytest.mark.asyncio
async def test_agent_various_queries(mock_dependencies, query, expected):
    result = await agent.run(query, deps=mock_dependencies)
    assert expected in result.output.lower()
```

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_agent.py

# Run specific test function
pytest tests/test_agent.py::test_agent_simple_query

# Run tests matching pattern
pytest -k "search"

# Run with coverage
pytest --cov=basic_pydantic_agent
```

### Async Test Considerations
- Always use `@pytest.mark.asyncio` decorator for async tests
- Use `AsyncMock` instead of `Mock` for async methods
- Await all async calls in tests

## Example: Converting Existing Test

Here's how to convert a basic test script to pytest format:

**Before (manual test script):**
```python
async def test_agent():
    deps = await create_dependencies()
    try:
        result = await agent.run("query", deps=deps)
        print(f"Result: {result}")
    finally:
        await cleanup_dependencies(deps)
```

**After (pytest format):**
```python
@pytest.mark.asyncio
async def test_agent_query(mock_dependencies):
    # No manual setup/cleanup needed
    result = await agent.run("query", deps=mock_dependencies)
    
    # Use assertions instead of prints
    assert result.output is not None
    assert len(result.output) > 0
```

## Next Steps

1. Start with simple unit tests for individual functions
2. Add integration tests for complete workflows
3. Consider adding performance tests for critical paths
4. Set up continuous integration to run tests automatically