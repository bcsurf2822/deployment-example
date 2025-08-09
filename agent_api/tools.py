"""
Brave Search API integration for Pydantic AI agents.

This module follows Pydantic AI best practices for tool creation
with proper dependency injection through RunContext.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncOpenAI
from httpx import AsyncClient
from supabase import Client
import logging
import os
import base64
import json


from dependencies import AgentDependencies

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Individual search result from Brave Search API."""
    
    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    description: str = Field(..., description="Description or snippet from the page")
    score: Optional[float] = Field(None, description="Relevance score if available")


class SearchResponse(BaseModel):
    """Complete search response containing multiple results."""
    
    results: List[SearchResult] = Field(..., description="List of search results")
    query: str = Field(..., description="Original search query")
    total_results: Optional[int] = Field(None, description="Total number of results found")


async def brave_search(
    ctx: RunContext[AgentDependencies],
    query: str, 
    count: int = 10
) -> str:
    """
    Perform a web search using Brave Search API.
    
    This tool follows Pydantic AI best practices by:
    - Accepting RunContext as first parameter
    - Accessing dependencies through ctx.deps
    - Using the injected HTTP client for requests
    
    Args:
        ctx: RunContext containing AgentDependencies
        query: The search query string
        count: Number of results to return (default: 10)
        
    Returns:
        Formatted search results as a string
    """
    deps = ctx.deps
    settings = deps.settings
    
    if settings.debug_mode:
        logger.info(f"[TOOLS-brave_search] Searching for: {query} (count: {count})")
        logger.info(f"[TOOLS-brave_search] Using endpoint: {settings.brave_search_url}")
    
    headers = {
        "X-Subscription-Token": deps.brave_api_key,
        "Accept": "application/json"
    }
    params = {
        "q": query,
        "count": count,
        "search_lang": "en"
    }
    
    try:
        response = await deps.http_client.get(
            settings.brave_search_url, 
            headers=headers, 
            params=params
        )
        response.raise_for_status()
        data = response.json()
        
        # Parse the response
        web_results = data.get("web", {}).get("results", [])
        
        if not web_results:
            return f"No results found for query: {query}"
        
        # Format results for the agent
        formatted_results = [f"Search results for: {query}\n"]
        
        for i, result in enumerate(web_results[:5], 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            description = result.get("description", "No description")
            
            formatted_results.append(
                f"{i}. {title}\n"
                f"   URL: {url}\n"
                f"   {description}\n"
            )
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"[TOOLS-brave_search] Error: {str(e)}")
        return f"Error performing search: {str(e)}"
    
async def get_embedding(text: str, embedding_client: AsyncOpenAI, embedding_model: str) -> List[float]:
    """
    Get embedding vector from OpenAI.
    """
    try:
        logger.info(f"[TOOLS-get_embedding] Using model: {embedding_model}")
        logger.info(f"[TOOLS-get_embedding] Text length: {len(text)}")
        logger.info(f"[TOOLS-get_embedding] OpenAI client base_url: {embedding_client.base_url}")
        logger.info(f"[TOOLS-get_embedding] Making embeddings request...")
        
        response = await embedding_client.embeddings.create(
            model=embedding_model,
            input=text,
        )
        
        logger.info(f"[TOOLS-get_embedding] Success! Embedding dimensions: {len(response.data[0].embedding)}")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"[TOOLS-get_embedding] Error: {e}")
        logger.error(f"[TOOLS-get_embedding] Error type: {type(e)}")
        logger.error(f"[TOOLS-get_embedding] Model used: {embedding_model}")
        return [0] * 1536


