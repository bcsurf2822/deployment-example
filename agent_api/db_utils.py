from typing import List, Optional, Dict, Any, AsyncIterator, Union, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from supabase import Client
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
import random
import json
import re


async def fetch_conversation_history(supabase: Client, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """ Fetch the conversation history from the database """
    try:
        response = supabase.table("messages") \
            .select("*") \
            .eq("session_id", session_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversation history: {e}")

# Conver History to Pydantic Format
async def convert_history_to_pydantic_format(conversation_history):
    """ Convert the conversation history to Pydantic format 
    Handles both AI messages with message_data and human messages without
    """
    # Import will be done inline when needed

    messages: List[ModelMessage] = []

    # Process messages in reverse order (oldest first)
    for msg in reversed(conversation_history):
        # Handle AI messages with message_data
        if msg.get("message_data"):
            try:
                # Validate the message_data field directly as JSON string
                # ModelMessagesTypeAdapter.validate_json expects a JSON string, not a parsed object
                messages.extend(ModelMessagesTypeAdapter.validate_json(msg["message_data"]))
            except Exception as e:
                print(f"[DB_UTILS-CONVERT_HISTORY] Error parsing message_data: {e}")
                # Skip message if there is an error
                continue
        
        # Handle human messages without message_data
        elif msg.get("message") and msg["message"].get("type") == "human":
            try:
                # Create a user message in the format expected by Pydantic AI
                user_message = {
                    "parts": [{"content": msg["message"]["content"], "part_kind": "user-prompt"}],
                    "instructions": None,
                    "kind": "request"
                }
                # Convert to JSON string and validate
                import json
                user_message_json = json.dumps([user_message])
                messages.extend(ModelMessagesTypeAdapter.validate_json(user_message_json))
            except Exception as e:
                print(f"[DB_UTILS-CONVERT_HISTORY] Error creating user message: {e}")
                continue
    
    return messages


# Create Conversation Record 
async def create_conversation(supabase: Client, user_id: str, session_id: str) -> dict[str, Any]:
    """
    Create a new Conversation record in the database
    
    Args:
        user_id (str): The user ID
        session_id (str): The session ID
    
    Returns:
        dict[str, Any]: The created conversation record
    """
    try:
        # Create a new conversation record
        response = supabase.table('conversations') \
            .insert({"user_id": user_id, "session_id": session_id}) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to create conversation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {e}")
    

async def update_conversation_title(supabase: Client, session_id: str, title: str) -> dict[str, Any]:
    """ Update the conversation title in the database 
    
    Args:
        session_id (str): The session ID
        title (str): The new title for the conversation
    
    Returns:
        dict[str, Any]: The updated conversation record
    """
    try:
        response = supabase.table("conversations") \
            .update({"title": title}) \
            .eq("session_id", session_id) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to update conversation title")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating conversation title: {e}")

async def store_message(
        supabase: Client,
        session_id: str,
        message_type: str,
        content: str,
        message_data: Optional[bytes] = None,
        data: Optional[Dict]=None,
        files: Optional[List[Dict]] = None,
):
    """ Store a message in the database table 
    
    Args:
        supabase: Supabase client
        session_id: The session ID
        message_type: The type of message
        content: The content of the message
        message_data: Optional: The binary data associated with the message
        data: Optional: Additional data to store with the message
        files: Optional: List of file attachments

    Returns:
        None
    
    """
    message_obj = {
        "type": message_type,
        "content": content,
    }
    if data:
        message_obj["data"] = data
    
    if files:
        message_obj["files"] = files

    try:
        insert_data = {
            "session_id": session_id,
            "message": message_obj,
        }
        if message_data:
            insert_data["message_data"] = message_data.decode("utf-8")

        supabase.table("messages").insert(insert_data).execute()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing message: {e}")
    

async def check_rate_limit(supabase: Client, user_id: str, rate_limit: int = 5) -> bool:
    """ Check if the user has exceeded the rate limit 
    
    Args:
        supabase: Supabase client
        user_id: The user ID
        rate_limit: The rate limit for the user
    
    Returns:
        bool: True if the user has exceeded the rate limit, False otherwise
    """
    try:
        # Get Timestamp for -1 min ago (UTC important depending on your db service)
        one_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")

        # Use count() to effeciently get just the number of requests w/o fetching all of the records
        response = supabase.table("requests") \
            .select("*", count="exact") \
            .eq("user_id", user_id) \
            .gte("timestamp", one_min_ago) \
            .execute()
        
        # Get the count of requests
        request_count = response.count if hasattr(response, "count") else 0

        # Check if the user has exceeded the rate limit
        return request_count < rate_limit
    except Exception as e:
        print(f"Error checking rate limit: {e}")
        return False
    
# Add a record to the requests table
async def store_request(supabase: Client, request_id: str, user_id: str, query: str):
    """ Store a request in the database 
    
    Args:
        supabase: Supabase client
        request_id: The request ID (will be converted to UUID)
        user_id: The user ID
        query: The query
    """
    try:
        import uuid
        # Generate a proper UUID for the request
        request_uuid = str(uuid.uuid4())
        
        # Store the request in the database, timestamp is optional since it is set automatically by Supabase
        supabase.table("requests").insert({
            "id": request_uuid, 
            "user_id": user_id, 
            "user_query": query, 
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        print(f"[DB_UTILS-STORE_REQUEST] Stored request with UUID: {request_uuid} (original ID: {request_id})")
    except Exception as e:
        print(f"[DB_UTILS-STORE_REQUEST] Error storing request: {e}")
        # Don't raise HTTPException here as this is running in background task
        # Just log the error and continue


def is_simple_greeting(message: str) -> bool:
    """Check if a message is a simple greeting that shouldn't be used for title generation"""
    greeting_patterns = [
        r'^(hi|hello|hey|good morning|good afternoon|good evening)\.?$',
        r'^(how are you|how\'s it going|what\'s up|sup)\.?\??$',
        r'^(greetings|salutations)\.?$',
        r'^(yo|howdy)\.?$',
        r'^(good day|nice to meet you)\.?$'
    ]
    
    message_clean = message.lower().strip()
    for pattern in greeting_patterns:
        if re.match(pattern, message_clean):
            return True
    return False


async def should_generate_or_update_title(supabase: Client, session_id: str, current_query: str) -> tuple[bool, str]:
    """
    Determine if we should generate or update a conversation title
    
    Returns:
        tuple: (should_generate, reason)
        - should_generate: bool indicating if title should be generated/updated
        - reason: string explaining the decision
    """
    try:
        # Get message count for this conversation
        response = supabase.table("messages") \
            .select("*", count="exact") \
            .eq("session_id", session_id) \
            .execute()
        
        message_count = response.count if hasattr(response, "count") else len(response.data or [])
        
        # Check if conversation has a title
        conv_response = supabase.table("conversations") \
            .select("title") \
            .eq("session_id", session_id) \
            .single() \
            .execute()
        
        has_title = conv_response.data and conv_response.data.get("title") is not None
        
        print(f"[DB_UTILS-TITLE_CHECK] Session {session_id}: {message_count} messages, has_title: {has_title}")
        
        # Skip if it's a simple greeting and no other messages exist
        if message_count <= 2 and is_simple_greeting(current_query):
            return False, "Simple greeting, waiting for substantive conversation"
        
        # Generate title for new conversations with substantive content
        if not has_title and not is_simple_greeting(current_query):
            return True, "New conversation with substantive content"
        
        # Update title after 3-4 human messages (6-8 total messages including AI responses)
        if message_count >= 6 and not has_title:
            return True, "Conversation developed enough for title generation"
        
        # Update title if conversation has grown significantly and current title might be outdated
        if has_title and message_count >= 10 and message_count % 8 == 0:
            return True, "Conversation grown significantly, updating title"
        
        return False, "No title generation needed"
        
    except Exception as e:
        print(f"[DB_UTILS-TITLE_CHECK] Error checking title status: {str(e)}")
        return False, "Error checking title status"


async def generate_conversation_summary(conversation_history: list) -> str:
    """Generate a summary of the conversation for better title generation"""
    human_messages = []
    ai_messages = []
    
    for msg in conversation_history:
        if msg.get("message") and msg["message"].get("type") == "human":
            content = msg["message"]["content"]
            if not is_simple_greeting(content):
                human_messages.append(content)
        elif msg.get("message") and msg["message"].get("type") == "ai":
            content = msg["message"]["content"]
            # Take first sentence of AI response for context
            first_sentence = content.split('.')[0] if content else ""
            if len(first_sentence) > 10:  # Meaningful content
                ai_messages.append(first_sentence)
    
    # Combine meaningful parts of the conversation
    summary_parts = []
    if human_messages:
        summary_parts.append("User asked about: " + "; ".join(human_messages[:3]))
    if ai_messages:
        summary_parts.append("Discussion included: " + "; ".join(ai_messages[:2]))
    
    return " | ".join(summary_parts) if summary_parts else "General conversation"
