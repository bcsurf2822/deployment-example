# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Primary Development:**
```bash
npm run dev          # Start development server with Turbopack
npm run build        # Production build
npm run start        # Production server
npm run lint         # ESLint checking
```

**Database Setup:**
SQL files in `/sql/` directory must be run in numerical order:
1. `1_user_profiles.requests.sql` - Core user management
2. `2_user_profiles_requests_rls.sql` - Row Level Security for users/requests  
3. `3_conversations_messages.sql` - Chat conversation system
4. `4_conversations_messages_rls.sql` - RLS for conversations/messages

## Architecture Overview

**Technology Stack:**
- Next.js 15 with App Router
- React 19 with TypeScript 5
- Tailwind CSS 4 for styling
- PostgreSQL with Supabase backend
- UUID-based authentication system

**Database Design:**
Four-table architecture with comprehensive Row Level Security:

- `user_profiles` - User management with admin flags, links to Supabase auth.users
- `requests` - User query tracking with timestamps
- `conversations` - Session-based chat management with auto-generated titles
- `messages` - JSONB message storage with computed session parsing for N8N integration

**Security Model:**
- Users can only access their own data (enforced by RLS)
- Admins have full read access to all data  
- Delete operations are completely denied for all users
- Computed session IDs enable secure message access control

**Key Patterns:**
- Session IDs use format: `{user_id}~{timestamp}` for computed column parsing
- JSONB message storage allows flexible message formats
- Auto-creation triggers for user profiles on auth signup
- Foreign key cascading maintains data integrity

**Current State:**
Frontend is still using default Next.js template. Database schema is production-ready for a multi-user chat application with admin capabilities and N8N workflow integration.

## Development Guidelines

**TypeScript & React Best Practices:**
- Use TypeScript for all code with proper type safety
- Prefer interfaces over types, avoid enums (use const maps)
- Use functional and declarative programming patterns
- Structure components logically: exports, subcomponents, helpers, types
- Prefix event handlers with 'handle' (handleClick, handleSubmit)
- Use descriptive names with auxiliary verbs (isLoading, hasError)

**Next.js 15 Specific Requirements:**
- Always use async versions of runtime APIs:
  ```typescript
  const cookieStore = await cookies()
  const headersList = await headers()
  const params = await props.params
  const searchParams = await props.searchParams
  ```
- Favor React Server Components (RSC) where possible
- Minimize 'use client' directives
- Use `useActionState` instead of deprecated `useFormState`

**Directory Naming:**
- Use lowercase with dashes for directories (components/auth-wizard)

**Documentation Reference:**
If unsure about implementation details, consult the latest Next.js documentation at: https://nextjs.org/docs