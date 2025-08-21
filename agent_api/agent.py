"""
Brave Search Agent using Pydantic AI.

This module follows Pydantic AI best practices for:
- Dependency injection using dataclasses
- Proper tool registration with RunContext
- Environment variable management through pydantic-settings
"""

import asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.mcp import MCPServerSSE

from clients import settings, setup_openai_env
from dependencies import AgentDependencies, create_dependencies, cleanup_dependencies
from tools import (
    brave_search,
    retrieve_relevant_documents,
    list_documents,
    get_document_content,
    execute_sql_query,
    analyze_image_tool
)
from typing import List
from prompts import SYSTEM_PROMPT


# ============AGENT DEFINITION PART==========
# Create the agent with proper dependency injection
# Set environment variable for OpenAI API key
setup_openai_env()


# ============MCP SERVER==========
# MCP servers are now managed dynamically through MCPManager
# The manager handles:
# - Automatic startup of configured servers
# - Health checking and auto-recovery
# - Dynamic server registration/unregistration
# - Multiple transport types (SSE, Stdio, HTTP)

# Create agent with dynamic toolsets from MCP manager
# Toolsets will be populated from dependencies at runtime
agent = Agent(
    model=f"openai:{settings.openai_model}",
    system_prompt=SYSTEM_PROMPT,
    deps_type=AgentDependencies,  # Specify the dependency type
    instrument=True
)

# Function to update agent toolsets dynamically
def update_agent_toolsets(mcp_manager):
    """Update agent toolsets from MCP manager."""
    if mcp_manager:
        toolsets = mcp_manager.get_active_toolsets()
        if toolsets:
            # Note: Pydantic AI doesn't have a direct way to update toolsets after creation
            # We'll need to handle this through dependency injection
            print(f"[AGENT-update_toolsets] Active MCP toolsets: {len(toolsets)}")
            return toolsets
    return []

# ============Agent Tools==========
# Register tools with proper RunContext usage using decorator pattern

# IMPORTANT: How Pydantic AI uses docstrings for LLM context:
# 
# The triple-quoted string ("""...""") below is NOT a regular comment - it's a Python docstring.
# Pydantic AI extracts these docstrings and sends them to the LLM as tool descriptions.
# 
# When the LLM sees available tools, it receives:
# 1. The function name (e.g., "web_search")
# 2. The entire docstring content as the tool description
# 3. The function parameters and their types
# 
# This is why the docstring format matters - the LLM uses this text to understand:
# - WHAT the tool does (main description)
# - WHEN to use it (based on the description)
# - HOW to use it (Args section)
# - WHAT to expect back (Returns section)
#
# The @agent.tool decorator is what registers this function as a tool and extracts the docstring.
# Behind the scenes, Pydantic AI uses Python's introspection capabilities to:
# - Access the function's __doc__ attribute (which contains the docstring)
# - Extract parameter names and types from the function signature
# - Package all this information for the LLM in the system message

@agent.tool
async def web_search(
    ctx: RunContext[AgentDependencies],
    query: str, 
    count: int = 10
) -> str:
    """
    Search the web with a specific query and get a summary of the top search results.
    
    Args:
        ctx: The context for the agent including the HTTP client and optional Brave API key/SearXNG base url
        query: The query for the web search
        count: Number of results to return (default: 10)
        
    Returns:
        A summary of the web search.
        For Brave, this is a single paragraph.
        For SearXNG, this is a list of the top search results including the most relevant snippet from the page.
    """
    print(f"[AGENT-web_search] Calling web_search tool")
    return await brave_search(ctx, query, count)

