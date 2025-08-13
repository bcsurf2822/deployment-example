# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Development server with Turbopack hot reload
npm run dev

# Production build
npm run build

# Start production server
npm run start

# ESLint checking
npm run lint
```

## Architecture Overview

This is a Next.js 15 frontend application for an AI chat assistant with RAG (Retrieval-Augmented Generation) capabilities and web search integration. The application uses React 19, TypeScript 5 with strict mode, and Tailwind CSS 4 for styling.

### Core Stack
- **Framework**: Next.js 15 with App Router
- **UI**: React 19 with TypeScript 5 (strict mode)
- **Styling**: Tailwind CSS 4 with shadcn/ui components
- **Auth**: Supabase Auth with SSR support
- **Database**: PostgreSQL via Supabase with pgvector for embeddings
- **Real-time**: Server-Sent Events for streaming chat responses

### Project Structure

**API Routes** (`app/api/`)
- `/chat/route.ts`: Handles streaming chat requests to Pydantic agent backend
- `/documents/route.ts`: Fetches RAG document metadata
- `/google-drive/upload/route.ts`: Google Drive file upload endpoint

**Pages** (`app/`)
- `/chat`: Main chat interface with conversation management
- `/documents`: RAG document viewer
- `/rag-pipelines`: RAG pipeline management
- `/settings`: User settings
- `/auth/login`: Authentication with email/password and Google OAuth

**Components** (`components/`)
- Chat components: `ChatLayout`, `ChatInput`, `MessageContainer`, `ConversationsSidebar`
- Document components: `DocumentContainer`, `DocumentList`, `DocumentItem`
- Auth components: `AuthProvider`, `LoginForm`, `AuthContainer`
- UI components: shadcn/ui components with custom styling

### Key Patterns

**Authentication Flow**
- Middleware handles session refresh (`middleware.ts`)
- Server components use `createClient()` from `lib/supabase/server.ts`
- Client components use `createClient()` from `lib/supabase/client.ts`
- Auth state managed via `AuthProvider` context

**Chat Implementation**
- Session IDs format: `{user_id}~{timestamp}` for message access control
- Streaming responses handled via Server-Sent Events
- Messages stored as JSONB with computed session parsing
- Real-time message updates during streaming

**TypeScript Conventions**
- Strict mode enabled
- Path alias `@/*` maps to root directory
- Database types in `lib/types/database.ts`
- Component types in `lib/types/index.ts`

### Environment Variables

Required:
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
NEXT_PUBLIC_PYDANTIC_AGENT_API_URL
```

Optional:
```
NEXT_PUBLIC_LANGFUSE_HOST_WITH_PROJECT  # For trace viewing
NEXT_PUBLIC_SITE_URL                    # For OAuth redirects
```

### Database Schema

The application expects these tables with RLS enabled:
- `user_profiles`: User management with admin flags
- `conversations`: Chat sessions with auto-generated titles
- `messages`: JSONB message storage with session parsing
- `document_metadata`: RAG document metadata
- `document_rows`: Tabular data from spreadsheets
- `documents`: Vector embeddings for RAG

### Development Guidelines

**Next.js 15 Requirements**
- Always await runtime APIs: `await cookies()`, `await headers()`, `await params`, `await searchParams`
- Prefer React Server Components, minimize `'use client'` directives
- Use `useActionState` instead of deprecated `useFormState`

**Component Structure**
- Order: exports → subcomponents → helpers → types
- Event handlers: `handleClick`, `handleSubmit`, etc.
- Boolean props: `isLoading`, `hasError`, etc.
- Directory naming: lowercase with dashes (e.g., `auth-wizard`)

**API Integration**
- Chat API expects: `{ query, session_id, user_id, files? }`
- Responses stream as JSON lines with `{ text: string }` chunks
- Completion signaled by `{ complete: true }`
- Errors returned as `{ error: string }`

### Common Issues

1. **Auth Token Issues**: Ensure `SUPABASE_SERVICE_ROLE_KEY` is set for bypassing RLS
2. **Streaming Not Working**: Check CORS and ensure backend returns proper SSE headers
3. **Session ID Mismatch**: Format must be `{user_id}~{suffix}` for computed columns
4. **Build Errors**: Run `npm run lint` to catch TypeScript issues before build