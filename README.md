# Pydantic AI Agent Deployment Stack

A comprehensive multi-service AI agent system with web search capabilities, document retrieval (RAG), and modern web interface.

## 🏗️ Architecture Overview

This repository implements a production-ready AI agent system with the following components:

### Core Services

- **Frontend (Next.js)**: Modern React-based web interface with Supabase authentication
- **Agent API (FastAPI)**: Core AI agent with web search, memory management, and tool system
- **RAG Pipeline**: Document processing system for Google Drive and local files
- **Database (Supabase)**: PostgreSQL with Row Level Security for data persistence

### Key Features

- **Multi-LLM Support**: OpenAI, OpenRouter, Ollama integration
- **Web Search**: Brave Search and SearXNG integration
- **Memory Management**: Conversation memory with Mem0
- **Document RAG**: Process PDFs, text files, spreadsheets, and images
- **Authentication**: Secure user management with Supabase Auth
- **Real-time Updates**: Live document monitoring and processing

## 📦 Project Structure

```
├── agent_api/              # FastAPI backend service
├── frontend/               # Next.js web application
├── rag_pipeline/           # Document processing services
│   ├── Google_Drive/       # Google Drive integration
│   ├── Local_Files/        # Local file monitoring
│   └── common/             # Shared utilities
├── sql/                    # Database schema files
├── nginx/                  # Production proxy configuration
└── docker-compose*.yml    # Container orchestration
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Supabase account
- OpenAI API key
- Brave Search API key (optional)

### 1. Environment Setup

Copy and configure environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

Required environment variables:

- `OPENAI_API_KEY`: OpenAI API access
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Public API key
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for RAG operations
- `BRAVE_API_KEY`: Brave Search API (optional)

### 2. Database Setup

Execute SQL files in `/sql/` directory in order:

```bash
# In your Supabase SQL editor, run these files in sequence:
1. 1_user_profiles_requests.sql     # Core user management
2. 2_user_profiles_requests_rls.sql # Row Level Security
3. 3_conversations_messages.sql     # Chat system
4. 4_conversations_messages_rls.sql # Chat RLS
5. 5-document_metadata.sql          # RAG metadata
6. 6-document_rows.sql              # RAG tabular data
7. 7-documents.sql                  # RAG documents
8. 8-execute_sql_rpc.sql            # SQL execution function
9. 9-rag_pipeline_state.sql         # RAG state tracking
```

### 3. Deployment

Use the `deploy.py` script for all deployment operations:

## 🛠️ Deployment Commands

The `deploy.py` script provides a unified interface for managing the entire stack:

### Basic Usage

```bash
# Make script executable (first time only)
chmod +x deploy.py

# Development deployment
python deploy.py --mode dev

# Development with RAG pipeline
python deploy.py --mode dev --with-rag

# Production deployment
python deploy.py --mode prod

# Production with RAG pipeline
python deploy.py --mode prod --with-rag
```

### Management Commands

```bash
# Stop services
python deploy.py --down --mode dev

# Stop services with RAG pipeline
python deploy.py --down --mode dev --with-rag

# View logs (live tail)
python deploy.py --mode dev --logs

# Check container status
python deploy.py --mode dev --ps

# Custom project name
python deploy.py --mode dev --project my-agent
```

### 🔄 Redeploying Latest Changes

When you've made code changes and want to redeploy with the latest updates:

```bash
# Quick redeploy (rebuilds only changed services)
python deploy.py --mode dev --with-rag

# Force rebuild all containers
python deploy.py --down --mode dev
python deploy.py --mode dev --with-rag

# Rebuild specific service (using docker compose directly)
docker compose -p pydantic-agent -f docker-compose.dev.yml up -d --build agent-api-dev

# Apply changes without rebuilding (for config/env changes)
docker compose -p pydantic-agent -f docker-compose.dev.yml restart

# Hot reload notes:
# - Frontend: Changes apply automatically (Next.js hot reload)
# - Agent API: Python files reload automatically (uvicorn --reload)
# - RAG Pipeline: Requires container restart for code changes
```

### Common Development Workflows

```bash
# Working on frontend only
cd frontend && npm run dev  # Local development
# OR
python deploy.py --mode dev  # Containerized

