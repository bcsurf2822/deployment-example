import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Get the authenticated user
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { query, session_id, files } = body;

    if (!query || !session_id) {
      return NextResponse.json(
        { error: "Missing query or session_id" },
        { status: 400 }
      );
    }

    // Ensure conversation exists
    const { error: conversationError } = await supabase
      .from("conversations")
      .select("session_id")
      .eq("session_id", session_id)
      .single();

    if (conversationError && conversationError.code === "PGRST116") {
      // Conversation doesn't exist, create it
      const { error: insertError } = await supabase
        .from("conversations")
        .insert({
          session_id: session_id,
          user_id: user.id,
          title: null, // Will be auto-generated
          metadata: {},
        });

      if (insertError) {
        console.error("[API-CHAT] Error creating conversation:", insertError);
        return NextResponse.json(
          { error: `Failed to create conversation: ${insertError.message}` },
          { status: 500 }
        );
      }
      console.log("[API-CHAT] Conversation created:", session_id);
    } else if (conversationError) {
      console.error(
        "[API-CHAT] Error checking conversation:",
        conversationError
      );
      return NextResponse.json(
        { error: `Database error: ${conversationError.message}` },
        { status: 500 }
      );
    }

    // Get the user's session/token for authentication
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      return NextResponse.json(
        { error: "No valid session token" },
        { status: 401 }
      );
    }

    console.log("[API-CHAT] Token prefix:", session.access_token.substring(0, 20) + "...");

    // Forward the request to the Pydantic agent API
    // Use internal Docker service name if available, otherwise fallback to public URL
    const apiUrl =
      process.env.PYDANTIC_AGENT_API_URL ||
      process.env.NEXT_PUBLIC_PYDANTIC_AGENT_API_URL ||
      "http://localhost:8001/api/pydantic-agent";

    const requestId = `req_${Date.now()}_${Math.random()
      .toString(36)
      .substring(2, 9)}`;

    const payload = {
      query: query,
      user_id: user.id,
      request_id: requestId,
      session_id: session_id,
      ...(files && { files: files }),
    };

    console.log("[API-CHAT] Sending request to:", apiUrl);
    console.log("[API-CHAT] Payload:", payload);

    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(payload),
    });

    console.log("[API-CHAT] Response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("[API-CHAT] Error response:", errorText);
      return NextResponse.json(
        { error: `API Error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    // Return the streaming response
    return new NextResponse(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("[API-CHAT] Unexpected error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
