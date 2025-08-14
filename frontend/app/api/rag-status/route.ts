import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  // Determine the RAG pipeline status server URL based on environment
  // Try multiple possible URLs in order of preference
  const possibleUrls = [
    process.env.RAG_STATUS_URL,  // Custom env variable if set
    'http://rag-google-drive-dev:8003/status',  // Docker dev container
    'http://localhost:8003/status',  // Local development fallback
  ].filter(Boolean) as string[];

  if (process.env.NODE_ENV === 'production') {
    possibleUrls.unshift('http://rag-google-drive:8003/status');  // Production container
  }

  let lastError: Error | null = null;
  
  // Try each URL until one works
  for (const ragStatusUrl of possibleUrls) {
    try {
      console.log(`[RAG-STATUS-API] Attempting to fetch status from: ${ragStatusUrl}`);

      // Fetch status from the RAG pipeline status server
      const response = await fetch(ragStatusUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Don't cache this request
        cache: 'no-store',
        // Short timeout since we poll frequently
        signal: AbortSignal.timeout(3000),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Add server timestamp for client-side sync
        data.serverTime = new Date().toISOString();
        
        console.log(`[RAG-STATUS-API] Successfully fetched status from: ${ragStatusUrl}`);
        return NextResponse.json(data);
      }
      
      lastError = new Error(`Server returned status ${response.status}`);
    } catch (error) {
      lastError = error as Error;
      console.log(`[RAG-STATUS-API] Failed to fetch from ${ragStatusUrl}:`, error);
      // Continue to next URL
    }
  }

  // All URLs failed
  console.error("[RAG-STATUS-API] All RAG pipeline URLs failed:", lastError);
  
  // Return appropriate error response
  if (lastError) {
    if (lastError.name === 'AbortError') {
      return NextResponse.json(
        { 
          error: "Request timeout",
          status: "offline",
          message: "RAG pipeline is not responding"
        },
        { status: 504 }
      );
    }
    
    if (lastError.message.includes('fetch failed') || lastError.message.includes('ECONNREFUSED')) {
      return NextResponse.json(
        { 
          error: "Connection failed",
          status: "offline",
          message: "RAG pipeline is offline or not accessible"
        },
        { status: 503 }
      );
    }
  }
  
  return NextResponse.json(
    { 
      error: "Service unavailable",
      status: "offline",
      message: "Could not connect to RAG pipeline status server"
    },
    { status: 503 }
  );
}

// Handle CORS preflight
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}