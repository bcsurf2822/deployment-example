"""
Dependency injection container for Pydantic AI agent.

This module defines the dependencies that will be injected into
the agent's tools and system prompts.
"""

from dataclasses import dataclass
import httpx
from supabase import Client
from openai import AsyncOpenAI
from clients import (
    Settings, 
    settings,
    get_supabase_client,
    get_embedding_client,
    get_http_client
)


@dataclass
class AgentDependencies:
    """
    Dependencies container for the Pydantic AI agent.
    
    This follows Pydantic AI best practices for dependency injection,
    using a dataclass to hold all required dependencies.
    """
    settings: Settings
    http_client: httpx.AsyncClient
    supabase: Client
    embedding_client: AsyncOpenAI
    memories: str
    
    @property
    def brave_api_key(self) -> str:
        """Get the Brave API key (unwrapped from SecretStr)."""
        return self.settings.brave_api_key.get_secret_value()
    
    @property
    def openai_api_key(self) -> str:
        """Get the OpenAI API key (unwrapped from SecretStr)."""
        return self.settings.openai_api_key.get_secret_value()
    
    @property
    def supabase_key(self) -> str:
        """Get the Supabase key (unwrapped from SecretStr)."""
        return self.settings.supabase_key.get_secret_value()


async def create_dependencies(memories: str = "") -> AgentDependencies:
    """
    Create and initialize dependencies for the agent.
    
    Args:
        memories: User memories string to include in the dependencies
    
    Returns:
        AgentDependencies instance with all required dependencies
    """
    # Use client factory functions from clients module
    http_client = get_http_client()
    supabase = get_supabase_client()
    embedding_client = get_embedding_client()
    
    return AgentDependencies(
        settings=settings,
        http_client=http_client,
        supabase=supabase,
        embedding_client=embedding_client,
        memories=memories
    )


async def cleanup_dependencies(deps: AgentDependencies) -> None:
    """
    Cleanup dependencies (e.g., close HTTP connections).
    
    Args:
        deps: Dependencies to cleanup
    """
    if deps.http_client:
        await deps.http_client.aclose()