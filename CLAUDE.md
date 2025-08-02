# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start

```bash
# Development deployment with hot reload
python deploy.py --mode dev --with-rag

# View logs during development
python deploy.py --mode dev --logs

# Stop all services
python deploy.py --down --mode dev --with-rag

# Check service status
python deploy.py --mode dev --ps
```

### Python Backend Services

**Agent API (agent_api/)**
```bash
cd agent_api
source venv/bin/activate
pip install -r requirements.txt

# Run API server locally
python agent_api.py

# Run tests
pytest tests/ -v
pytest tests/test_agent.py -v
```

**RAG Pipeline Components**
```bash
# Google Drive integration
cd rag_pipeline/Google_Drive
python main.py

# Local file processing
cd rag_pipeline/Local_Files
python main.py
```

### TypeScript Frontend (frontend/)

```bash
cd frontend
npm install

# Development with hot reload
npm run dev

# Production build and start
npm run build
npm run start

# Linting
npm run lint
```

### Database Setup

Execute SQL files in `/sql/` directory in numerical order:
1. `0-all-tables.sql` - Complete schema (alternative to individual files)
2. `1-user_profiles_requests.sql` - Core user management
3. `2-user_profiles_requests_rls.sql` - Row Level Security
4. `3-conversations_messages.sql` - Chat conversation system
5. `4-conversations_messages_rls.sql` - RLS for conversations
6. `5-document_metadata.sql` - RAG metadata
7. `6-document_rows.sql` - RAG tabular data
8. `7-documents.sql` - RAG documents with vectors
9. `8-execute_sql_rpc.sql` - SQL execution function
10. `9-rag_pipeline_state.sql` - RAG state tracking

### Docker Management

```bash
# Development deployment
python deploy.py --mode dev [--with-rag]

# Production deployment
python deploy.py --mode prod [--with-rag]

# Cloud deployment with Caddy
python deploy.py --type cloud [--with-rag]

# Local deployment without Caddy
python deploy.py --type local [--with-rag]

# Custom project name
python deploy.py --mode dev --project my-agent

# Alternative: Using Makefile
make dev           # Development mode
make with-rag      # With RAG pipeline
make logs          # View logs
make down          # Stop services
```

## Architecture Overview

This repository implements a multi-service AI agent system with web search capabilities, document retrieval (RAG), and a modern web interface.

### Service Architecture

**Backend Services:**
- **Agent API**: FastAPI service with Pydantic AI agent, web search (Brave/SearXNG), memory management (Mem0), and MCP server support
- **RAG Pipeline**: Parallel document processors for Google Drive and local files with OpenAI embeddings
- **Database**: PostgreSQL via Supabase with pgvector extension for embeddings

**Frontend:**
- **Next.js Application**: Server-side rendered React app with Supabase authentication and real-time chat interface

### Key Technologies

**Python Stack:**
- Pydantic AI 0.0.9+ for agent framework with dependency injection
- FastAPI with async support and streaming responses
- Supabase Python client for database and auth
- OpenAI SDK for embeddings and LLM integration
- Brave Search Python client for web search
- Mem0 for conversation memory management
- pytest with pytest-asyncio for testing

**TypeScript Stack:**
- Next.js 15 with App Router and React Server Components
- React 19 with TypeScript 5 strict mode
- Tailwind CSS 4 for styling
- Supabase SSR client for authentication

### Database Schema

PostgreSQL with Row Level Security:
- `user_profiles`: User management linked to auth.users with admin flags
- `requests`: Query tracking with user association and timestamps
- `conversations`: Chat sessions with auto-generated titles
- `messages`: JSONB message storage with computed session parsing
- `documents`: Vector embeddings for RAG with metadata
- `document_metadata`: File metadata and table schemas
- `document_rows`: Tabular data from spreadsheets
- `rag_pipeline_state`: Processing state tracking

Session ID format: `{user_id}~{timestamp}` for computed columns

### Environment Configuration

Required environment variables:
- `OPENAI_API_KEY`: OpenAI API access
- `BRAVE_API_KEY`: Brave Search API (optional)
- `SEARXNG_BASE_URL`: SearXNG instance (optional)
- `SUPABASE_URL`: Database URL
- `SUPABASE_ANON_KEY`: Public API key
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for RAG
- `DEBUG_MODE`: Enable debug logging
- `GOOGLE_DRIVE_CREDENTIALS_JSON`: Service account credentials
- `RAG_WATCH_FOLDER_ID`: Google Drive folder to monitor
- `RAG_WATCH_DIRECTORY`: Local directory to monitor

For cloud deployment:
- `AGENT_API_HOSTNAME`: API subdomain (e.g., agent.yourdomain.com)
- `FRONTEND_HOSTNAME`: Frontend subdomain (e.g., chat.yourdomain.com)
- `LETSENCRYPT_EMAIL`: Email for SSL certificates

### Code Patterns

**Python Development:**
- Async-first design with asyncio throughout
- Dependency injection via Pydantic dataclasses
- Tool system with @agent.tool decorators for extensibility
- Type hints with Pydantic validation
- Structured error handling with specific exceptions
- Mock-based testing with pytest fixtures

**TypeScript Development:**
- Async runtime APIs in Next.js 15 (await cookies(), headers(), params, searchParams)
- React Server Components by default, minimize 'use client'
- TypeScript strict mode with proper type safety
- Component structure: exports → subcomponents → helpers → types
- Event handler naming: handleClick, handleSubmit, etc.
- Boolean naming: isLoading, hasError, etc.
- Directory naming: lowercase with dashes (e.g., auth-wizard)

### Testing

**Python Testing:**
```bash
# Agent API tests with mocked dependencies
cd agent_api && pytest tests/ -v

# RAG Pipeline tests
cd rag_pipeline/Local_Files && pytest tests/ -v
```

**TypeScript Testing:**
```bash
cd frontend
npm run lint        # ESLint checking
npm run type-check  # TypeScript validation (if configured)
```

### Docker Support

**Development Mode (`docker-compose.dev.yml`):**
- Hot reload enabled for all services
- Source code mounted as volumes
- Debug mode with verbose logging
- Separate containers for Google Drive and Local Files RAG

**Production Mode (`docker-compose.yml`):**
- Optimized builds with health checks
- No source mounting, uses built images
- Nginx reverse proxy configuration available
- Service dependencies ensure proper startup order

**Cloud Mode (`docker-compose.caddy.yml`):**
- Caddy reverse proxy with automatic SSL
- Domain-based routing for services
- Let's Encrypt certificate provisioning

### Common Issues and Solutions

1. **RAG Permission Errors**: Ensure `SUPABASE_SERVICE_ROLE_KEY` is set
2. **Frontend API Connection**: Verify `PYDANTIC_AGENT_API_URL` matches backend
3. **Google Drive Auth**: Check service account credentials JSON format
4. **Docker Build Failures**: Clear cache with `docker system prune -a`
5. **Port Conflicts**: Check for services using ports 3000, 8001, 8002
6. **Memory Issues**: Increase Docker memory allocation in Docker Desktop