async def retrieve_relevant_documents(
    supabase: Client,
    embedding_client: AsyncOpenAI,
    user_query: str,
    embedding_model: str,
    top_k: int = 4
) -> str:
    """
    Retrieve relevant document chunks based on similarity search using RAG best practices.
    
    Args:
        supabase: Supabase client (should use service role key to bypass RLS)
        embedding_client: OpenAI client for embeddings
        user_query: The user's search query
        embedding_model: Model to use for embeddings
        top_k: Number of results to return
        
    Returns:
        Formatted string of relevant document chunks with similarity scores
    """
    try:
        logger.info(f"[TOOLS-retrieve_relevant_documents] Searching for: '{user_query}'")
        
        # Get embedding for the query
        query_embedding = await get_embedding(user_query, embedding_client, embedding_model)
        
        if not query_embedding or len(query_embedding) != 1536:
            logger.error(f"[TOOLS-retrieve_relevant_documents] Invalid embedding dimensions: {len(query_embedding) if query_embedding else 'None'}")
            return "Error: Could not generate valid embedding for the query."
        
        # Perform similarity search with proper logging
        logger.info(f"[TOOLS-retrieve_relevant_documents] Executing vector search with {len(query_embedding)}-dim embedding")
        
        response = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_count': top_k,
                'filter': {}
            }
        ).execute()
        
        logger.info(f"[TOOLS-retrieve_relevant_documents] Found {len(response.data) if response.data else 0} results")
        
        if not response.data:
            return "No relevant documents found in the knowledge base."
        
        # Apply similarity threshold (0.5 is more appropriate for embeddings - 0.7 was too restrictive)
        MIN_SIMILARITY = 0.5
        filtered_results = [doc for doc in response.data if doc.get('similarity', 0) >= MIN_SIMILARITY]
        
        if not filtered_results:
            logger.info(f"[TOOLS-retrieve_relevant_documents] No results above similarity threshold {MIN_SIMILARITY}")
            # If no results above threshold, return all results with a note about lower relevance
            filtered_results = response.data
            logger.info(f"[TOOLS-retrieve_relevant_documents] Returning all {len(filtered_results)} results due to no high-similarity matches")
        
        # Format results with improved readability
        results = []
        for chunk in filtered_results:
            content = chunk.get('content', '')
            similarity = chunk.get('similarity', 0)
            metadata = chunk.get('metadata', {})
            
            # Extract file_id and title from metadata for better context
            file_id = metadata.get('file_id', 'Unknown')  # This is the document_metadata.id (TEXT)
            title = metadata.get('file_name', metadata.get('title', f'Document {file_id}'))
            
            # Truncate content intelligently at sentence boundaries
            truncated_content = content[:600]
            if len(content) > 600:
                # Try to end at a sentence
                last_period = truncated_content.rfind('.')
                if last_period > 400:  # Only if we have a reasonable amount of content
                    truncated_content = truncated_content[:last_period + 1]
                else:
                    truncated_content = truncated_content + "..."
            
            results.append(
                f"📄 **{title}** (Match: {similarity:.2f})\n"
                f"{truncated_content}\n"
                f"*[File ID: {file_id}]*\n"
            )
        
        logger.info(f"[TOOLS-retrieve_relevant_documents] Returning {len(filtered_results)} relevant documents")
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"[TOOLS-retrieve_relevant_documents] Error: {e}")
        return f"Error retrieving documents: {str(e)}"


async def list_documents(supabase: Client) -> List[str]:
    """
    List all available documents in the database.
    
    Args:
        supabase: Supabase client
        
    Returns:
        List of document information
    """
    try:
        response = supabase.table('document_metadata').select('*').execute()
        
        if not response.data:
            return ["No documents found in the database."]
        
        documents = []
        for doc in response.data:
            # Use title if available, otherwise show as "Unnamed Document"
            title = doc.get('title', 'Unnamed Document')
            doc_info = (
                f"Title: {title}\n"
                f"ID: {doc.get('id', 'Unknown')}\n"
                f"URL: {doc.get('url', 'Unknown')}\n"
                f"Created: {doc.get('created_at', 'Unknown')}"
            )
            documents.append(doc_info)
        
        return documents
        
    except Exception as e:
        logger.error(f"[TOOLS-list_documents] Error: {e}")
        return [f"Error listing documents: {str(e)}"]


async def get_document_content(supabase: Client, document_id: str) -> str:
    """
    Get the full content of a document by file_id (from document_metadata).
    
    Args:
        supabase: Supabase client
        document_id: The file_id from document_metadata (TEXT, like Google Drive IDs)
        
    Returns:
        Combined content of all document chunks for this file
    """
    try:
        logger.info(f"[TOOLS-get_document_content] Fetching content for file_id: {document_id}")
        
        # Query documents table where metadata->>'file_id' matches the document_id
        response = supabase.table('documents')\
            .select('id, content, metadata')\
            .eq('metadata->>file_id', document_id)\
            .execute()
        
        if not response.data:
            return f"No content found for file ID: {document_id}"
        
        # Combine all document chunks for this file
        all_content = []
        for doc in response.data:
            content = doc.get('content', '')
            if content:
                all_content.append(content)
        
        if not all_content:
            return f"File {document_id} found but has no content"
        
        combined_content = '\n\n'.join(all_content)
        logger.info(f"[TOOLS-get_document_content] Retrieved {len(all_content)} chunks, total length: {len(combined_content)}")
        
        return combined_content
        
    except Exception as e:
        logger.error(f"[TOOLS-get_document_content] Error: {e}")
        return f"Error retrieving document content: {str(e)}"