@agent.tool
async def retrieve_documents(ctx: RunContext[AgentDependencies], user_query: str) -> str:
    """
    Retrieve relevant document chunks based on the query with RAG.

    Args:
        ctx: The context including the Supabase client and OpenAI client.
        user_query: The user's question or query.
        
    Returns:
        A formatted string of the 4 most relevant document chunks.
    """
    # TECHNICAL NOTE: When Pydantic AI processes this tool, it sends something like this to the LLM:
    # 
    # Available tool: retrieve_documents
    # Description: Retrieve relevant document chunks based on the query with RAG.
    # 
    # Args:
    #     ctx: The context including the Supabase client and OpenAI client.
    #     user_query: The user's question or query.
    # 
    # Returns:
    #     A formatted string of the 4 most relevant document chunks.
    # 
    # Parameters:
    # - user_query (string, required): The search query
    # 
    # The LLM then decides whether to call this tool based on:
    # 1. The system prompt (which tells it to search documents first)
    # 2. The tool description (which mentions "RAG" and "document chunks")
    # 3. The user's query (if it seems like something that could be in documents)
    
    print(f"[AGENT-retrieve_documents] Calling retrieve_relevant_documents tool")
    return await retrieve_relevant_documents(
        ctx.deps.supabase, 
        ctx.deps.embedding_client, 
        user_query,
        ctx.deps.settings.embedding_model
    )

@agent.tool
async def list_all_documents(ctx: RunContext[AgentDependencies]) -> List[str]:
    """
    Retrieve a list of all available documents.

    Args:
        ctx: The context including the Supabase client.
        
    Returns:
        List[str]: A list of documents with their title, ID, URL, and creation date.
    """
    print(f"[AGENT-list_all_documents] Calling list_documents tool")
    return await list_documents(ctx.deps.supabase)

@agent.tool
async def get_full_document(ctx: RunContext[AgentDependencies], document_id: str) -> str:
    """
    Retrieve the full content of a specific document by its file ID.

    Args:
        ctx: The context including the Supabase client and OpenAI client.
        document_id: The file_id from the search results (e.g., "1VjmwV4nDTnELGfvd7N0RkdIYC8c_j0S8")
        
    Returns:
        str: The complete content of the document with all chunks combined.
    """
    print(f"[AGENT-get_full_document] Calling get_document_content tool")
    return await get_document_content(ctx.deps.supabase, document_id)

@agent.tool
async def run_sql_query(ctx: RunContext[AgentDependencies], sql_query: str) -> str:
    """
    Run a SQL query: use this query from the document_rows table once you know the file ID you are querying. 
    dataset_id is the file_id and you are always using the row_data for filtering, which is a jsonb field that has all the keys from the file schema given in the document_metadata table.

    Never use a placeholder file ID. Always use the list_documents tool first to get the file ID.

    Example Query:
    SELECT AVG((row_data->>'revenue')::numeric)
    FROM document_rows
    WHERE dataset_id = '123';

    Example Query 2:
    SELECT COUNT(*)
    FROM document_rows
    WHERE dataset_id = '123'
    AND (row_data->>'revenue')::numeric > 1000;

    Example Query 3:
    SELECT COUNT(*)
    FROM document_rows
    WHERE dataset_id = '123'
    AND (row_data->>'revenue')::numeric > 1000;

    Example Query 4:
    SELECT COUNT(*)
    FROM document_rows
    WHERE dataset_id = '123'
    AND (row_data->>'revenue')::numeric > 1000;

    Args:
        ctx: The context including the Supabase client.
        sql_query: The SQL query to execute.
        
    Returns:
        str: The results of the SQL query in JSON format.
    """
    print(f"[AGENT-run_sql_query] Calling execute_sql_query tool with SQL: {sql_query}")
    return await execute_sql_query(ctx.deps.supabase, sql_query)

# Image Analysis Tool

@agent.tool
async def analyze_image(ctx: RunContext[AgentDependencies], document_id: str, query: str) -> str:
    """
    Analyze an image and return a summary of the image based on the document ID of the image provided.  This function pulls the binary of the image from the knowledge base and passes that into a subagent with a vision LLM. Before calling this tool, call list-documents to see the images available and to get the exact document ID for the image you want to analyze.

    Args:
        ctx: The context including the Supabase client and OpenAI client.
        document_id: The ID (or file path) of the document to retrieve.
        query: What to extract from the image.

    Returns:
        str: An analysis of the image based on the query.
    """
    print(f"[AGENT-analyze_image] Calling analyze_image tool with document_id: {document_id} and query: {query}")
    return await analyze_image_tool(ctx.deps.supabase, document_id, query)

