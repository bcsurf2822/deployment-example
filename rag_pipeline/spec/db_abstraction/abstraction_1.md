# RAG Pipeline Database Abstraction Strategy

## Architecture Options

### 1. Same RAG Pipeline, Multiple Backends
Keep the existing `rag_pipeline/` folder but add abstraction layers:
- Create a `rag_pipeline/common/vector_stores/` directory
- Implement adapters for Supabase/pgvector, MongoDB Atlas, Pinecone, etc.
- Use environment variables to select which backend(s) to use
- This is cleaner and avoids duplication

### 2. Port Considerations
- MongoDB itself doesn't need a new port - you'd connect to MongoDB Atlas (cloud) or a local MongoDB instance
- Port 8003 (Google Drive pipeline) can stay the same - it's just changing where vectors are stored
- The processing logic remains identical, only the storage backend changes

## Recommended Approach

```
rag_pipeline/
├── common/
│   ├── vector_stores/
│   │   ├── base.py          # Abstract interface
│   │   ├── supabase.py      # Current implementation
│   │   ├── mongodb.py       # MongoDB Atlas Vector Search
│   │   └── pinecone.py      # Optional: other providers
│   └── db_handler.py        # Modified to use vector_stores
```

## Configuration Strategy
- Use `VECTOR_STORE_TYPE` env variable: "supabase", "mongodb", "multi"
- For comparison mode ("multi"), write to multiple stores and query from both
- Keep the same REST API endpoints but add optional `?store=mongodb` query params

This way you maintain one pipeline codebase, avoid port conflicts, and can easily A/B test different vector stores.

---

## Abstraction Implementation Plan

### Question
> Ok just out of curiosity since we already have supabase going could we start by abstracting that one while maintaining functionality?

### Answer
Yes, absolutely! That's a perfect approach - refactor the existing Supabase implementation into an abstracted pattern while maintaining full functionality. This way you can:

1. **Create the abstraction layer** without breaking anything
2. **Extract the Supabase-specific code** into an adapter class
3. **Test that everything still works** before adding new backends

### Refactoring Strategy

```
rag_pipeline/common/
├── vector_stores/
│   ├── __init__.py
│   ├── base.py           # Abstract base class/interface
│   └── supabase.py       # Move Supabase-specific logic here
└── db_handler.py          # Becomes a thin wrapper that uses vector_stores
```

### Key Steps
1. Define the interface in `base.py` (methods like `store_embeddings()`, `search_similar()`, `delete_documents()`)
2. Move all Supabase client code from `db_handler.py` to `vector_stores/supabase.py`
3. Update `db_handler.py` to instantiate the appropriate vector store based on config
4. Keep the same public API so Google_Drive and Local_Files don't need changes

This refactoring maintains 100% backward compatibility - the existing pipeline continues working exactly as before, but now you have a clean interface to implement MongoDB or other stores against.