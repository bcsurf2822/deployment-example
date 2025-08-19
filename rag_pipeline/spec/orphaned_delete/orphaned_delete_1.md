# RAG Pipeline Orphaned Document Deletion Implementation

## Overview
This document describes the implementation of automatic synchronization and deletion of orphaned documents in the RAG pipeline when files are removed from source systems (Google Drive or Local Files).

## Problem Statement
Previously, when files were deleted from Google Drive or the local file system while the pipeline was not running, those deletions would not be detected, leading to orphaned documents in Supabase that no longer existed in the source.

## Solution Architecture

### 1. Core Components Created

#### 1.1 `sync_manager.py` (New Module)
Location: `/rag_pipeline/common/sync_manager.py`

**Purpose**: Centralized synchronization logic for managing pipeline state persistence and orphaned document detection.

**Key Class**: `PipelineSyncManager`
- **Initialization**: Takes Supabase client, pipeline_id, and pipeline_type
- **State Management**:
  - `load_pipeline_state()`: Loads known_files from `rag_pipeline_state` table
  - `save_pipeline_state()`: Persists known_files to database
- **Orphan Detection**:
  - `get_all_document_file_ids()`: Queries all file IDs from documents table
  - `find_orphaned_documents()`: Compares Supabase documents with current source files
  - `sync_deletions()`: Deletes orphaned documents in batch

### 2. Database Integration

#### 2.1 `rag_pipeline_state` Table Utilization
**Schema**:
```sql
- pipeline_id (TEXT PRIMARY KEY): Unique identifier for each pipeline instance
- pipeline_type (TEXT): 'google_drive' or 'local_files'
- known_files (JSONB): Stores {file_id: {modifiedTime, ...}} mapping
- last_check_time (TIMESTAMP): Last successful check
- last_run (TIMESTAMP): Last successful run
```

**Purpose**: Persists file tracking state across pipeline restarts to enable detection of deletions that occurred while offline.

### 3. Pipeline Modifications

#### 3.1 Google Drive Pipeline (`drive_watcher.py`)

**Initialization Changes**:
```python
# Added sync manager initialization
pipeline_id = os.getenv('RAG_PIPELINE_ID', f'google_drive_{folder_id or "all"}')
self.sync_manager = create_sync_manager(pipeline_id, 'google_drive')
```

**State Loading** (in `load_config()`):
```python
# Load persistent state from database
state = self.sync_manager.load_pipeline_state()
if state['known_files']:
    self.known_files = state['known_files']
    self.initialized = True  # Skip initial scan if we have state
```

**Synchronization Process** (in `check_for_changes()`):
1. Process regular file changes (additions/modifications)
2. Check for deleted files using existing `check_for_deleted_files()`
3. **NEW**: Perform full synchronization:
   ```python
   # Get all current file IDs from Google Drive
   current_file_ids = set(self.known_files.keys())
   
   # Find and delete orphaned documents
   sync_stats = self.sync_manager.sync_deletions(current_file_ids, delete_document_by_file_id)
   
   # Save updated state
   self.sync_manager.save_pipeline_state(self.known_files, self.last_check_time)
   ```

**Startup Synchronization**:
- On first run after restart, performs full sync to catch any deletions that occurred while offline
- Configurable via `sync_settings.sync_on_startup` in config.json

#### 3.2 Local Files Pipeline (`file_watcher.py`)

**Identical modifications** to Google Drive pipeline:
- Sync manager initialization with `pipeline_id = f'local_files_{watch_directory or "default"}'`
- State loading from database on startup
- Full synchronization in `check_for_changes()`
- Persistent state saving after each check cycle

### 4. Configuration Options

Added to both `config.json` files:
```json
"sync_settings": {
    "enable_orphan_deletion": true,      // Enable/disable orphan cleanup
    "sync_on_startup": true,             // Run sync on pipeline startup
    "sync_interval_checks": 5,           // How often to run full sync
    "deletion_grace_period_seconds": 0   // Delay before deleting (future feature)
}
```

### 5. Database Operations Flow

#### 5.1 Deletion Detection Process

1. **Known Files Tracking**:
   - Each pipeline maintains `known_files` dictionary in memory
   - Maps file_id → metadata (modifiedTime, etc.)
   - Persisted to `rag_pipeline_state` table after each check

2. **Orphan Detection**:
   ```
   Orphaned Documents = Documents in Supabase - Files in Source
   ```
   - Query all document file_ids from Supabase
   - Compare with current known_files from source
   - Difference = orphaned documents to delete

3. **Deletion Execution**:
   - Calls `delete_document_by_file_id()` for each orphan
   - Deletes from:
     - `documents` table (all chunks)
     - `document_rows` table (tabular data)
     - `document_metadata` table (file metadata)

#### 5.2 State Persistence Flow

```
Pipeline Start → Load State from DB → Initial Sync (if enabled)
       ↓
Regular Check → Detect Changes → Update known_files
       ↓
Save State to DB → Sync Orphans → Delete from Supabase
```

### 6. Key Features

1. **Persistent State**: Survives pipeline restarts
2. **Automatic Cleanup**: Removes orphaned documents automatically
3. **Configurable**: Behavior controlled via config.json
4. **Efficient**: Batch operations for large file sets
5. **Logging**: Detailed logs with [COMPONENT-FUNCTION] format
6. **Statistics**: Tracks orphaned_deleted count in check stats

### 7. Integration Points

#### 7.1 `db_handler.py` Additions
- `create_sync_manager()`: Factory function for sync managers
- `perform_full_sync()`: Convenience function for manual sync

#### 7.2 Supabase MCP Integration
- Uses existing Supabase client from db_handler
- Leverages service role key for RLS bypass
- Direct SQL operations via Supabase client

### 8. Testing & Validation

To test the synchronization:
1. Add files to Google Drive/Local directory
2. Let pipeline process them (creates Supabase records)
3. Delete files from source while pipeline is running
4. Observe immediate deletion from Supabase
5. Delete files while pipeline is stopped
6. Restart pipeline and observe orphan cleanup on startup

### 9. Monitoring

Log entries to watch:
- `[SYNC_MANAGER-LOAD_STATE]`: State loading from database
- `[SYNC_MANAGER-SAVE_STATE]`: State persistence
- `[SYNC_MANAGER-ORPHANED]`: Orphan detection results
- `[SYNC_MANAGER-DELETE]`: Individual deletion operations
- `[DRIVE_WATCHER-SYNC]`: Google Drive sync statistics
- `[FILE_WATCHER-SYNC]`: Local Files sync statistics

### 10. Future Enhancements

1. **Grace Period**: Implement `deletion_grace_period_seconds` to delay deletions
2. **Soft Delete**: Mark as deleted before permanent removal
3. **Audit Trail**: Track all sync operations in separate table
4. **Conflict Resolution**: Handle file moves vs deletions
5. **Performance**: Optimize for very large file sets (>10k files)