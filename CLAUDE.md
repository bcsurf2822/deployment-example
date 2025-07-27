# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Python Backend Services

**Pydantic AI Agent (Pydantic_Tutorial/)**
```bash
# Setup virtual environment
./setup_venv.sh
source venv/bin/activate
pip install -r requirements.txt

# Run main agent
python agent.py
python run.py

# Run tests
pytest tests/ -v
pytest tests/test_agent.py -v

# Docker operations
docker-compose up pydantic-ai-agent
docker-compose up dev
```

**FastAPI Service (pydantic_api/)**
```bash
cd pydantic_api
source venv/bin/activate
pip install -r requirements.txt

# Run API server
python agent_api.py
```

**RAG Pipeline Components**
```bash
# Google Drive integration
cd RAG_pipeline/Google_Drive
python main.py

# Local file processing
cd RAG_pipeline/Local_Files
python main.py
```

### TypeScript Frontend (pydantic-demo/)

```bash
cd pydantic-demo
npm install

# Development
npm run dev --turbopack

# Production
npm run build
npm run start

# Code quality
npm run lint
```

### Database Setup

Execute SQL files in `/sql/` directory in numerical order:
1. `1_user_profiles.requests.sql` - Core user management
2. `2_user_profiles_requests_rls.sql` - Row Level Security
3. `3_conversations_messages.sql` - Chat conversation system
4. `4_conversations_messages_rls.sql` - RLS for conversations

## Architecture Overview

This repository implements a multi-service AI agent system with web search capabilities, document retrieval (RAG), and a modern web interface.

### Service Architecture

**Backend Services:**
- **Pydantic AI Agent**: Core agent with web search (Brave/SearXNG) and tool system
- **FastAPI Service**: REST API with memory management (Mem0) and conversation handling
- **RAG Pipeline**: Document processing for Google Drive and local files
- **Streamlit UI**: Alternative web interface for the agent

**Frontend:**
- **Next.js Application**: Modern React-based UI with Supabase authentication

### Key Technologies

**Python Stack:**
- Pydantic AI for agent framework with dependency injection
- FastAPI for REST APIs with async support
- Supabase for database and authentication
- OpenAI/OpenRouter/Ollama for LLM providers
- Brave Search and SearXNG for web search
- Mem0 for conversation memory
- pytest for testing with async support

**TypeScript Stack:**
- Next.js 15 with App Router
- React 19 with TypeScript 5
- Tailwind CSS 4
- Supabase client SDK

### Database Schema

PostgreSQL with Row Level Security:
- `user_profiles`: User management linked to auth.users
- `requests`: Query tracking with timestamps
- `conversations`: Chat sessions with auto-generated titles
- `messages`: JSONB message storage with session parsing

Session ID format: `{user_id}~{timestamp}` for computed columns

### Environment Configuration

Required environment variables (see env.example files):
- `OPENAI_API_KEY`: OpenAI API access
- `BRAVE_API_KEY`: Brave Search API
- `SEARXNG_BASE_URL`: SearXNG instance (optional)
- `SUPABASE_URL`: Database URL
- `SUPABASE_ANON_KEY`: Public API key
- `DEBUG_MODE`: Enable debug logging

### Code Patterns

**Python Development:**
- Async-first design with asyncio
- Dependency injection via dataclasses
- Modular tool system for agent capabilities
- Type hints throughout with Pydantic validation
- Structured error handling with fallbacks

**TypeScript Development:**
- Async runtime APIs in Next.js 15 (await cookies(), headers(), etc.)
- React Server Components by default
- TypeScript strict mode enabled
- Component structure: exports, subcomponents, helpers, types
- Event handler naming: handleClick, handleSubmit
- Boolean naming: isLoading, hasError

### Testing

**Python Testing:**
- pytest with pytest-asyncio for async tests
- Mock dependencies for isolated testing
- Test files: `test_*.py` in tests/ directories
- Shared fixtures in conftest.py

**TypeScript Testing:**
- No test suite currently implemented in frontend

### Docker Support

Multi-service orchestration with docker-compose:
- Python 3.11 slim base images
- Non-root user for security
- Volume mounts for development
- Environment variable configuration