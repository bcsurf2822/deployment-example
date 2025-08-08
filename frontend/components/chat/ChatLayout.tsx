"use client";

import { useState, useEffect } from "react";
import { User } from "@supabase/supabase-js";
import { Message, FileAttachment } from "@/lib/types/database";
import { createClient } from "@/lib/supabase/client";
import MessageContainer from "./MessageContainer";
import ChatInput from "./ChatInput";
import ConversationsSidebar from "./ConversationsSidebar";
import { SidebarProvider } from "@/components/ui/sidebar";

export default function ChatLayout() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const supabase = createClient();
  
  // Import user from auth context
  const [user, setUser] = useState<User | null>(null);
  
  // Get user from auth and create session ID
  useEffect(() => {
    const getUser = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      
      if (user) {
        setUser(user);
        // Generate session_id in format: {user_id}~{random_string} to match existing conversations
        const randomSuffix = Math.random().toString(36).substring(2, 12);
        const sessionId = `${user.id}~${randomSuffix}`;
        setSessionId(sessionId);
        console.log("[ChatLayout-getUser] Session ID generated:", sessionId);
      }
    };

    getUser();
  }, [supabase]);

  const handleSendMessage = async (input: string, files?: FileAttachment[]) => {
    if ((!input.trim() && (!files || files.length === 0)) || !user || !sessionId) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}-user`,
      session_id: sessionId,
      computed_session_user_id: user.id,
      message: {
        type: "human",
        content: input.trim(),
        files: files,
      },
      message_data: null,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    console.log("[ChatLayout-handleSendMessage] Starting request");
    console.log("[ChatLayout-handleSendMessage] User ID:", user.id);
    console.log("[ChatLayout-handleSendMessage] Session ID:", sessionId);
    console.log("[ChatLayout-handleSendMessage] Query:", userMessage.message.content);
    console.log("[ChatLayout-handleSendMessage] Files count:", files?.length || 0);

    const requestBody = {
      query: userMessage.message.content,
      user_id: user.id,
      session_id: sessionId,
      files: files,
    };

    console.log("[ChatLayout-handleSendMessage] Request body:", JSON.stringify(requestBody, null, 2));

    try {
      console.log("[ChatLayout-handleSendMessage] Making fetch request to /api/chat");
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      console.log("[ChatLayout-handleSendMessage] Response status:", response.status);
      console.log("[ChatLayout-handleSendMessage] Response headers:", Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `API Error: ${response.status}`);
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body reader available");
      }

      // Create assistant message with empty content that we'll update
      const assistantMessageId = `temp-${Date.now()}-ai`;
      const assistantMessage: Message = {
        id: assistantMessageId,
        session_id: sessionId,
        computed_session_user_id: user.id,
        message: {
          type: "ai",
          content: "",
        },
        message_data: null,
        created_at: new Date().toISOString(),
      };

      // Add empty assistant message to show streaming is starting
      setMessages((prev) => [...prev, assistantMessage]);

      const decoder = new TextDecoder();
      let accumulatedText = "";

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            console.log("[ChatLayout-handleSendMessage] Stream complete");
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          console.log("[ChatLayout-handleSendMessage] Received chunk:", chunk);

          // Split chunk by newlines to handle multiple JSON objects
          const lines = chunk.split("\n").filter((line) => line.trim());

          for (const line of lines) {
            try {
              const data = JSON.parse(line);

              // Check if this is a completion signal
              if (data.complete === true) {
                console.log(
                  "[ChatLayout-handleSendMessage] Received completion signal"
                );
                break;
              }

              // Only update if text is not empty (to avoid clearing at the end)
              if (data.text !== undefined && data.text !== "") {
                accumulatedText = data.text;

                // Update the assistant message content in real-time
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? {
                          ...msg,
                          message: {
                            ...msg.message,
                            content: accumulatedText,
                          },
                        }
                      : msg
                  )
                );
              }
            } catch {
              console.warn(
                "[ChatLayout-handleSendMessage] Could not parse line as JSON:",
                line
              );
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (err) {
      console.error("[ChatLayout-handleSendMessage] Request failed:", err);
      setError(err instanceof Error ? err.message : "Failed to send message");

      // Add error message to chat
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        session_id: sessionId,
        computed_session_user_id: user?.id || null,
        message: {
          type: "ai",
          content: `Error: ${
            err instanceof Error ? err.message : "Unknown error occurred"
          }`,
        },
        message_data: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setError(null);
    // Generate new session ID for fresh conversation
    if (user) {
      const randomSuffix = Math.random().toString(36).substring(2, 12);
      const newSessionId = `${user.id}~${randomSuffix}`;
      setSessionId(newSessionId);
    }
  };

  const handleNewConversation = () => {
    handleClearChat();
  };

  const handleSelectConversation = (selectedSessionId: string) => {
    setSessionId(selectedSessionId);
    setMessages([]);
    setError(null);
    // TODO: Load messages for selected conversation from database
    console.log("[ChatLayout-handleSelectConversation] Selected session:", selectedSessionId);
  };

  return (
    <SidebarProvider>
      <div className="flex min-h-screen bg-background">
        <ConversationsSidebar 
          user={user}
          currentSessionId={sessionId}
          onNewConversation={handleNewConversation}
          onSelectConversation={handleSelectConversation}
        />
        
        <div className="flex-1 flex flex-col">
          {/* Chat Container */}
          <div className="flex-1 px-4 sm:px-6 lg:px-8 py-8">
        {/* Chat Header */}
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">AI Chat Assistant</h1>
          <button
            onClick={handleClearChat}
            className="bg-red-400 hover:bg-red-500 text-white px-4 py-2 rounded-lg transition-colors font-medium"
          >
            Clear Chat
          </button>
        </div>
            <div className="bg-white shadow-lg rounded-xl overflow-hidden border border-gray-200">
              {/* Messages Area */}
              <MessageContainer
                messages={messages}
                isLoading={isLoading}
                user={user}
                sessionId={sessionId}
              />

              {/* Input Area */}
              <ChatInput
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                error={error}
                user={user}
                sessionId={sessionId}
              />
            </div>

            {/* Debug Info */}
            <div className="mt-6 bg-gray-100 border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                Debug Information
              </h3>
              <div className="text-xs text-gray-600 space-y-1">
                <p>
                  <span className="font-medium">API URL:</span> /api/chat
                </p>
                <p>
                  <span className="font-medium">User ID:</span>{" "}
                  {user?.id || "Loading..."}
                </p>
                <p>
                  <span className="font-medium">Session ID:</span>{" "}
                  {sessionId ? (
                    <>
                      {sessionId}
                      {/* Langfuse link - uses NEXT_PUBLIC_LANGFUSE_HOST_WITH_PROJECT env var */}
                      {typeof window !== 'undefined' && process.env.NEXT_PUBLIC_LANGFUSE_HOST_WITH_PROJECT && (
                        <a
                          href={`${process.env.NEXT_PUBLIC_LANGFUSE_HOST_WITH_PROJECT}/sessions/${sessionId}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-blue-400 hover:text-blue-300 underline text-xs"
                        >
                          View in Langfuse →
                        </a>
                      )}
                    </>
                  ) : (
                    "Generating..."
                  )}
                </p>
                <p>
                  <span className="font-medium">Messages:</span>{" "}
                  {messages.length}
                </p>
                <p>
                  <span className="font-medium">Status:</span>{" "}
                  {isLoading ? "Loading..." : "Ready"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
}