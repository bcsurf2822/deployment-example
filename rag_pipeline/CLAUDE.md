# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Running the RAG Pipeline

```bash
# Google Drive Pipeline
cd Google_Drive
python main.py --interval 60 --folder-id <folder_id>
python main.py --single-run  # Run once and exit

# Local Files Pipeline
cd Local_Files  
python main.py --directory /path/to/watch --interval 60
python main.py --single-run  # Run once and exit

# With Docker (service-specific)
RAG_SERVICE=google_drive python -m venv venv && source venv/bin/activate
RAG_SERVICE=local_files python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Testing

```bash
# Run Local Files tests with proper path setup
cd Local_Files && python -m pytest tests/ -v
python -m pytest tests/test_file_watcher.py::TestLocalFilesWatcher::test_process_new_file -v

# Mock-based testing using conftest.py fixtures
python -m pytest tests/ -v --tb=short
```

### Status Monitoring

```bash
# Check pipeline status (when running)
curl http://localhost:8003/status  # Legacy status server
curl http://localhost:8003/health

# Check Supabase pipeline state
python -c "from supabase_status import init_status_tracker; print('Status OK')"
```

## Architecture Overview

### Core Components

**Main Services:**
- `Google_Drive/main.py` - Google Drive file monitoring with OAuth2/Service Account auth
- `Local_Files/main.py` - Local directory file monitoring with MD5-based file IDs
- `status_server.py` - HTTP status endpoint (port 8003) with threading 
- `supabase_status.py` - Database-based heartbeat and status tracking

**Common Modules:**
- `common/text_processor.py` - Text chunking, PDF extraction, OpenAI embeddings
- `common/db_handler.py` - Supabase operations for documents/metadata/rows tables
- `common/sync_manager.py` - Orphaned file cleanup and pipeline state persistence

**Entry Points:**
- `entrypoint.sh` - Docker service selection via `RAG_SERVICE` env var
- `healthcheck.sh` - Docker health check script

### Processing Flow

1. **File Discovery**: 
   - Google Drive: Uses Google Drive API with OAuth2 or service account
   - Local Files: Recursive directory scanning with `os.walk()`

2. **Change Detection**:
   - Google Drive: Compares `modifiedTime` from API against stored state
   - Local Files: Compares filesystem `mtime` against known files dictionary

3. **Content Extraction**: 
   - PDF: `pypdf.PdfReader` for text extraction
   - Text files: Direct UTF-8 reading with fallback encoding
   - CSV/Excel: Tabular processing for both chunks and row-by-row storage

4. **Text Chunking**: 
   - Configurable chunk size (default 1000 chars Local Files, 400 Google Drive)
   - No overlap by default (configurable)
   - Text cleaning (remove `\r` characters)

5. **Embedding Generation**: 
   - OpenAI `text-embedding-3-small` model
   - Batched processing for efficiency
   - Error handling with retry logic

6. **Database Storage**:
   - `documents` table: Text chunks + embeddings (pgvector)
   - `document_metadata` table: File info and CSV schemas  
   - `document_rows` table: Row-by-row tabular data
   - `rag_pipeline_state` table: Pipeline state and known files

7. **Orphaned Cleanup**: 
   - `PipelineSyncManager` tracks database vs source state
   - Automatic deletion of documents for removed/moved files
   - Statistics tracking for cleanup operations

### Database Schema

**Key Tables:**
- `documents` - Chunks with embeddings, metadata JSONB field
- `document_metadata` - File metadata, table schemas for CSVs  
- `document_rows` - Individual rows from spreadsheets/CSVs
- `rag_pipeline_state` - Pipeline persistence and known files tracking

**Critical Fields:**
- `documents.metadata->>'file_id'` - Links chunks to source files
- `documents.metadata->>'source'` - Pipeline type ('google_drive' or 'local_files')
- `rag_pipeline_state.known_files` - JSONB dict of file_id -> metadata

### Configuration Files

**Google_Drive/config.json:**
```json
{
  "supported_mime_types": [
    "application/pdf", "text/plain", "text/csv",
    "application/vnd.google-apps.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  ],
  "tabular_mime_types": ["text/csv", "application/vnd.ms-excel"],
  "text_processing": {"chunk_size": 400, "default_chunk_overlap": 0},
  "watch_folder_id": "1ABC...xyz",
  "last_check_time": "2025-08-23T20:05:08Z"
}
```

**Local_Files/config.json:**
```json
{
  "supported_mime_types": [...],
  "text_processing": {"chunk_size": 1000},
  "watch_directory": "/app/Local_Files/data",
  "last_check_time": "2025-08-23T20:05:08Z"
}
```

### Environment Variables

**Required:**
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx  # Must be service role, not anon key
OPENAI_API_KEY=sk-xxx
```

**Google Drive:**
```bash
GOOGLE_DRIVE_CREDENTIALS_JSON={"type": "service_account", ...}  # Service account
RAG_WATCH_FOLDER_ID=1ABC...xyz
```

**Local Files:**
```bash
RAG_WATCH_DIRECTORY=/app/Local_Files/data
```

**Optional:**
```bash
RAG_SERVICE=google_drive|local_files  # Docker service selection
RAG_PIPELINE_ID=custom-pipeline-id    # Unique pipeline identifier
RUN_MODE=single                       # Enable single-run mode
DEBUG_MODE=true
```

### Key Implementation Details

**File ID Generation:**
- Google Drive: Uses native Google Drive file ID
- Local Files: MD5 hash of absolute file path (`hashlib.md5(abs_path.encode())`)

**Authentication:**
- Google Drive: Service account (env var) or OAuth2 flow (credentials.json)
- Local Files: File system permissions only

**Threading and Concurrency:**
- Status server runs in background daemon thread
- Heartbeat updates via separate thread in `supabase_status.py`
- Main processing is single-threaded with proper exception handling

**Error Handling:**
- `Resource deadlock avoided` - macOS Docker + cloud sync folders
- Google API quota/auth errors with retry logic
- Supabase connection failures with graceful degradation
- File access permissions with detailed logging

**Testing Patterns:**
- Mock-based testing with `conftest.py` fixtures
- Temporary directory creation/cleanup
- Mocked Supabase and OpenAI clients
- Environment variable patching

### Deployment Modes

**Single-Run Mode:**
- Processes all changes once and exits
- Returns statistics: `files_processed`, `files_deleted`, `errors`, `duration`
- Exit codes: 0 (success), 1 (errors occurred)

**Continuous Mode:**
- Infinite loop with configurable interval (default 60s)
- Graceful shutdown with SIGTERM/SIGINT handling
- Persistent state via database and config files

**Docker Deployment:**
```bash
# Build image
docker build -t rag-pipeline .

# Google Drive service
docker run -e RAG_SERVICE=google_drive \
  -e SUPABASE_URL=xxx \
  -e SUPABASE_SERVICE_ROLE_KEY=xxx \
  -e GOOGLE_DRIVE_CREDENTIALS_JSON='{}' \
  -e RAG_WATCH_FOLDER_ID=xxx \
  rag-pipeline

# Local Files service  
docker run -e RAG_SERVICE=local_files \
  -v /host/path:/app/Local_Files/data \
  -e SUPABASE_URL=xxx \
  -e SUPABASE_SERVICE_ROLE_KEY=xxx \
  rag-pipeline
```

### Common Issues

1. **Permission Denied**: Ensure `SUPABASE_SERVICE_ROLE_KEY` not `SUPABASE_ANON_KEY`
2. **Google Auth Failed**: Check service account JSON format and Drive API permissions
3. **No Files Processing**: Verify `last_check_time` in config.json isn't too recent  
4. **Embedding Errors**: Confirm `OPENAI_API_KEY` is valid and has quota
5. **Docker Volume Issues**: Check mounted directory permissions (user 1001:1001)
6. **Cloud Sync Deadlock**: Move files out of iCloud/Dropbox/OneDrive folders
7. **State Persistence**: Verify `rag_pipeline_state` table exists in Supabase