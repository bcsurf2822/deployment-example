# MCP (Model Context Protocol) Support Architecture

**Date:** August 29, 2025  
**Status:** Active - Python MCP Server Successfully Connected

## Overview

This document outlines the MCP integration architecture for the Agent API system. We have successfully implemented a dynamic MCP server management system that allows the AI agent to execute Python code and integrate with external tools through the Model Context Protocol.

## Current Architecture

### Core Components

#### 1. MCP Manager (`agent_api/mcp_manager.py`)
The central orchestrator for all MCP server lifecycle management.

**Key Features:**
- Dynamic server registration/unregistration
- Health checking and auto-recovery
- Multiple transport support (stdio, SSE, HTTP)
- Connection pooling and retry logic
- Process management for subprocess-based servers

**Key Classes:**
- `MCPManager`: Main manager class
- `MCPServerConfig`: Configuration dataclass
- `TransportType`: Enum for transport types (stdio, sse, http)
- `ServerStatus`: Connection status tracking

**Transport Support:**
- **stdio**: Direct stdin/stdout communication (currently used)
- **sse**: Server-sent events over HTTP
- **http**: RESTful HTTP communication

#### 2. Configuration (`agent_api/mcp_config.json`)
JSON configuration file that defines available MCP servers.

**Current Configuration:**
```json
{
  "servers": [
    {
      "name": "python-executor",
      "transport": "stdio", 
      "enabled": true,
      "auto_start": true,
      "command": "deno",
      "args": ["run", "-N", "-R=node_modules", "-W=node_modules", "--node-modules-dir=auto", "jsr:@pydantic/mcp-run-python", "stdio"],
      "retry_attempts": 3,
      "retry_delay": 3,
      "health_check_interval": 30,
      "timeout": 10
    }
  ]
}
```

#### 3. Docker Integration (`agent_api/Dockerfile.mcp`)
Enhanced Dockerfile that includes both Deno and Node.js runtimes for MCP server support.

**Runtime Support:**
- **Python 3.11**: Main application runtime
- **Deno**: For Pydantic AI MCP servers
- **Node.js 20.x**: For Node.js-based MCP servers (ready for future use)

#### 4. Container Orchestration (`docker-compose.dev.yml`)
Development configuration with MCP support enabled.

**Key Configuration:**
- Agent API runs with MCP manager
- Volume mounts for hot reload
- Port 8001 exposed for API access
- No additional ports needed for stdio transport

## Current Implementation Status

###  Successfully Implemented
- **Python Code Execution**: Via Pydantic AI MCP Python server
- **stdio Transport**: Reliable stdin/stdout communication
- **Process Management**: Automatic startup/shutdown of MCP servers
- **Health Monitoring**: Background health checks and auto-restart
- **Docker Integration**: Containerized deployment with all dependencies

### =' Architecture Decisions Made

#### Transport Choice: stdio vs SSE
**Decision**: Use stdio transport for reliability
**Reasoning**: 
- SSE transport had network connectivity issues in containerized environment
- stdio provides direct process communication without network dependencies
- More reliable in Docker containers with process isolation

#### Process Management
**Decision**: Subprocess management within the MCP manager
**Reasoning**:
- Better control over MCP server lifecycle
- Integrated error handling and restart logic
- Simplified deployment without external process managers

## API Endpoints

### MCP Server Management
- `GET /api/mcp/servers` - List all MCP servers and their status
- `POST /api/mcp/servers/{server_name}/restart` - Restart specific server
- `POST /api/mcp/servers` - Add new MCP server (dynamic registration)

### Example Response
```json
{
  "servers": [
    {
      "name": "python-executor",
      "transport": "stdio", 
      "status": "connected",
      "enabled": true,
      "error_count": 0,
      "last_health_check": null,
      "connected": true
    }
  ]
}
```

## Testing the Implementation

### Python Code Execution Tests
Users can test the MCP integration with these queries:

```
Can you run this Python code: print("Hello from MCP!")
```

```
Calculate 123 * 456 using Python
```

```
Create a list of squares from 1 to 10 using Python
```

## Adding New MCP Servers

### Step-by-Step Process

#### 1. Update Configuration
Add new server entry to `agent_api/mcp_config.json`:

```json
{
  "name": "new-mcp-server",
  "transport": "stdio",
  "enabled": true,
  "auto_start": true,
  "command": "node",
  "args": ["/path/to/server.js"],
  "retry_attempts": 3,
  "retry_delay": 3,
  "health_check_interval": 30,
  "timeout": 10
}
```