# Working on agent API
python deploy.py --mode dev --logs  # Watch logs while developing

# Testing RAG pipeline changes
python deploy.py --down --mode dev  # Stop everything
python deploy.py --mode dev --with-rag  # Fresh start with RAG

# Quick restart after .env changes
docker compose -p pydantic-agent -f docker-compose.dev.yml restart

# Check what's running
docker ps --filter "name=pydantic-agent"
```

### Complete Command Reference

| Command          | Description                        |
| ---------------- | ---------------------------------- |
| `--mode dev`     | Development mode with hot reload   |
| `--mode prod`    | Production mode with optimizations |
| `--with-rag`     | Include RAG pipeline services      |
| `--down`         | Stop and remove containers         |
| `--logs`         | Show live logs from all services   |
| `--ps`           | Show container status              |
| `--project NAME` | Custom Docker Compose project name |

### Examples

```bash
# Start development environment
python deploy.py --mode dev --with-rag

# Check if everything is running
python deploy.py --mode dev --ps

# Watch logs for debugging
python deploy.py --mode dev --logs

# Stop everything when done
python deploy.py --down --mode dev --with-rag

# Production deployment
python deploy.py --mode prod --with-rag
```

## 🐳 Docker Compose Files

### `docker-compose.dev.yml` - Development Environment

**Purpose**: Local development with hot reload and debugging capabilities

**Services**:

- `frontend-dev`: Next.js with Turbopack and live reload
- `agent-api-dev`: FastAPI with auto-restart on code changes
- `rag-google-drive-dev`: Google Drive document processor
- `rag-local-files-dev`: Local file system monitor

**Features**:

- Source code mounted as volumes
- Hot reload for all services
- Debug mode enabled
- Development ports exposed
- Separate RAG services for parallel processing

**Access**:

- Frontend: http://localhost:3000
- API: http://localhost:8001

### `docker-compose.yml` - Production Environment

**Purpose**: Production deployment with optimized builds and health checks

**Services**:

- `frontend`: Production Next.js build served via Nginx
- `agent-api`: Production FastAPI with MCP server
- `agent-api-simple`: Simplified API without MCP (profile: simple)

**Features**:

- Optimized production builds
- Health checks for all services
- Nginx reverse proxy
- Persistent volumes
- Service dependencies

**Access**:

- Frontend: http://localhost:3000 (via Nginx)
- API: http://localhost:8001
- Simple API: http://localhost:8002

### `docker-compose.prod.yml` - Production Alternative

**Purpose**: Alternative production configuration

**Note**: Currently mirrors the main production setup. Can be customized for different production environments (staging, etc.).

## 📁 Service Details

### Frontend Service (`frontend/`)

**Technology**: Next.js 15 with React 19, TypeScript, Tailwind CSS

**Key Features**:

- Server-side rendering with App Router
- Supabase authentication integration
- Real-time chat interface
- Responsive design with Tailwind CSS

**Development**:

```bash
cd frontend
npm install
npm run dev --turbopack
```

**Key Files**:

- `app/api/chat/route.ts`: Chat API endpoint
- `app/chat/page.tsx`: Main chat interface
- `components/chat/`: Chat UI components
- `lib/supabase/`: Supabase client configuration

### Agent API Service (`agent_api/`)

**Technology**: FastAPI with Pydantic AI, async Python

**Key Features**:

- Pydantic AI agent with dependency injection
- Web search via Brave/SearXNG
- Memory management with Mem0
- Tool system for extensible capabilities
- MCP (Model Context Protocol) server

**Development**:

```bash
cd agent_api
source venv/bin/activate
pip install -r requirements.txt
python agent_api.py
```

**Key Files**:

- `agent_api.py`: Main FastAPI application
- `agent.py`: Core Pydantic AI agent
- `tools.py`: Agent tool implementations
- `dependencies.py`: Dependency injection setup

### RAG Pipeline Services (`rag_pipeline/`)

**Technology**: Python with asyncio, OpenAI embeddings, Supabase vector storage

#### Google Drive Service (`Google_Drive/`)

**Purpose**: Monitor and process documents from Google Drive

**Features**:

- Real-time Google Drive monitoring
- Service account authentication
- Incremental document processing
- Automatic text extraction and chunking

**Configuration**:

- Set `GOOGLE_DRIVE_CREDENTIALS_JSON` in .env
- Configure `RAG_WATCH_FOLDER_ID` for specific folder monitoring

#### Local Files Service (`Local_Files/`)

**Purpose**: Monitor and process local file system documents

**Features**:

- File system watching with automatic updates
- Support for multiple file formats (PDF, TXT, CSV, images)
- Configurable watch directory
- Change detection and incremental updates

**Configuration**:

- Set `RAG_WATCH_DIRECTORY` in .env (defaults to `/app/Local_Files/data`)
- Mount host directory to container path in docker-compose

**Supported Formats**:

- Documents: PDF, TXT, HTML, Markdown
- Spreadsheets: CSV, Excel
- Images: PNG, JPG, SVG
- Google Docs exports

### Database Schema (`sql/`)

**Technology**: PostgreSQL with pgvector extension via Supabase

**Core Tables**:

- `user_profiles`: User management linked to auth.users
- `conversations`: Chat sessions with auto-generated titles
- `messages`: JSONB message storage with session parsing
- `documents`: Vector embeddings for RAG
- `document_metadata`: File metadata and schemas
- `document_rows`: Tabular data from spreadsheets

**Security**: Row Level Security (RLS) policies protect user data

## 🔧 Configuration

### Environment Variables

Create `.env` file in the root directory:

```bash
# Core API Configuration
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
VISION_MODEL=gpt-4o-mini

