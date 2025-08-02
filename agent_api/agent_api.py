import sys
import os
import json
import asyncio
import base64
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from httpx import AsyncClient

# Load environment variables from .env
load_dotenv(override=True)

# Now import from local modules
from agent import agent, search
from clients import settings, get_supabase_client, get_openai_client, get_mem0_client_async, get_authenticated_supabase_client
from dependencies import AgentDependencies

# Import Pydantic AI types
from pydantic_ai import Agent, ModelRequestNode
from pydantic_ai.messages import (
    PartStartEvent,
    PartDeltaEvent,
    TextPartDelta,
    BinaryContent
)

# Import database utilities
from db_utils import (
    fetch_conversation_history,
    convert_history_to_pydantic_format,
    create_conversation,
    store_message,
    update_conversation_title,
    check_rate_limit,
    store_request,
    should_generate_or_update_title,
    generate_conversation_summary
)


# We now define clients as None
embeddings_client = None
supabase = None
http_client = None
title_agent = None
mem0_client = None

# Define the lifespan context manager (Best practice)
# Fast API we have concept of lifespan to create clients 
# way to create client in every request w/oo havin gto create in every request

@asynccontextmanager
async def lifespan(app: FastAPI):
    global embeddings_client, supabase, http_client, title_agent, mem0_client

    # Startup: Initialize clients
    embeddings_client = get_openai_client()
    supabase = get_supabase_client()
    http_client = AsyncClient()
    title_agent = Agent('openai:gpt-4-turbo')
    mem0_client = await get_mem0_client_async()

    # Yield control back to FastAPI
    yield

    # Shutdown: Clean up clients
    if http_client:
        await http_client.aclose()


# Initialize FastAPI Application
app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File attachments
class FileAttachment(BaseModel):
    fileName: str
    content: str # Base64 encoded content
    mimeType: str

# Request/Response Models
class AgentRequest(BaseModel):
    query: str
    user_id: str
    request_id: str
    session_id: str
    files: Optional[List[FileAttachment]] = None

class AgentResponse(BaseModel):
    success: bool
    error: Optional[str] = None

# Helper function to stream error responses
async def stream_error_response(error_message: str, request_id: str):
    """Stream an error response in the same format as successful responses"""
    error_data = {
        "text": error_message,
        "error": True,
        "request_id": request_id,
        "complete": True,
    }
    yield json.dumps(error_data).encode('utf-8') + b'\n'

