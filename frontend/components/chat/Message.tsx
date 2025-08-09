"use client";

import { Message as MessageType } from "@/lib/types/database";

interface MessageProps {
  message: MessageType;
}

function formatMarkdownToHtml(content: string): string {
  return content
    // Headers with emojis
    .replace(/^## (.*$)/gm, '<h2 class="text-lg font-bold mt-4 mb-2 text-blue-600">$1</h2>')
    .replace(/^### (.*$)/gm, '<h3 class="text-base font-semibold mt-3 mb-2 text-blue-500">$1</h3>')
    .replace(/^#### (.*$)/gm, '<h4 class="text-sm font-semibold mt-2 mb-1 text-blue-400">$1</h4>')
    
    // Bold and italic
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
    .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em class="italic">$1</em>')
    
    // Lists with proper nesting
    .replace(/^• (.*$)/gm, '<li class="flex items-start mb-1"><span class="text-blue-500 mr-2">•</span><span>$1</span></li>')
    .replace(/^◦ (.*$)/gm, '<li class="flex items-start mb-1 ml-4"><span class="text-blue-400 mr-2">◦</span><span>$1</span></li>')
    
    // Wrap consecutive list items in ul
    .replace(/(<li[^>]*>.*?<\/li>\n?)+/g, '<ul class="space-y-1 mb-3">$&</ul>')
    
    // Horizontal rule
    .replace(/---/g, '<hr class="my-4 border-gray-300">')
    
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
    
    // Line breaks
    .replace(/\n/g, '<br>');
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
        <div 
          className="text-sm break-words max-w-none prose prose-sm prose-blue"
          dangerouslySetInnerHTML={{
            __html: formatMarkdownToHtml(message.message.content)
          }}
          style={{
            lineHeight: '1.6',
          }}
        />
        <p className={`text-xs mt-2 ${
          isHuman ? "text-blue-100" : isError ? "text-red-500" : "text-gray-500"
        }`}>
          {new Date(message.created_at).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}