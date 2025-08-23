# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Agent API

```bash
# Local development with hot reload
source venv/bin/activate
python agent_api.py

# Direct agent testing
python run.py

# Testing with health check
curl http://localhost:8001/health

# View MCP server status
curl http://localhost:8001/api/mcp/servers
```

### Testing Commands

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_agent.py -v

# Run with async support
pytest tests/ -v --asyncio-mode=auto
```

### Linting and Code Quality

```bash
# Format code with Black
black . --line-length=88

# Type checking with MyPy
mypy agent_api.py agent.py

# Install dependencies
pip install -r requirements.txt
```

## Architecture Overview

This is a **FastAPI-based AI agent service** built with Pydantic AI that provides:

- **Streaming conversational AI** with real-time token streaming
- **RAG (Retrieval-Augmented Generation)** with vector embeddings
- **Web search capabilities** via Brave Search API
- **MCP (Model Context Protocol)** integration for extensible tooling
- **Memory management** with Mem0 for conversation persistence
- **Authentication** via Supabase JWT tokens

### Core Technologies

**Pydantic AI Framework:**
- Agent definition with dependency injection pattern
- Tool registration using `@agent.tool` decorators
- Dynamic toolsets from MCP servers
- RunContext for dependency access in tools

**FastAPI Service Architecture:**
- Async lifespan management for client initialization
- Streaming responses with Server-Sent Events
- JWT authentication with Supabase verification
- Rate limiting and request tracking

**Database Integration:**
- Supabase PostgreSQL with Row Level Security (RLS)
- Vector embeddings storage using pgvector
- Conversation and message persistence
- Document metadata and RAG content storage

### Key Components

**Agent System** (`agent.py`):
- Main Pydantic AI agent with OpenAI model integration
- Built-in tools: web search, document retrieval, SQL queries, image analysis
- Dynamic system prompt with user memory integration
- MCP toolset support for runtime tool extension

**MCP Manager** (`mcp_manager.py`):
- Dynamic MCP server lifecycle management
- Health checking and auto-recovery
- Multiple transport types (SSE, Stdio, HTTP)
- Runtime server registration/unregistration

**Tools** (`tools.py`):
- Web search via Brave Search API
- RAG document retrieval with embeddings
- SQL query execution on structured data
- Image analysis with vision models

**Dependencies** (`dependencies.py`):
- Dependency injection dataclass pattern
- Client initialization (OpenAI, Supabase, HTTP, Mem0)
- Settings management with pydantic-settings

### Request Flow

1. **Authentication**: JWT token validation against Supabase
2. **Rate Limiting**: Check user request limits
3. **Conversation Management**: Create/retrieve conversation history
4. **Memory Retrieval**: Fetch relevant user memories with Mem0
5. **Agent Execution**: Run Pydantic AI agent with streaming
6. **Response Storage**: Store messages and update conversation titles
7. **Memory Storage**: Update user memories post-conversation

### Environment Configuration

Required environment variables:
- `OPENAI_API_KEY`: OpenAI API access for LLM and embeddings
- `BRAVE_API_KEY`: Brave Search API (optional, falls back to SearXNG)
- `SEARXNG_BASE_URL`: SearXNG instance URL (optional)
- `SUPABASE_URL`: Database connection
- `SUPABASE_ANON_KEY`: Public API key for authentication
- `SUPABASE_SERVICE_ROLE_KEY`: Service role for bypassing RLS
- `DEBUG_MODE`: Enable detailed logging

### MCP Integration

**Configuration** (`mcp_config.json`):
- Default Python executor server on port 3001
- SSE transport with auto-start capability
- Health checking and retry logic

**Manager Features**:
- Dynamic server registration via REST API
- Multiple transport types (SSE, Stdio, HTTP)
- Automatic health monitoring and recovery
- Tool prefix support for namespace isolation

### Testing Strategy

**Async Testing Pattern**:
```python
@pytest.mark.asyncio
async def test_agent_tool(mock_dependencies):
    # Arrange
    mock_deps = Mock(spec=AgentDependencies)
    mock_deps.http_client = AsyncMock()
    
    # Act
    result = await agent.run("test query", deps=mock_deps)
    
    # Assert
    assert result.output is not None
```

**Dependency Mocking**:
- Use `AsyncMock` for async dependencies
- Mock HTTP clients, database connections
- Fixture-based test setup in `conftest.py`

### Code Patterns

**Tool Registration**:
```python
@agent.tool
async def tool_name(ctx: RunContext[AgentDependencies], param: str) -> str:
    """Tool description for LLM."""
    return await actual_implementation(ctx.deps.client, param)
```

**Dependency Injection**:
```python
@dataclass
class AgentDependencies:
    http_client: AsyncClient
    supabase: Client
    settings: Settings
```

**Streaming Response Pattern**:
```python
async def stream_response():
    async with agent.iter(query, deps=deps) as run:
        async for node in run:
            if isinstance(node, ModelRequestNode):
                # Stream tokens in real-time
                yield json.dumps({"text": content})
```

### Security Considerations

- JWT token verification for all API endpoints
- Row Level Security (RLS) policies on database tables
- Service role key isolation for system operations
- Rate limiting per user
- Input validation with Pydantic models

### Common Development Patterns

**Error Handling**:
- Stream error responses instead of raising HTTPException
- Store error messages in conversation history
- Graceful degradation when services are unavailable

**Resource Management**:
- Lifespan context managers for client initialization
- Proper cleanup of async resources
- Connection pooling for database and HTTP clients

**Logging Format**:
Use the format: `[FILENAME-FUNCTION] description of operation`