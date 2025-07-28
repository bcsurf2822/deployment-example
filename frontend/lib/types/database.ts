/**
 * TypeScript interfaces for database models
 * Based on spec/models.md specification
 */

// ============================================================================
// Core Models
// ============================================================================



export interface UserProfile {
  id: string; // UUID
  email: string;
  full_name: string | null;
  is_admin: boolean;
  created_at: string; // ISO timestamp
  updated_at: string; // ISO timestamp
}

export interface Request {
  id: string; // UUID
  user_id: string; // UUID
  timestamp: string | null; // ISO timestamp
  user_query: string;
}

export interface Conversation {
  session_id: string; // VARCHAR primary key
  user_id: string; // UUID
  title: string | null;
  created_at: string | null; // ISO timestamp
  last_message_at: string | null; // ISO timestamp
  is_archived: boolean | null;
  metadata: Record<string, unknown>; // JSONB - currently empty objects
}

export interface FileAttachment {
  fileName: string;
  content: string; // Base64 encoded content / Binary of the file
  mimeType: string; // Application/pdf, image/jpeg, etc.
}

export interface Message {
  id: string; // Changed to string for consistency with UI
  computed_session_user_id: string | null; // UUID computed column
  session_id: string; // VARCHAR
  message: {
    type: 'human' | 'ai';
    content: string;
    files?: FileAttachment[];
  }; // JSONB with structured format
  message_data: string | null;
  created_at: string; // ISO timestamp
}

// ============================================================================
// Document Management Models
// ============================================================================

// Document metadata structure based on actual data
export interface DocumentMetadataFields {
  file_id: string;
  file_url: string;
  mime_type: string;
  file_title: string;
  chunk_index: number;
}

export interface Document {
  id: number; // BIGINT
  content: string | null;
  metadata: DocumentMetadataFields | null; // JSONB with file processing info
  embedding: number[] | null; // Vector type (1536 dimensions for OpenAI embeddings)
}

export interface DocumentMetadata {
  id: string; // TEXT primary key
  title: string | null;
  url: string | null;
  created_at: string | null; // ISO timestamp
  schema: string | null;
}

export interface DocumentRow {
  id: number; // Auto-incrementing integer
  dataset_id: string | null; // TEXT, references document_metadata.id
  row_data: Record<string, unknown> | null; // JSONB - structure unknown, no data exists
}

// ============================================================================
// Frontend-Specific Types
// ============================================================================

export interface CreateConversationData {
  user_id: string;
  title?: string;
  metadata?: Record<string, unknown>;
}

export interface CreateMessageData {
  session_id: string;
  message: {
    type: 'human' | 'ai';
    content: string;
    files?: FileAttachment[];
  };
  message_data?: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface UserProfileUpdate {
  full_name?: string;
  // Note: email and is_admin typically not updatable by users
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// ============================================================================
// Context/State Types for React
// ============================================================================

export interface AuthUser {
  id: string;
  email: string;
  profile: UserProfile | null;
  isLoading: boolean;
}

export interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export interface DocumentState {
  documents: Document[];
  metadata: DocumentMetadata[];
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Utility Types
// ============================================================================

export type SessionIdComponents = {
  userId: string;
  timestamp: string;
};

export type DatabaseTable = 
  | 'user_profiles'
  | 'requests'
  | 'conversations'
  | 'messages'
  | 'documents'
  | 'document_metadata'
  | 'document_rows';

export type UserRole = 'user' | 'admin';

// Helper type for RLS context
export interface RLSContext {
  userId: string;
  isAdmin: boolean;
}