async def execute_sql_query(supabase: Client, sql_query: str) -> str:
    """
    Run a SQL query - use this to query from the document_rows table once you know the file ID you are querying. 
    dataset_id is the file_id and you are always using the row_data for filtering, which is a jsonb field that has 
    all the keys from the file schema given in the document_metadata table.

    Example query:
    SELECT AVG((row_data->>'revenue')::numeric)
    FROM document_rows
    WHERE dataset_id = '123';

    Example query 2:
    SELECT 
        row_data->>'category' as category,
        SUM((row_data->>'sales')::numeric) as total_sales
    FROM document_rows
    WHERE dataset_id = '123'
    GROUP BY row_data->>'category';
    
    Args:
        supabase: Supabase client
        sql_query: SQL query to execute (must be read-only)
        
    Returns:
        Query results as formatted string
    """
    try:
        import re
        import json
        
        # Validate that the query is read-only by checking for write operations
        sql_query = sql_query.strip()
        write_operations = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']
        
        # Convert query to uppercase for case-insensitive comparison
        upper_query = sql_query.upper()
        
        # Check if any write operations are in the query
        for op in write_operations:
            pattern = r'\b' + op + r'\b'
            if re.search(pattern, upper_query):
                return f"Error: Write operation '{op}' detected. Only read-only queries are allowed."
        
        # Execute the query using the RPC function
        response = supabase.rpc(
            'execute_custom_sql',
            {"sql_query": sql_query}
        ).execute()
        
        # Check for errors in the response
        if response.data and isinstance(response.data, dict) and 'error' in response.data:
            return f"SQL Error: {response.data['error']}"
        
        if not response.data:
            return "Query returned no results."
        
        # Format results as JSON string
        return json.dumps(response.data, indent=2)
        
    except Exception as e:
        logger.error(f"[TOOLS-execute_sql_query] Error: {e}")
        return f"Error executing SQL query: {str(e)}"
    
async def analyze_image_tool(supabase: Client, document_id: str, query: str) -> str:
    try:
        # ENV for the vision model
        llm = os.getenv("VISION_MODEL")
        if not llm:
            raise ValueError("VISION_MODEL environment variable is not set")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not base_url:
            raise ValueError("BASE_URL environment variable is not set")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        logger.info(f"[TOOLS-analyze_image_tool] Using vision model: {llm}")
        logger.info(f"[TOOLS-analyze_image_tool] Using base URL: {base_url}")
        
        # Define the vision agent with proper model format
        from pydantic_ai import Agent as PydanticAgent
        vision_agent = PydanticAgent(
            model=f"openai:{llm}",
            system_prompt="You are an image analyzer who looks at images provided and answers the accompanying query in detail"
        )
        
        # Get the image binary from the database
        response = supabase.from_('documents') \
            .select('metadata') \
            .eq('metadata->>file_id', document_id) \
            .limit(1) \
            .execute()
        
        if not response.data:
            return f"No image found for document ID: {document_id}"
        
        # Get the image binary and mime_type
        metadata = response.data[0]['metadata']
        binary_str = metadata['file_contents']
        mime_type = metadata['mime_type']

        if not binary_str:
            return f"No binary data found for document ID: {document_id}"
        
        # Turn binary string into binary and send it to the vision LLM
        binary_bytes = base64.b64decode(binary_str.encode('utf-8'))
        logger.info(f"[TOOLS-analyze_image_tool] Image size: {len(binary_bytes)} bytes")
        logger.info(f"[TOOLS-analyze_image_tool] MIME type: {mime_type}")
        
        try:
            result = await vision_agent.run([query, BinaryContent(data=binary_bytes, media_type=mime_type)])
            return result.output
        except Exception as vision_error:
            logger.error(f"[TOOLS-analyze_image_tool] Vision agent error: {vision_error}")
            logger.error(f"[TOOLS-analyze_image_tool] Error type: {type(vision_error)}")
            raise
    
    except Exception as e:
        logger.error(f"[TOOLS-analyze_image_tool] Error analyzing image: {e}")
        return f"Error analyzing image: {str(e)}"
       