# Verify token function
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> tuple[Dict[str, Any], str]:
    """
    Verify the JWT token from Supabase / Return User information and token

    Args: credentials: The HTTP Authorization Credentials containing the bearer token

    Returns: tuple[Dict[str, Any], str] - The user information from Supabase and the token

    Raises: HTTPException(401) - If the token is invalid or cannot be verified
    """
    try:
        # Extract the token from the credentials
        token = credentials.credentials
        
        # Check if token exists
        if not token:
            print(f"[AGENT_API-VERIFY_TOKEN] No token provided in Authorization header")
            raise HTTPException(status_code=401, detail="No authorization token provided")
        
        if not http_client:
            raise HTTPException(status_code=500, detail="HTTP client not initialized")
        
        # Get Supabase URL and anon key from environment variables
        # Should match Environment Variable names used in project
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        # Check if environment variables are set
        if not supabase_url:
            print(f"[AGENT_API-VERIFY_TOKEN] SUPABASE_URL environment variable is missing")
            raise HTTPException(status_code=500, detail="Server configuration error: SUPABASE_URL not set")
        
        if not supabase_key:
            print(f"[AGENT_API-VERIFY_TOKEN] SUPABASE_ANON_KEY environment variable is missing")
            raise HTTPException(status_code=500, detail="Server configuration error: SUPABASE_ANON_KEY not set")

        # Create Supabase client
        response = await http_client.get(f"{supabase_url}/auth/v1/user", headers={"Authorization": f"Bearer {token}", "apikey": supabase_key})

        # Check if the response is successful
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Parse the response JSON
        user_data = response.json()
        return user_data, token
    except Exception as e:
        print(f"[AGENT_API-VERIFY_TOKEN] Error verifying token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
        
       
# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration and monitoring.
    
    Returns:
        Dict with status and service health information
    """
    # Check if critical dependencies are initialized
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "embeddings_client": embeddings_client is not None,
            "supabase": supabase is not None,
            "http_client": http_client is not None,
            "title_agent": title_agent is not None,
            "mem0_client": mem0_client is not None
        }
    }
    
    # If any critical service is not initialized, mark as unhealthy
    if not all(health_status["services"].values()):
        health_status["status"] = "unhealthy"
        return JSONResponse(status_code=503, content=health_status)
    
    return health_status

# Routes  | Adds mems makes request record, get res from agent , and makes titles all in parallel making it very efficient
@app.post("/api/pydantic-agent")
async def pydantic_agent(request: AgentRequest, auth_result: tuple[Dict[str, Any], str] = Depends(verify_token)):
    # Extract user and token from auth result
    user, access_token = auth_result
    
    # Verify user ID in the request matches the user ID from the token
    # Once you have the user ID you can secure in so many different ways such as token limits tracking tokens etc
    if request.user_id != user.get("id"):
        raise HTTPException(status_code=403, detail="Unauthorized, User ID does not match the authenticated user")
    
    try:
        # Create authenticated Supabase client for this user
        auth_supabase = get_authenticated_supabase_client(access_token)
        
        # Check Rate Limit using authenticated client
        rate_limit_ok = await check_rate_limit(auth_supabase, request.user_id)
        if not rate_limit_ok:
            return StreamingResponse(
                stream_error_response("Rate limit exceeded. Please try again later.", request.request_id),
                media_type="text/plain",
            )

        # start request tracking
        request_tracking_task = asyncio.create_task(
            store_request(auth_supabase, request.request_id, request.user_id, request.query)
        )

        
        session_id = request.session_id
        conversation_record = None
        conversation_title = None

        # check if sess_id is empty, create a new conversation if needed
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            # create a new conversation record
            conversation_record = await create_conversation(auth_supabase, request.user_id, session_id)


        # Store users query immediately with any file attachments
        file_attachments = None
        if request.files:
            # Convert Pydantic models to dictionaries for storage
            file_attachments = [
                {
                    "fileName": file.fileName,
                    "content": file.content,
                    "mimeType": file.mimeType,
                } for file in request.files]

        # Store users query right away
        await store_message(auth_supabase, session_id=session_id, message_type="human", content=request.query, files=file_attachments)

        # Fetch Conversation History from DB 
        conversation_history = await fetch_conversation_history(auth_supabase, session_id)

        # Convert conversation history into framework format (Pydantic Here)
        pydantic_messages = await convert_history_to_pydantic_format(conversation_history)

        # Retrieve user's memories with Mem0
        print(f"[AGENT_API-MEMORY_SEARCH] Searching memories for user_id: {request.user_id}")
        relevant_memories = await mem0_client.search(query=request.query, user_id=request.user_id, limit=3)
        print(f"[AGENT_API-MEMORY_SEARCH] Found {len(relevant_memories.get('results', []))} memories")
        memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories.get('results', []))

        # Check if we should generate or update the conversation title
        should_generate_title, title_reason = await should_generate_or_update_title(auth_supabase, session_id, request.query)
        print(f"[AGENT_API-TITLE_DECISION] {title_reason}")
        
        # Start smart title generation in parallel if needed
        title_task = None
        if should_generate_title:
            async def generate_smart_title():
                try:
                    # Get full conversation history for context
                    full_history = await fetch_conversation_history(auth_supabase, session_id, limit=20)
                    conversation_summary = await generate_conversation_summary(full_history)
                    
                    # Create a more contextual prompt for title generation
                    title_prompt = f"""
                    Generate a concise, specific title (3-6 words) for this conversation based on the following summary:
                    
                    {conversation_summary}
                    
                    Current query: {request.query}
                    
                    The title should reflect the main topic or purpose of the conversation, not generic greetings.
                    Examples of good titles: "Python Data Analysis Help", "Resume Review Session", "JavaScript Bug Debugging"
                    """
                    
                    result = await title_agent.run(title_prompt)
                    title = result.output if hasattr(result, 'output') else str(result)
                    
                    # Clean up the title (remove quotes, trim)
                    title = title.strip().strip('"\'')
                    print(f"[AGENT_API-GENERATE_TITLE] Generated title: {title}")
                    return title
                except Exception as e:
                    print(f"[AGENT_API-GENERATE_TITLE] Error generating title: {str(e)}")
                    return f"Conversation - {request.query[:30]}..."
            
            title_task = asyncio.create_task(generate_smart_title())

        async def stream_response():
            # Process title result if it exists (IN BACKGROUND)
            nonlocal conversation_title

            # Use the global HTTP Client Here
            agent_deps = AgentDependencies(
                http_client=http_client,
                embedding_client=embeddings_client,
                supabase=supabase,
                settings=settings,
                memories=memories_str
            )

            # Process any file attachments for the agent
            binary_contents = []
            if request.files:
                try:
                    for file in request.files:
                        # Decode base64 content
                        binary_data = base64.b64decode(file.content)
                        # Create binary content object / LLM Don't accept text/plain so we convert to application/pdf
                        fileMimeType = "application/pdf" if file.mimeType == "text/plain" else file.mimeType
                        binary_content = BinaryContent(
                            data=binary_data,
                            media_type=fileMimeType
                        )
                        binary_contents.append(binary_content)
                except Exception as e:
                    print(f"[AGENT_API-FILE_ATTACHMENT] Error processing file attachment: {str(e)}")


            # Prepare the user message - if there are binary contents, include them with the query
            if binary_contents:
                # For Pydantic AI, we need to create a UserMessage with both text and binary content
                user_message = [request.query] + binary_contents
            else:
                user_message = request.query

            # Run Agent with user prompt and the chat history this is the same as streamlit where we can see the agent thinking and typing out its response in rewal time (Cannot do this in N8N)
            async with agent.iter(user_message, deps=agent_deps, message_history=pydantic_messages) as run:
                full_response = ""
                async for node in run:
                    if isinstance(node, ModelRequestNode):
                        # A model request node => We can stream tokens from the model's request
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                    yield json.dumps({"text": event.part.content}).encode('utf-8') + b'\n'
                                    full_response += event.part.content
                                elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                    delta = event.delta.content_delta
                                    yield json.dumps({"text": full_response}).encode('utf-8') + b'\n'
                                    full_response += delta

            # After streaming is complete store the full response in the database
            message_data =  run.result.new_messages_json()
            
            # Store agent response
            await store_message(auth_supabase, session_id=session_id, message_type="ai", content=full_response, message_data=message_data, data={"request_id": request.request_id})


            # Wait for title gen to compelete if it's running
            if title_task:
                title_result = await title_task
                conversation_title = title_result

            # Update conversation title in database
            if conversation_title:
                await update_conversation_title(auth_supabase, session_id, conversation_title)

            # Send the final title in the last chunk

            final_data = {
                "text": "",
                "session_id": session_id,
                "conversation_title": conversation_title,
                "complete": True,
            }

            yield json.dumps(final_data).encode('utf-8') + b'\n'
            
            # Store conversation memories after streaming is complete
            try:
                memory_messages = [
                    {"role": "user", "content": request.query},
                    # Including AI Response from the agent often leads to much verbose memories however this is an example of how to do it
                    # {"role": "assistant", "content": full_response},
                ]

                # Store memories in the database
                await mem0_client.add(memory_messages, user_id=request.user_id)
            except Exception as e:
                print(f"[AGENT_API-MEMORY_STORAGE] Error storing memories: {str(e)}")

        return StreamingResponse(stream_response(), media_type="text/plain")

    except Exception as e:
        print(f"Error in pydantic_agent: {str(e)}")
        # Store error message in conversation if session_id is provided
        if request.session_id:
            try:
                await store_message(
                    auth_supabase, 
                    session_id=request.session_id, 
                    message_type="ai", 
                    content="I apologize, I'm having trouble processing your request. Please try again later.", 
                    data={"error": str(e), "request_id": request.request_id}
                )
            except Exception as store_error:
                print(f"[AGENT_API-ERROR_STORAGE] Failed to store error message: {str(store_error)}")
        
        # Return streaming error response instead of raising HTTPException
        error_message = "I apologize, I'm having trouble processing your request. Please try again later."
        return StreamingResponse(
            stream_error_response(error_message, request.request_id),
            media_type="text/plain",
            status_code=500
        )
    

# Run the app with uvicorn and host it on localhost:8001
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)