#### 2. Runtime Dependencies
Ensure required runtime is available in `Dockerfile.mcp`:
- Deno: Already installed
- Node.js: Already installed  
- Python: Available as base image
- Others: Add to Dockerfile as needed

#### 3. Volume Mounting (if needed)
For external MCP servers, add volume mounts to `docker-compose.dev.yml`:

```yaml
volumes:
  - ./agent_api:/app
  - agent_venv:/app/venv
  - /path/to/external/mcp:/app/mcp/external-server
```

#### 4. Container Restart
Restart the agent API container to pick up changes:
```bash
docker restart pydantic-agent-agent-api-dev-1
```

### Transport Types

#### stdio (Recommended)
- **Use Case**: Most MCP servers
- **Pros**: Reliable, no network dependencies, good for containers
- **Cons**: Process-bound, requires subprocess management
- **Configuration**: `command` and `args` fields

#### SSE (Server-Sent Events)
- **Use Case**: Web-based MCP servers
- **Pros**: HTTP-based, can be external services
- **Cons**: Network dependencies, firewall/proxy considerations
- **Configuration**: `url` field pointing to SSE endpoint

#### HTTP (RESTful)
- **Use Case**: REST API-based MCP servers
- **Pros**: Standard HTTP, cacheable, stateless
- **Cons**: Less real-time than SSE, request/response overhead
- **Configuration**: `url` field pointing to HTTP endpoint

## Logging and Monitoring

### Log Format
All MCP-related logs use the format: `[MCP-MANAGER-function] description`

### Key Log Messages
- `[MCP-MANAGER-initialize]`: Manager startup
- `[MCP-MANAGER-start_server]`: Server startup attempts
- `[MCP-MANAGER-_create_connection]`: Connection establishment
- `[MCP-MANAGER-_health_check_loop]`: Health monitoring

### Monitoring Commands
```bash
# Check MCP server status
curl -s http://localhost:8001/api/mcp/servers

# View MCP logs
docker logs pydantic-agent-agent-api-dev-1 | grep MCP

# Restart specific MCP server
curl -X POST http://localhost:8001/api/mcp/servers/python-executor/restart
```

## Future Enhancements

### Planned Improvements
1. **Dynamic Configuration Updates**: Hot-reload of MCP config without container restart
2. **MCP Server Marketplace**: Registry of available MCP servers
3. **Performance Monitoring**: Metrics for MCP server response times
4. **Load Balancing**: Multiple instances of same MCP server type
5. **Security Hardening**: Sandboxing and permission controls

### Additional MCP Servers to Consider
- **File System MCP**: File operations and directory management
- **Database MCP**: Direct database query capabilities  
- **Web Scraping MCP**: Web content extraction
- **API Integration MCP**: Third-party service connectors
- **SharePoint MCP**: Document management (attempted, ready for future integration)

## Troubleshooting

### Common Issues

#### Server Status "error"
**Symptoms**: MCP server shows error status
**Solutions**: 
1. Check if required runtime is installed
2. Verify command/args configuration
3. Check Docker container logs for subprocess errors
4. Ensure file paths are accessible within container

#### Process Not Starting
**Symptoms**: MCP manager reports "Process started" but no connection
**Solutions**:
1. Test MCP command manually inside container
2. Check for port conflicts (if using SSE/HTTP)
3. Verify file permissions and paths
4. Increase startup wait time in configuration

#### Connection Timeouts
**Symptoms**: Connection attempts fail with timeouts
**Solutions**:
1. Increase `timeout` and `retry_delay` in config
2. Check network connectivity for SSE/HTTP transports
3. Verify MCP server is properly responding to health checks

### Debug Commands
```bash
# Test MCP server manually in container
docker exec pydantic-agent-agent-api-dev-1 deno run [args...]

# Check running processes
docker exec pydantic-agent-agent-api-dev-1 ps aux

# Verify file mounts
docker exec pydantic-agent-agent-api-dev-1 ls -la /app/mcp/
```

## Conclusion

The MCP integration provides a robust foundation for extending the AI agent with external tool capabilities. The current Python execution capability demonstrates successful implementation, and the architecture is designed to easily accommodate additional MCP servers as needed.

The stdio transport pattern has proven reliable and should be the preferred approach for new MCP server integrations unless specific requirements dictate otherwise.