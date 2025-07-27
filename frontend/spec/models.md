# Database Models Specification

This document describes the database models and their relationships for the pydantic-demo chat application with document management capabilities.

## Core Models

### User Profiles
**Table:** `user_profiles`  
**Purpose:** User management with admin capabilities linked to Supabase auth

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Primary key, references auth.users | NOT NULL, PK, FK to auth.users |
| email | TEXT | User email address | NOT NULL |
| full_name | TEXT | User's full name | NULLABLE |
| is_admin | BOOLEAN | Admin privileges flag | DEFAULT false |
| created_at | TIMESTAMPTZ | Account creation timestamp | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMPTZ | Last profile update | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**Security:** Row Level Security (RLS) enabled - users can only access their own profiles, admins have full access

### Requests
**Table:** `requests`  
**Purpose:** User query tracking and logging

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Primary key | NOT NULL, PK |
| user_id | UUID | References user_profiles.id | NOT NULL, FK to user_profiles |
| timestamp | TIMESTAMPTZ | Query timestamp | DEFAULT CURRENT_TIMESTAMP |
| user_query | TEXT | The user's query/request | NOT NULL |

**Security:** RLS enabled - users can only view their own requests, admins have full access

### Conversations
**Table:** `conversations`  
**Purpose:** Chat session management with metadata support

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| session_id | VARCHAR | Primary key, custom session identifier | NOT NULL, PK, UNIQUE |
| user_id | UUID | References user_profiles.id | NOT NULL, FK to user_profiles |
| title | VARCHAR | Auto-generated conversation title | NULLABLE |
| created_at | TIMESTAMPTZ | Conversation start time | DEFAULT now() |
| last_message_at | TIMESTAMPTZ | Last activity timestamp | DEFAULT now() |
| is_archived | BOOLEAN | Archive status | DEFAULT false |
| metadata | JSONB | Additional conversation data | DEFAULT '{}' |

**Security:** RLS enabled - users can only access their own conversations, admins have full access

### Messages
**Table:** `messages`  
**Purpose:** Individual chat messages with N8N workflow integration

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | INTEGER | Auto-incrementing primary key | IDENTITY, PK |
| computed_session_user_id | UUID | Computed from session_id for access control | GENERATED, STORED |
| session_id | VARCHAR | References conversations.session_id | NOT NULL, FK to conversations |
| message | JSONB | Message content and metadata | NOT NULL |
| message_data | TEXT | Additional message data | NULLABLE |
| created_at | TIMESTAMPTZ | Message timestamp | DEFAULT now() |

**Key Pattern:** Session ID format: `{user_id}~{timestamp}` enables computed column parsing for secure access control

**Security:** RLS enabled - access controlled via computed_session_user_id

## Document Management Models

### Documents
**Table:** `documents`  
**Purpose:** Vector-enabled document storage with embeddings

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | BIGINT | Auto-incrementing primary key | SERIAL, PK |
| content | TEXT | Document text content | NULLABLE |
| metadata | JSONB | Document metadata | NULLABLE |
| embedding | VECTOR | Vector embedding for similarity search | NULLABLE |

**Security:** No RLS - appears to be shared document store

### Document Metadata
**Table:** `document_metadata`  
**Purpose:** Document dataset organization and schema definition

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | TEXT | Dataset identifier | NOT NULL, PK |
| title | TEXT | Dataset title | NULLABLE |
| url | TEXT | Source URL | NULLABLE |
| created_at | TIMESTAMP | Creation timestamp | DEFAULT now() |
| schema | TEXT | Dataset schema definition | NULLABLE |

### Document Rows
**Table:** `document_rows`  
**Purpose:** Structured document data storage

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | INTEGER | Auto-incrementing primary key | SERIAL, PK |
| dataset_id | TEXT | References document_metadata.id | FK to document_metadata |
| row_data | JSONB | Structured row data | NULLABLE |

## Relationships

```
user_profiles (1) ──> (N) requests
user_profiles (1) ──> (N) conversations
conversations (1) ──> (N) messages
document_metadata (1) ──> (N) document_rows
auth.users (1) ──> (1) user_profiles
```

## Security Model

**Row Level Security (RLS):**
- **user_profiles, requests, conversations, messages:** Users can only access their own data
- **Admin Override:** Admin users have full read access to all user data
- **No Delete Policy:** Delete operations are completely denied for all users
- **documents, document_metadata, document_rows:** No RLS - shared access

## Key Design Patterns

1. **Session-Based Architecture:** Conversations use custom session IDs with embedded user information
2. **JSONB Flexibility:** Messages and metadata use JSONB for flexible schema evolution
3. **Computed Columns:** Automatic session parsing for secure access control
4. **Audit Trail:** Comprehensive timestamping on all user actions
5. **Vector Search Ready:** Document embeddings support semantic search capabilities
6. **N8N Integration:** Message structure designed for workflow automation compatibility

## Frontend Model Requirements

Based on the database schema, the frontend will need TypeScript interfaces for:

1. **UserProfile** - User management and admin checks
2. **Request** - Query tracking
3. **Conversation** - Chat session management
4. **Message** - Chat message handling
5. **Document** - Vector document storage
6. **DocumentMetadata** - Dataset organization
7. **DocumentRow** - Structured document data

Each interface should include proper typing for JSONB fields and timestamp handling.