# Search Configuration
BRAVE_API_KEY=your_brave_key
SEARXNG_BASE_URL=http://localhost:8080  # Optional

# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# RAG Configuration
RAG_WATCH_DIRECTORY=/app/Local_Files/data
RAG_WATCH_FOLDER_ID=your_google_drive_folder_id
GOOGLE_DRIVE_CREDENTIALS_JSON={"type":"service_account",...}

# Application Settings
DEBUG_MODE=true
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### RAG Pipeline Configuration

Each RAG service has its own `config.json`:

```json
{
  "supported_mime_types": [
    "application/pdf",
    "text/plain",
    "text/csv",
    "image/png"
  ],
  "text_processing": {
    "chunk_size": 1000,
    "default_chunk_overlap": 0
  }
}
```

## 🧪 Testing

### Python Services

```bash
# Agent API tests
cd agent_api
pytest tests/ -v

# RAG Pipeline tests
cd rag_pipeline/Local_Files
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm run lint
npm run type-check
```

## 📊 Monitoring & Debugging

### View Logs

```bash
# All services
python deploy.py --mode dev --logs

# Specific service
docker logs pydantic-agent-frontend-dev-1 -f
```

### Health Checks

All production services include health checks:

```bash
# Check health status
python deploy.py --mode dev --ps

# Manual health check
curl http://localhost:8001/health
```

### Common Issues

1. **RAG Permission Errors**: Ensure service role key is set and paths are correct
2. **Frontend API Connection**: Verify `PYDANTIC_AGENT_API_URL` environment variable
3. **Google Drive Auth**: Check service account credentials and folder permissions

## 🚦 Production Deployment

### Security Checklist

- [ ] Use service role key for RAG operations
- [ ] Enable HTTPS with proper certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Monitor resource usage
- [ ] Enable logging aggregation

### Scaling Considerations

- Use Docker Swarm or Kubernetes for orchestration
- Configure load balancer for multiple frontend instances
- Set up Redis for session storage
- Use external vector database for large RAG deployments
- Implement monitoring with Prometheus/Grafana

## 📚 Development Workflow

1. **Setup**: Clone repo, configure `.env`, run database migrations
2. **Development**: Use `python deploy.py --mode dev --with-rag`
3. **Testing**: Run test suites for modified components
4. **Code Quality**: Use linting and type checking
5. **Deployment**: Test with `--mode prod` before production release

## 🤝 Contributing

1. Follow the existing code patterns and conventions
2. Add tests for new features
3. Update documentation for API changes
4. Use the type system throughout (Python + TypeScript)
5. Follow security best practices

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.
# deployment-example