# ============SYSTEM PROMPT==========
@agent.system_prompt
async def dynamic_system_prompt(ctx: RunContext[AgentDependencies]) -> str:
    """
    Dynamic system prompt that can access dependencies.
    
    This demonstrates how to use RunContext in system prompts.
    """
    base_prompt = SYSTEM_PROMPT
    
    # Add user memories if available
    if hasattr(ctx.deps, 'memories') and ctx.deps.memories:
        base_prompt += f"\n\nUser Memories:\n{ctx.deps.memories}"
    
    if ctx.deps.settings.debug_mode:
        base_prompt += "\n\nDEBUG MODE: Provide detailed information about your search process."
    
    return base_prompt


async def search(query: str) -> str:
    """
    Perform a web search using the Brave Search agent.
    
    This follows best practices by:
    - Creating dependencies properly
    - Passing them to the agent
    - Cleaning up resources
    
    Args:
        query: The search query
        
    Returns:
        Search results and agent's response
    """
    deps = None
    try:
        # Create dependencies with MCP manager
        deps = await create_dependencies()
        
        # Get MCP toolsets from the manager
        toolsets = []
        if deps.mcp_manager:
            toolsets = deps.mcp_manager.get_active_toolsets()
            if toolsets:
                print(f"[AGENT-search] Using {len(toolsets)} MCP toolsets")
        
        # Run the agent with dependencies and dynamic toolsets
        result = await agent.run(query, deps=deps, toolsets=toolsets)
        return result.output  # Use .output instead of deprecated .data
        
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        # Clean up dependencies
        if deps:
            await cleanup_dependencies(deps)


async def interactive_search():
    """
    Run an interactive search session.
    
    This demonstrates proper dependency lifecycle management.
    """
    print("Brave Search Agent (using Pydantic AI)")
    print("Type 'quit' or 'exit' to end the session")
    print("-" * 50)
    
    # Create dependencies once for the session
    deps = None
    toolsets = []
    try:
        deps = await create_dependencies()
        
        # Get MCP toolsets
        if deps.mcp_manager:
            toolsets = deps.mcp_manager.get_active_toolsets()
            if toolsets:
                print(f"Connected to {len(toolsets)} MCP server(s)")
            
            # Show MCP server status
            servers_status = deps.mcp_manager.get_all_servers_status()
            for status in servers_status:
                print(f"MCP Server '{status['name']}': {status['status']}")
        
        # Show configuration info in debug mode
        if deps.settings.debug_mode:
            print(f"Using OpenAI model: {deps.settings.openai_model}")
            print(f"Using OpenAI endpoint: {deps.settings.openai_base_url}")
            print(f"Using Brave Search endpoint: {deps.settings.brave_search_url}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Configuration error: {str(e)}")
        print("Please set up your environment variables in .env file")
        return
    
    try:
        while True:
            query = input("\nEnter your search query: ").strip()
            
            if query.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            if not query:
                print("Please enter a valid search query.")
                continue
            
            print("\nSearching...")
            try:
                # Update toolsets in case they changed
                if deps.mcp_manager:
                    toolsets = deps.mcp_manager.get_active_toolsets()
                
                result = await agent.run(query, deps=deps, toolsets=toolsets)
                print("\n" + result.output)
            except Exception as e:
                print(f"Error: {str(e)}")
                
    finally:
        # Always clean up dependencies
        if deps:
            await cleanup_dependencies(deps)


def main():
    """
    Main entry point for the search agent.
    """
    asyncio.run(interactive_search())


if __name__ == "__main__":
    main()