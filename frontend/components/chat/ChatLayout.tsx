"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { User } from "@supabase/supabase-js";
import { Message, FileAttachment } from "@/lib/types/database";
import { createClient } from "@/lib/supabase/client";
import MessageContainer from "./MessageContainer";
import ChatInput from "./ChatInput";

export default function ChatLayout() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const router = useRouter();
  const supabase = createClient();

  // Get user and create session ID
  useEffect(() => {
    const getUser = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) {
        router.push("/auth/login");
        return;
      }

      setUser(user);
      // Generate session_id in format: {user_id}~{random_string} to match existing conversations
      const randomSuffix = Math.random().toString(36).substring(2, 12);
      const sessionId = `${user.id}~${randomSuffix}`;
      setSessionId(sessionId);
      console.log("[ChatLayout-getUser] Session ID generated:", sessionId);
    };

    getUser();
  }, [supabase, router]);

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

    console.log("[ChatLayout-handleSendMessage] Sending message with files:", files?.length || 0);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: userMessage.message.content,
          user_id: user.id,
          session_id: sessionId,
          files: files,
        }),
      });

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
            } catch (parseError) {
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
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-purple-950 to-black text-white">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-yellow-400/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl"></div>
      </div>

      {/* Navigation */}
      <nav className="relative border-b border-yellow-400/20 backdrop-blur-xl bg-black/20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push("/")}
                className="text-yellow-400 hover:text-yellow-300 transition-colors"
              >
                � Back to Dashboard
              </button>
              <h1 className="text-xl font-bold text-yellow-400">Chat Test</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleClearChat}
                className="bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 px-4 py-2 rounded-lg transition-all duration-300"
              >
                Clear Chat
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Chat Container */}
      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-black/40 backdrop-blur-xl border border-yellow-400/20 rounded-2xl overflow-hidden">
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
        <div className="mt-6 bg-black/20 backdrop-blur-xl border border-gray-600/20 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-2">
            Debug Information
          </h3>
          <div className="text-xs text-gray-400 space-y-1">
            <p>
              <span className="text-yellow-400">API URL:</span> /api/chat
            </p>
            <p>
              <span className="text-yellow-400">User ID:</span>{" "}
              {user?.id || "Loading..."}
            </p>
            <p>
              <span className="text-yellow-400">Session ID:</span>{" "}
              {sessionId || "Generating..."}
            </p>
            <p>
              <span className="text-yellow-400">Messages:</span>{" "}
              {messages.length}
            </p>
            <p>
              <span className="text-yellow-400">Status:</span>{" "}
              {isLoading ? "Loading..." : "Ready"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}