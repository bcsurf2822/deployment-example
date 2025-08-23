# RAG Pipeline Dependencies

## Required Python Packages

### Primary Dependency: python-socketio

```bash
pip install "python-socketio[asyncio]>=5.10.0"
```

**Why this package:**
- Official Socket.IO implementation for Python
- Full asyncio support for non-blocking operations
- Compatible with existing HTTP server architecture
- Supports namespaces, rooms, and authentication

### Additional Dependencies

```bash
pip install "aiofiles>=23.0.0"  # For async file operations if needed
```

## Version Compatibility

### Python Version Requirements
- **Minimum**: Python 3.8
- **Recommended**: Python 3.10+
- **Tested**: Python 3.11

### Package Compatibility Matrix

| Package | Version | Notes |
|---------|---------|-------|
| python-socketio | >=5.10.0 | AsyncIO support required |
| aiohttp | >=3.8.0 | For ASGI integration if needed |
| uvloop | >=0.17.0 | Optional: Better asyncio performance |

## Installation in Different Environments

### Local Development
```bash
cd rag_pipeline
pip install "python-socketio[asyncio]>=5.10.0"
```

### Docker Environment
Add to `requirements.txt`:
```text
python-socketio[asyncio]>=5.10.0
```

### Poetry (if using)
```bash
poetry add "python-socketio[asyncio]"
```

## Import Verification

Test the installation with:
```python
import socketio
import asyncio

# Verify AsyncServer is available
server = socketio.AsyncServer()
print(f"Socket.IO version: {socketio.__version__}")
print("AsyncServer imported successfully")
```

## Common Installation Issues

### 1. Missing asyncio extras
**Error**: `ImportError: No module named 'socketio.async_server'`
**Solution**: Install with `[asyncio]` extra: `pip install "python-socketio[asyncio]"`

### 2. Version conflicts
**Error**: Dependency conflicts with existing packages
**Solution**: Use virtual environment or update conflicting packages

### 3. C compiler issues (on some systems)
**Error**: `error: Microsoft Visual C++ 14.0 is required`
**Solution**: Install build tools or use pre-compiled wheels

## Performance Optimization (Optional)

For better asyncio performance:
```bash
pip install uvloop  # Unix systems only
```

Enable in code:
```python
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
```

## Dependency Updates

To update to latest compatible version:
```bash
pip install --upgrade "python-socketio[asyncio]"
```

Check for security updates regularly as Socket.IO is a network-facing component.