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
    <div ref={containerRef} className="h-96 overflow-y-auto p-6 space-y-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-400 py-12">
          <p className="text-lg mb-2">Chat Test Interface</p>
          <p className="text-sm">
            Send a message to test your Pydantic agent API connection
          </p>
          <p className="text-xs mt-2 text-yellow-400">
            API: /api/chat
          </p>
          {user && (
            <p className="text-xs mt-1 text-green-400">
              User: {user.email}
            </p>
          )}
          {sessionId && (
            <p className="text-xs mt-1 text-purple-400">
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
          <div className="bg-purple-500/20 border border-purple-500/40 text-white max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
            <div className="flex items-center space-x-2">
              <div className="animate-spin w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full"></div>
              <span className="text-sm">Agent is thinking...</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Invisible element to maintain scroll position */}
      <div ref={bottomRef} />
    </div>
  );
}