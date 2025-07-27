"""
Client configuration and initialization module.

This module handles all external client initialization and environment
configuration, centralizing API keys, base URLs, and client creation.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from supabase import create_client, Client
from openai import AsyncOpenAI
import httpx
from typing import Optional
from mem0 import Memory, AsyncMemory


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    Follows Pydantic Settings best practices for secure configuration management.
    """
    
    # API Keys - using SecretStr for sensitive data
    openai_api_key: SecretStr = Field(
        ..., 
        alias="OPENAI_API_KEY",
        description="OpenAI API key for LLM access"
    )
    brave_api_key: SecretStr = Field(
        ..., 
        alias="BRAVE_API_KEY",
        description="Brave Search API key"
    )
    supabase_url: str = Field(
        ...,
        alias="SUPABASE_URL",
        description="Supabase project URL"
    )
    supabase_key: SecretStr = Field(
        ...,
        alias="SUPABASE_KEY",
        description="Supabase service role key"
    )
    
    # Database Configuration
    database_url: SecretStr = Field(
        ...,
        alias="DATABASE_URL",
        description="PostgreSQL connection string for Supabase"
    )
    
    # API Endpoints
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_BASE_URL",
        description="OpenAI API base URL"
    )
    brave_search_url: str = Field(
        default="https://api.search.brave.com/res/v1/web/search",
        alias="BRAVE_SEARCH_URL",
        description="Brave Search API endpoint"
    )
    
    # Model Configuration
    openai_model: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_MODEL",
        description="OpenAI model to use"
    )
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        alias="EMBEDDING_MODEL",
        description="OpenAI embedding model to use"
    )
    
    # Request Configuration
    request_timeout: int = Field(
        default=30,
        alias="REQUEST_TIMEOUT",
        description="HTTP request timeout in seconds"
    )
    
    # Debug Configuration
    debug_mode: bool = Field(
        default=False,
        alias="DEBUG_MODE",
        description="Enable debug logging"
    )
    
    model_config = SettingsConfigDict(
        env_file=['.env'],
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Ignore extra environment variables
    )


# Create a singleton instance
settings = Settings()


def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.
    
    Returns:
        Supabase client instance
    """
    return create_client(
        settings.supabase_url,
        settings.supabase_key.get_secret_value()
    )


def get_openai_client() -> AsyncOpenAI:
    """
    Create and return an OpenAI client for general use.
    
    Returns:
        AsyncOpenAI client instance
    """
    return AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        base_url=settings.openai_base_url
    )


def get_embedding_client() -> AsyncOpenAI:
    """
    Create and return an OpenAI client specifically for embeddings.
    
    Returns:
        AsyncOpenAI client instance configured for embeddings
    """
    # For now, using the same client as general OpenAI
    # Can be customized if needed for different embedding providers
    return AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        base_url=settings.openai_base_url
    )


def get_http_client(timeout: Optional[int] = None) -> httpx.AsyncClient:
    """
    Create and return an HTTP client with appropriate settings.
    
    Args:
        timeout: Optional timeout override
        
    Returns:
        httpx.AsyncClient instance
    """
    return httpx.AsyncClient(
        timeout=timeout or settings.request_timeout,
        headers={"User-Agent": "PydanticAI-BraveSearch/1.0"}
    )


def get_supabase_connection_string() -> str:
    """
    Get the Supabase PostgreSQL connection string.
    
    Returns:
        The connection string for Supabase PostgreSQL database
    """
    return settings.database_url.get_secret_value()


def setup_openai_env():
    """
    Set up OpenAI environment variable.
    This is called to ensure the OpenAI API key is available in the environment.
    """
    os.environ['OPENAI_API_KEY'] = settings.openai_api_key.get_secret_value()

def get_mem0_config():
    # LLM Provider
    llm_provider = os.getenv("LLM_PROVIDER")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_model = os.getenv("LLM_MODEL")

    # Embedding Provider
    embedding_provider = os.getenv("EMBEDDING_PROVIDER")
    embedding_api_key = os.getenv("EMBEDDING_API_KEY")
    embedding_model = os.getenv("EMBEDDING_MODEL")

    config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": llm_model or settings.openai_model,
            "temperature": 0.2,
            "max_tokens": 2000,
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": embedding_model or settings.embedding_model,
        }
    },
    "vector_store": {
        "provider": "supabase",
        "config": {
            "connection_string": get_supabase_connection_string(),
            "collection_name": "mem0_memories",
            "index_method": "hnsw",  # Optional: defaults to "auto"
            "index_measure": "cosine_distance"  # Optional: defaults to "cosine_distance"
        }
    }
}
    
    return config


def get_mem0_client():
    # Create and return the Memory client
    config = get_mem0_config()
    return Memory.from_config(config)

async def get_mem0_client_async():
    # Create and return the Memory client
    config = get_mem0_config()    
    return await AsyncMemory.from_config(config)