"use client";

import { useEffect, useRef } from "react";
import { Message as MessageType } from "@/lib/types/database";
import { User } from "@supabase/supabase-js";
import Message from "./Message";

interface MessageContainerProps {
  messages: MessageType[];
  isLoading: boolean;
  user: User | null;
  sessionId: string;
}

export default function MessageContainer({
  messages,
  isLoading,
  user,
  sessionId,
}: MessageContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div ref={containerRef} className="h-96 overflow-y-auto p-6 space-y-4 bg-gray-50">
      {messages.length === 0 && (
        <div className="text-center text-gray-500 py-12">
          <p className="text-lg mb-2 font-semibold text-gray-700">Welcome to AI Chat</p>
          <p className="text-sm text-gray-600">
            Send a message to start a conversation with your AI assistant
          </p>
          <p className="text-xs mt-4 text-gray-500">
            API Endpoint: /api/chat
          </p>
          {user && (
            <p className="text-xs mt-1 text-gray-500">
              User: {user.email}
            </p>
          )}
          {sessionId && (
            <p className="text-xs mt-1 text-gray-500">
              Session: {sessionId}
            </p>
          )}
        </div>
      )}

      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}

      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-gray-100 border border-gray-300 text-gray-700 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
            <div className="flex items-center space-x-2">
              <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              <span className="text-sm">AI is thinking...</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Invisible element to maintain scroll position */}
      <div ref={bottomRef} />
    </div>
  );
}