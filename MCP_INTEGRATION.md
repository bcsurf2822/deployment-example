# MCP Integration Guide

This document explains the new MCP (Model Context Protocol) integration that provides dynamic server management and code execution capabilities.

## Overview

The MCP integration includes:

- **Dynamic MCP Server Management**: Add, remove, start, stop, and monitor MCP servers at runtime
- **Automatic Server Startup**: MCP servers start automatically with the application
- **Health Monitoring**: Continuous health checks with auto-recovery
- **Multiple Transport Types**: Support for SSE, Stdio, and HTTP transports
- **Configuration Management**: JSON-based configuration with environment variable overrides
- **API Management**: REST endpoints to manage MCP servers dynamically

## Architecture

### Key Components

1. **MCPManager**: Central manager for all MCP server lifecycle operations
2. **MCPServerConfig**: Configuration dataclass for individual servers
3. **Agent Integration**: Dynamic toolset injection into Pydantic AI agent
4. **API Endpoints**: RESTful management interface
5. **Health Monitoring**: Continuous server health checks

### Files Created/Modified

- `mcp_manager.py` - Core MCP manager implementation
- `mcp_config.json` - Default MCP server configuration
- `agent.py` - Updated to use dynamic MCP toolsets
- `dependencies.py` - Enhanced with MCP manager integration  
- `agent_api.py` - Added MCP management endpoints
- `Dockerfile.mcp` - MCP-enabled Docker configuration
- `docker-compose.yml` & `docker-compose.dev.yml` - Updated for MCP support

## Default Configuration

The system comes with a default Python code executor MCP server:

```json
{
  "servers": [
    {
      "name": "python-executor",
      "transport": "sse",
      "enabled": true,
      "auto_start": true,
      "url": "http://localhost:3001/sse",
      "process_command": "deno",
      "process_args": [
        "run", "-N", "-R=node_modules", "-W=node_modules",
        "--node-modules-dir=auto", "jsr:@pydantic/mcp-run-python",
        "sse", "--port", "3001"
      ],
      "retry_attempts": 5,
      "retry_delay": 3,
      "health_check_interval": 30
    }
  ]
}
```

## API Endpoints

### List MCP Servers
```
GET /api/mcp/servers
```
Returns all configured servers with their status.

### Add MCP Server
```
POST /api/mcp/servers
Content-Type: application/json

{
  "name": "my-server",
  "transport": "sse",
  "enabled": true,
  "url": "http://localhost:3002/sse"
}
```

### Remove MCP Server
```
DELETE /api/mcp/servers/{server_name}
```

### Server Operations
```
POST /api/mcp/servers/{server_name}/start
POST /api/mcp/servers/{server_name}/stop
POST /api/mcp/servers/{server_name}/restart
```

### Server Health
```
GET /api/mcp/servers/{server_name}/health
```

## Usage Examples

### Check MCP Server Status
```bash
curl http://localhost:8001/api/mcp/servers
```

### Add a New MCP Server
```bash
curl -X POST http://localhost:8001/api/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-search",
    "transport": "sse", 
    "enabled": true,
    "auto_start": true,
    "url": "http://localhost:3003/sse"
  }'
```

### Restart a Server
```bash
curl -X POST http://localhost:8001/api/mcp/servers/python-executor/restart
```

## Docker Deployment

### Development Mode
```bash
python deploy.py --mode dev --with-rag
```

### Production Mode
```bash
python deploy.py --mode prod --with-rag
```

The new MCP-enabled containers:
- Use `Dockerfile.mcp` instead of supervisord
- Handle MCP server process management in Python
- Include health checks for MCP servers
- Support hot reload in development mode

## Health Monitoring

The `/health` endpoint now includes MCP server status:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": { ... },
  "mcp_servers": [
    {
      "name": "python-executor",
      "transport": "sse",
      "status": "connected",
      "enabled": true,
      "error_count": 0,
      "connected": true
    }
  ]
}
```

Status values:
- `disconnected` - Server not connected
- `connecting` - Connection in progress
- `connected` - Server healthy and ready
- `error` - Server has errors
- `unhealthy` - Server failing health checks

## Configuration Options

### Server Configuration Fields

- `name` - Unique server identifier
- `transport` - Transport type (sse, stdio, http)
- `enabled` - Whether server is enabled
- `auto_start` - Start automatically with application
- `url` - Server URL for SSE/HTTP transports
- `command` - Command for stdio transport  
- `args` - Command arguments
- `tool_prefix` - Prefix for tool names to avoid conflicts
- `retry_attempts` - Number of connection retry attempts
- `retry_delay` - Delay between retries (seconds)
- `health_check_interval` - Health check frequency (seconds)
- `timeout` - Connection timeout (seconds)
- `process_command` - Command to start server process
- `process_args` - Process command arguments
- `process_env` - Environment variables for process

### Environment Variables

All configuration values can be overridden with environment variables using the pattern:
`MCP_{SERVER_NAME}_{FIELD_NAME}`

Example:
```bash
MCP_PYTHON_EXECUTOR_ENABLED=false
MCP_PYTHON_EXECUTOR_URL=http://localhost:3005/sse
```

## Troubleshooting

### Check MCP Server Logs
```bash
# Docker logs
docker logs <container_name>

# Development logs  
python deploy.py --mode dev --logs
```

### Common Issues

1. **Deno not found**: Ensure Deno is installed in the container
2. **Port conflicts**: Check that MCP server ports are available
3. **Connection failures**: Verify server URLs and network connectivity
4. **Process startup failures**: Check process command and arguments

### Debug Mode

Enable debug logging:
```bash
DEBUG_MODE=true python deploy.py --mode dev
```

This provides detailed MCP manager logs for troubleshooting connection issues.

## Future Enhancements

Planned improvements:
- WebSocket transport support
- MCP server templates and marketplace
- Metrics and monitoring dashboard
- Automatic server discovery
- Load balancing for multiple server instances