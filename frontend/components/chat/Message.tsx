"use client";

import { Message as MessageType } from "@/lib/types/database";

interface MessageProps {
  message: MessageType;
}

export default function Message({ message }: MessageProps) {
  const isHuman = message.message.type === "human";
  const isError = message.message.content.startsWith("Error:");

  return (
    <div className={`flex ${isHuman ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isHuman
            ? "bg-gradient-to-r from-yellow-400 to-yellow-600 text-black"
            : isError
            ? "bg-red-500/20 border border-red-500/40 text-red-300"
            : "bg-purple-500/20 border border-purple-500/40 text-white"
        }`}
      >
        <p className="text-sm break-words whitespace-pre-wrap">{message.message.content}</p>
        <p className="text-xs opacity-70 mt-1">
          {new Date(message.created_at).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}