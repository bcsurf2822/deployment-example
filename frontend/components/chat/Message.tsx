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
        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
          isHuman
            ? "bg-blue-600 text-white"
            : isError
            ? "bg-red-50 border border-red-200 text-red-700"
            : "bg-white border border-gray-200 text-gray-800 shadow-sm"
        }`}
      >
        <p className="text-sm break-words whitespace-pre-wrap">{message.message.content}</p>
        <p className={`text-xs mt-2 ${
          isHuman ? "text-blue-100" : isError ? "text-red-500" : "text-gray-500"
        }`}>
          {new Date(message.created_at).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}