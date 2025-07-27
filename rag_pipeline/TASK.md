# RAG Pipeline Implementation Tasks

## Overview
Implementing improvements to the RAG pipeline for both Google Drive and Local Files, with focus on single-run mode, service account authentication, and database state management.

## Phase 1: Core Single-Run Implementation 🚀 [HIGH PRIORITY]

### Google Drive Pipeline
- [x] **Task 1.1**: Extract `check_for_changes()` method in Google Drive Watcher
  - Extract core logic from `watch_for_changes()` infinite loop
  - Create new method that returns statistics
  - Maintain backward compatibility

- [x] **Task 1.2**: Update Google Drive main.py for single-run mode
  - Add --single-run flag
  - Implement proper exit codes
  - Add statistics output

### Local Files Pipeline
- [x] **Task 1.3**: Extract `check_for_changes()` method in Local Files Watcher
  - Mirror implementation from Google Drive watcher
  - Return same statistics format
  
- [x] **Task 1.4**: Create comprehensive Local Files implementation
  - Implement file watching for `/Users/benjamincorbett/Desktop/local_rag_drive`
  - Add proper file processing logic
  - Integrate with existing database handler

- [x] **Task 1.5**: Create main.py for Local Files
  - Support both continuous and single-run modes
  - Add command-line arguments
  - Implement proper error handling

### Docker Integration
- [ ] **Task 1.6**: Create/Update Docker Entrypoint
  - Implement proper single-run mode
  - Add exit codes (0=success, 1=retry, 2=config error, 3=auth error)
  - Add statistics logging

## Phase 2: Google Drive Service Account Authentication 🔐 [HIGH PRIORITY]

- [ ] **Task 2.1**: Implement Service Account Authentication
  - Add support for `GOOGLE_DRIVE_CREDENTIALS_JSON` env var
  - Maintain backward compatibility with file-based credentials
  - Update `authenticate_google_drive()` method

- [ ] **Task 2.2**: Update Google Drive API Client
  - Modify to use service account when available
  - Remove interactive OAuth2 flow for service accounts
  - Add proper error handling

- [ ] **Task 2.3**: Add Service Account Tests
  - Test service account authentication path
  - Test fallback to file-based auth

## Phase 3: Database State Management 💾 [MEDIUM PRIORITY]

- [ ] **Task 3.1**: Create Database Schema
  - Create `rag_pipeline_state` table schema
  - Add SQL migration script

- [ ] **Task 3.2**: Implement State Manager
  - Create `StateManager` class
  - Methods for load/save state
  - Handle `RAG_PIPELINE_ID` env var

- [ ] **Task 3.3**: Update Watchers for Database State
  - Integrate StateManager in both watchers
  - Update state persistence logic

- [ ] **Task 3.4**: Environment Variable Configuration
  - Add env var parsing for config overrides
  - Support all new environment variables

## Phase 4: Testing & Validation ✅ [HIGH PRIORITY]

- [ ] **Task 4.1**: Run and fix all existing tests
- [ ] **Task 4.2**: Add new integration tests
- [ ] **Task 4.3**: Manual testing of both modes
- [ ] **Task 4.4**: Docker container testing

## Current Status

**Starting Point**: Examining existing implementation
**Next Steps**: 
1. Review current Local Files implementation
2. Extract check_for_changes() methods
3. Implement comprehensive Local Files RAG pipeline

## Notes
- Local RAG folder: `/Users/benjamincorbett/Desktop/local_rag_drive`
- Must maintain 100% backward compatibility
- Focus on production-ready implementation