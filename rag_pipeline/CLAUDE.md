# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Workflow

```bash
# Start development with hot reload
python deploy.py --mode dev --with-rag

# View logs for debugging
python deploy.py --mode dev --logs

# Stop all services
python deploy.py --down --mode dev --with-rag

# Quick redeploy after changes
python deploy.py --mode dev --with-rag  # Rebuilds only changed services
```

### Testing Commands

```bash
# Run Agent API tests
cd agent_api && pytest tests/ -v

# Run specific test file
cd agent_api && pytest tests/test_agent.py -v

# Run RAG Pipeline tests
cd rag_pipeline/Local_Files && pytest tests/ -v

# Frontend linting
cd frontend && npm run lint

# Run all tests via Makefile
make test
```

### Local Development Without Docker

```bash
# Agent API
cd agent_api
source venv/bin/activate  # Or python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python agent_api.py  # Runs on port 8001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # Runs on port 3000 with hot reload

# RAG Pipeline (separate terminals)
cd rag_pipeline/Google_Drive && python main.py
cd rag_pipeline/Local_Files && python main.py
```

### Database Setup

Execute SQL files in `/sql/` directory in numerical order via Supabase SQL editor:
1. `0-all-tables.sql` - Complete schema (use this OR individual files 1-9)
2. Or execute files 1-9 individually in sequence

## Architecture Overview

### Multi-Service System

**Core Services:**
- **Agent API** (`agent_api/`): FastAPI service with Pydantic AI agent, web search (Brave/SearXNG), memory management (Mem0), MCP server support
- **RAG Pipeline** (`rag_pipeline/`): Parallel document processors for Google Drive and local files with OpenAI embeddings
- **Frontend** (`frontend/`): Next.js 15 with App Router, React 19, Supabase authentication, real-time chat interface
- **Database**: PostgreSQL via Supabase with pgvector extension for embeddings

### Key Technical Patterns

**Python Development (agent_api/, rag_pipeline/):**
- Async-first design with asyncio throughout
- Dependency injection via Pydantic dataclasses
- Tool system with @agent.tool decorators for extensibility
- Mock-based testing with pytest fixtures
- Structured error handling with specific exceptions

**TypeScript Development (frontend/):**
- Async runtime APIs in Next.js 15 (await cookies(), headers(), params, searchParams)
- React Server Components by default, minimize 'use client'
- TypeScript strict mode with proper type safety
- Event handler naming: handleClick, handleSubmit, etc.
- Boolean naming: isLoading, hasError, etc.

### Session ID Format

Sessions use format: `{user_id}~{timestamp}` for computed columns in database

### Environment Variables

Critical variables for RAG Pipeline development:
- `SUPABASE_SERVICE_ROLE_KEY`: Required for RAG operations (not anon key)
- `GOOGLE_DRIVE_CREDENTIALS_JSON`: Service account JSON for Google Drive
- `RAG_WATCH_FOLDER_ID`: Google Drive folder to monitor
- `RAG_WATCH_DIRECTORY`: Local directory to monitor (defaults to /app/Local_Files/data)
- `DEBUG_MODE`: Enable verbose logging

### Docker Compose Files

- **docker-compose.dev.yml**: Hot reload, source volumes, debug mode, separate RAG containers
- **docker-compose.yml**: Production builds, health checks, optimized images
- **docker-compose.caddy.yml**: Cloud deployment with automatic SSL via Caddy

### Common Troubleshooting

1. **RAG Permission Errors**: Ensure `SUPABASE_SERVICE_ROLE_KEY` is set (not anon key)
2. **Frontend API Connection**: Verify `PYDANTIC_AGENT_API_URL` matches backend (default: http://agent-api-dev:8001)
3. **Google Drive Auth**: Check service account credentials JSON format
4. **Port Conflicts**: Check for services using ports 3000, 8001, 8002
5. **Docker Build Failures**: Clear cache with `docker system prune -a`

### File Processing (RAG Pipeline)

**Google Drive config.json (`rag_pipeline/Google_Drive/config.json`):**
- Supported MIME types including Google Docs exports
- Tabular data processing for CSV/Excel files
- Text chunking configuration (default_chunk_size: 400)
- watch_folder_id and last_check_time for incremental processing

**Supported Formats:**
- Documents: PDF, TXT, HTML, Markdown
- Spreadsheets: CSV, Excel, Google Sheets
- Images: PNG, JPG, SVG
- Google Docs: Exported as text/plain or CSV