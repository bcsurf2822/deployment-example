from dotenv import load_dotenv
from langfuse import Langfuse
import os

load_dotenv()

# Configure Langfuse for agent observability
def configure_langfuse():
    """
    Configure Langfuse for agent observability and tracing.
    
    Returns:
        Langfuse or None: A Langfuse client instance if configured, None otherwise
    """
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    # If Langfuse credentials are not provided, return None
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        print("Langfuse credentials not found. Tracing disabled.")
        return None
    
    # Initialize Langfuse client
    try:
        langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )
        print(f"Langfuse configured successfully with host: {LANGFUSE_HOST}")
        return langfuse_client
    except Exception as e:
        print(f"Failed to configure Langfuse: {e}")
        return None