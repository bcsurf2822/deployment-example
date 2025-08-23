f"""
MCP Server Manager for dynamic server lifecycle management.

This module provides a centralized manager for MCP servers with support for:
- Multiple transport types (SSE, Stdio, HTTP)
- Dynamic server registration/unregistration
- Health checking and auto-recovery
- Connection pooling and retry logic
"""

import asyncio
import json
import subprocess
import httpx
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import logging

from pydantic_ai.mcp import MCPServerSSE, MCPServerStdio, MCPServerStreamableHTTP
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class TransportType(str, Enum):
    """Supported MCP transport types."""
    SSE = "sse"
    STDIO = "stdio"
    HTTP = "http"


class ServerStatus(str, Enum):
    """MCP server connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    UNHEALTHY = "unhealthy"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    transport: TransportType
    enabled: bool = True
    auto_start: bool = True
    
    # Connection details
    url: Optional[str] = None  # For SSE/HTTP transports
    command: Optional[str] = None  # For stdio transport
    args: Optional[List[str]] = None  # For stdio transport
    
    # Advanced options
    tool_prefix: Optional[str] = None
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds
    health_check_interval: int = 30  # seconds
    timeout: int = 10  # seconds
    
    # Process management (for subprocess-based servers)
    process_command: Optional[str] = None
    process_args: Optional[List[str]] = None
    process_env: Optional[Dict[str, str]] = None
    
    # Runtime state (not persisted)
    _process: Optional[subprocess.Popen] = field(default=None, init=False, repr=False)
    _last_health_check: Optional[datetime] = field(default=None, init=False, repr=False)
    _status: ServerStatus = field(default=ServerStatus.DISCONNECTED, init=False)
    _error_count: int = field(default=0, init=False)
    

class MCPServerConfigModel(BaseModel):
    """Pydantic model for validating MCP server configuration."""
    name: str = Field(..., description="Unique server identifier")
    transport: TransportType = Field(..., description="Transport type")
    enabled: bool = Field(default=True, description="Whether server is enabled")
    auto_start: bool = Field(default=True, description="Auto-start with application")
    
    url: Optional[str] = Field(None, description="Server URL for SSE/HTTP")
    command: Optional[str] = Field(None, description="Command for stdio transport")
    args: Optional[List[str]] = Field(None, description="Arguments for stdio transport")
    
    tool_prefix: Optional[str] = Field(None, description="Prefix for tool names")
    retry_attempts: int = Field(3, ge=0, le=10)
    retry_delay: int = Field(5, ge=1, le=60)
    health_check_interval: int = Field(30, ge=10, le=300)
    timeout: int = Field(10, ge=1, le=60)
    
    process_command: Optional[str] = Field(None, description="Command to start server process")
    process_args: Optional[List[str]] = Field(None, description="Arguments for server process")
    process_env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    
    @model_validator(mode='after')
    def validate_transport_requirements(self):
        """Validate that required fields are present based on transport type."""
        if self.transport in [TransportType.SSE, TransportType.HTTP] and not self.url:
            raise ValueError(f"URL required for {self.transport} transport")
        
        if self.transport == TransportType.STDIO and not self.command:
            raise ValueError("Command required for stdio transport")
        
        return self


class MCPManager:
    """Manager for MCP server lifecycle and connections."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize MCP Manager.
        
        Args:
            config_path: Path to MCP configuration file
        """
        self.servers: Dict[str, MCPServerConfig] = {}
        self.connections: Dict[str, Any] = {}
        self.config_path = config_path or Path("mcp_config.json")
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
        
    async def initialize(self):
        """Initialize the MCP manager and load configuration."""
        print("[MCP-MANAGER-initialize] Initializing MCP Manager")
        
        # Create HTTP client for health checks
        self._http_client = httpx.AsyncClient(timeout=5.0)
        
        # Load configuration
        await self.load_config()
        
        # Start auto-start servers
        for server_name, config in self.servers.items():
            if config.enabled and config.auto_start:
                print(f"[MCP-MANAGER-initialize] Auto-starting server: {server_name}")
                await self.start_server(server_name)
    
    async def shutdown(self):
        """Shutdown all servers and cleanup resources."""
        print("[MCP-MANAGER-shutdown] Shutting down MCP Manager")
        
        # Cancel health check tasks
        for task in self._health_check_tasks.values():
            task.cancel()
        
        # Stop all servers
        for server_name in list(self.servers.keys()):
            await self.stop_server(server_name)
        
        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()
    
    async def load_config(self):
        """Load MCP server configuration from file."""
        if not self.config_path.exists():
            print(f"[MCP-MANAGER-load_config] Config file not found: {self.config_path}")
            await self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            for server_data in config_data.get('servers', []):
                # Validate with Pydantic
                validated = MCPServerConfigModel(**server_data)
                
                # Convert to dataclass
                config = MCPServerConfig(
                    name=validated.name,
                    transport=validated.transport,
                    enabled=validated.enabled,
                    auto_start=validated.auto_start,
                    url=validated.url,
                    command=validated.command,
                    args=validated.args,
                    tool_prefix=validated.tool_prefix,
                    retry_attempts=validated.retry_attempts,
                    retry_delay=validated.retry_delay,
                    health_check_interval=validated.health_check_interval,
                    timeout=validated.timeout,
                    process_command=validated.process_command,
                    process_args=validated.process_args,
                    process_env=validated.process_env
                )
                
                self.servers[config.name] = config
                print(f"[MCP-MANAGER-load_config] Loaded server config: {config.name}")
                
        except Exception as e:
            print(f"[MCP-MANAGER-load_config] Error loading config: {e}")
            await self._create_default_config()
    
    async def _create_default_config(self):
        """Create default MCP configuration."""
        print("[MCP-MANAGER-_create_default_config] Creating default configuration")
        
        # Default Python MCP server configuration
        default_config = {
            "servers": [
                {
                    "name": "python-executor",
                    "transport": "sse",
                    "enabled": True,
                    "auto_start": True,
                    "url": "http://localhost:3001/sse",
                    "process_command": "deno",
                    "process_args": [
                        "run",
                        "-N", "-R=node_modules", "-W=node_modules",
                        "--node-modules-dir=auto",
                        "jsr:@pydantic/mcp-run-python",
                        "sse",
                        "--port", "3001"
                    ],
                    "retry_attempts": 5,
                    "retry_delay": 3,
                    "health_check_interval": 30
                }
            ]
        }
        
        # Save default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        # Load the default config
        await self.load_config()
    
    async def start_server(self, server_name: str) -> bool:
        """
        Start an MCP server.
        
        Args:
            server_name: Name of the server to start
            
        Returns:
            True if successful, False otherwise
        """
        if server_name not in self.servers:
            print(f"[MCP-MANAGER-start_server] Server not found: {server_name}")
            return False
        
        config = self.servers[server_name]
        
        if not config.enabled:
            print(f"[MCP-MANAGER-start_server] Server disabled: {server_name}")
            return False
        
        try:
            # Start subprocess if configured
            if config.process_command:
                await self._start_subprocess(config)
            
            # Create connection based on transport type
            connection = await self._create_connection(config)
            
            if connection:
                self.connections[server_name] = connection
                config._status = ServerStatus.CONNECTED
                config._error_count = 0
                
                # Start health checking
                if server_name not in self._health_check_tasks:
                    self._health_check_tasks[server_name] = asyncio.create_task(
                        self._health_check_loop(server_name)
                    )
                
                print(f"[MCP-MANAGER-start_server] Started server: {server_name}")
                return True
            
        except Exception as e:
            print(f"[MCP-MANAGER-start_server] Error starting {server_name}: {e}")
            config._status = ServerStatus.ERROR
            config._error_count += 1
        
        return False
    
    async def stop_server(self, server_name: str) -> bool:
        """
        Stop an MCP server.
        
        Args:
            server_name: Name of the server to stop
            
        Returns:
            True if successful, False otherwise
        """
        if server_name not in self.servers:
            return False
        
        config = self.servers[server_name]
        
        try:
            # Cancel health check task
            if server_name in self._health_check_tasks:
                self._health_check_tasks[server_name].cancel()
                del self._health_check_tasks[server_name]
            
            # Close connection
            if server_name in self.connections:
                connection = self.connections[server_name]
                if hasattr(connection, '__aexit__'):
                    await connection.__aexit__(None, None, None)
                del self.connections[server_name]
            
            # Stop subprocess
            if config._process:
                config._process.terminate()
                try:
                    config._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    config._process.kill()
                config._process = None
            
            config._status = ServerStatus.DISCONNECTED
            print(f"[MCP-MANAGER-stop_server] Stopped server: {server_name}")
            return True
            
        except Exception as e:
            print(f"[MCP-MANAGER-stop_server] Error stopping {server_name}: {e}")
            return False
    
    async def restart_server(self, server_name: str) -> bool:
        """Restart an MCP server."""
        await self.stop_server(server_name)
        await asyncio.sleep(1)  # Brief pause before restart
        return await self.start_server(server_name)
    
    async def add_server(self, config: MCPServerConfig) -> bool:
        """
        Add a new MCP server dynamically.
        
        Args:
            config: Server configuration
            
        Returns:
            True if successful, False otherwise
        """
        if config.name in self.servers:
            print(f"[MCP-MANAGER-add_server] Server already exists: {config.name}")
            return False
        
        self.servers[config.name] = config
        
        # Save updated configuration
        await self.save_config()
        
        # Start if auto-start is enabled
        if config.enabled and config.auto_start:
            return await self.start_server(config.name)
        
        return True
    
    async def remove_server(self, server_name: str) -> bool:
        """
        Remove an MCP server.
        
        Args:
            server_name: Name of the server to remove
            
        Returns:
            True if successful, False otherwise
        """
        if server_name not in self.servers:
            return False
        
        # Stop the server first
        await self.stop_server(server_name)
        
        # Remove from configuration
        del self.servers[server_name]
        
        # Save updated configuration
        await self.save_config()
        
        return True
    
    async def save_config(self):
        """Save current configuration to file."""
        config_data = {
            "servers": [
                {
                    "name": config.name,
                    "transport": config.transport.value,
                    "enabled": config.enabled,
                    "auto_start": config.auto_start,
                    "url": config.url,
                    "command": config.command,
                    "args": config.args,
                    "tool_prefix": config.tool_prefix,
                    "retry_attempts": config.retry_attempts,
                    "retry_delay": config.retry_delay,
                    "health_check_interval": config.health_check_interval,
                    "timeout": config.timeout,
                    "process_command": config.process_command,
                    "process_args": config.process_args,
                    "process_env": config.process_env
                }
                for config in self.servers.values()
            ]
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_active_toolsets(self) -> List[Any]:
        """Get list of active MCP connections for use as toolsets."""
        return list(self.connections.values())
    
    def get_server_status(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get status information for a server."""
        if server_name not in self.servers:
            return None
        
        config = self.servers[server_name]
        return {
            "name": server_name,
            "transport": config.transport.value,
            "status": config._status.value,
            "enabled": config.enabled,
            "error_count": config._error_count,
            "last_health_check": config._last_health_check.isoformat() if config._last_health_check else None,
            "connected": server_name in self.connections
        }
    
    def get_all_servers_status(self) -> List[Dict[str, Any]]:
        """Get status for all servers."""
        return [self.get_server_status(name) for name in self.servers.keys()]
    
    async def _start_subprocess(self, config: MCPServerConfig):
        """Start a subprocess for the MCP server."""
        if not config.process_command:
            return
        
        if config._process and config._process.poll() is None:
            print(f"[MCP-MANAGER-_start_subprocess] Process already running for {config.name}")
            return
        
        try:
            env = os.environ.copy()
            if config.process_env:
                env.update(config.process_env)
            
            print(f"[MCP-MANAGER-_start_subprocess] Starting process: {config.process_command} {' '.join(config.process_args or [])}")
            
            config._process = subprocess.Popen(
                [config.process_command] + (config.process_args or []),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for process to stabilize
            await asyncio.sleep(2)
            
            if config._process.poll() is not None:
                stderr = config._process.stderr.read() if config._process.stderr else b""
                raise Exception(f"Process exited immediately: {stderr.decode()}")
            
            print(f"[MCP-MANAGER-_start_subprocess] Process started for {config.name}")
            
        except Exception as e:
            print(f"[MCP-MANAGER-_start_subprocess] Failed to start process for {config.name}: {e}")
            raise
    
    async def _create_connection(self, config: MCPServerConfig) -> Optional[Any]:
        """Create MCP connection based on transport type."""
        for attempt in range(config.retry_attempts):
            try:
                if config.transport == TransportType.SSE:
                    if not config.url:
                        raise ValueError("URL required for SSE transport")
                    
                    # Test connection first
                    if self._http_client:
                        try:
                            response = await self._http_client.get(config.url.replace('/sse', ''))
                            if response.status_code != 200:
                                raise Exception(f"Server not ready: {response.status_code}")
                        except Exception as e:
                            if attempt < config.retry_attempts - 1:
                                print(f"[MCP-MANAGER-_create_connection] Connection attempt {attempt + 1} failed: {e}")
                                await asyncio.sleep(config.retry_delay)
                                continue
                            raise
                    
                    return MCPServerSSE(url=config.url, tool_prefix=config.tool_prefix)
                
                elif config.transport == TransportType.STDIO:
                    if not config.command:
                        raise ValueError("Command required for stdio transport")
                    
                    return MCPServerStdio(
                        config.command,
                        args=config.args,
                        tool_prefix=config.tool_prefix
                    )
                
                elif config.transport == TransportType.HTTP:
                    if not config.url:
                        raise ValueError("URL required for HTTP transport")
                    
                    return MCPServerStreamableHTTP(
                        url=config.url,
                        tool_prefix=config.tool_prefix
                    )
                
                else:
                    raise ValueError(f"Unsupported transport: {config.transport}")
                    
            except Exception as e:
                if attempt < config.retry_attempts - 1:
                    print(f"[MCP-MANAGER-_create_connection] Retry {attempt + 1}/{config.retry_attempts} for {config.name}: {e}")
                    await asyncio.sleep(config.retry_delay)
                else:
                    print(f"[MCP-MANAGER-_create_connection] Failed to create connection for {config.name}: {e}")
                    raise
        
        return None
    
    async def _health_check_loop(self, server_name: str):
        """Background task to perform health checks."""
        config = self.servers[server_name]
        
        while True:
            try:
                await asyncio.sleep(config.health_check_interval)
                
                # Check subprocess if applicable
                if config._process and config._process.poll() is not None:
                    print(f"[MCP-MANAGER-_health_check_loop] Process died for {server_name}, restarting...")
                    config._status = ServerStatus.UNHEALTHY
                    await self.restart_server(server_name)
                    continue
                
                # Check connection health
                if config.transport == TransportType.SSE and config.url and self._http_client:
                    try:
                        response = await self._http_client.get(
                            config.url.replace('/sse', ''),
                            timeout=config.timeout
                        )
                        if response.status_code == 200:
                            config._status = ServerStatus.CONNECTED
                            config._error_count = 0
                        else:
                            config._status = ServerStatus.UNHEALTHY
                            config._error_count += 1
                    except Exception:
                        config._status = ServerStatus.UNHEALTHY
                        config._error_count += 1
                
                config._last_health_check = datetime.now()
                
                # Auto-restart if too many errors
                if config._error_count >= 3:
                    print(f"[MCP-MANAGER-_health_check_loop] Too many errors for {server_name}, restarting...")
                    await self.restart_server(server_name)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MCP-MANAGER-_health_check_loop] Health check error for {server_name}: {e}")