"use client";

import { useState, useRef } from "react";
import { User } from "@supabase/supabase-js";
import { FileAttachment } from "@/lib/types/database";

interface ChatInputProps {
  onSendMessage: (message: string, files?: FileAttachment[]) => void;
  isLoading: boolean;
  error: string | null;
  user: User | null;
  sessionId: string;
}

export default function ChatInput({
  onSendMessage,
  isLoading,
  error,
  user,
  sessionId,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<FileAttachment[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB in bytes
  const MAX_FILES = 3;

  const handleSubmit = () => {
    if ((!input.trim() && attachedFiles.length === 0) || isLoading || !user || !sessionId) return;
    onSendMessage(input, attachedFiles.length > 0 ? attachedFiles : undefined);
    setInput("");
    setAttachedFiles([]);
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setFileError(null);
    
    // Check if adding these files would exceed the maximum
    if (attachedFiles.length + files.length > MAX_FILES) {
      setFileError(`Maximum ${MAX_FILES} files allowed. You currently have ${attachedFiles.length} files.`);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }
    
    // Validate each file
    for (const file of files) {
      if (file.size > MAX_FILE_SIZE) {
        setFileError(`File "${file.name}" is too large. Maximum size is 5MB.`);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }
    }
    
    // Process valid files
    for (const file of files) {
      const reader = new FileReader();
      reader.onload = () => {
        const base64Content = reader.result as string;
        const base64Data = base64Content.split(',')[1]; // Remove data:type;base64, prefix
        
        const attachment: FileAttachment = {
          fileName: file.name,
          content: base64Data,
          mimeType: file.type,
        };
        
        setAttachedFiles(prev => [...prev, attachment]);
      };
      reader.readAsDataURL(file);
    }
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
    setFileError(null); // Clear error when removing files
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-yellow-400/20 p-4">
      {/* File attachments display */}
      {attachedFiles.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachedFiles.map((file, index) => (
            <div key={index} className="flex items-center bg-gray-700/80 border border-gray-600 rounded-full px-3 py-2 space-x-2">
              <div className="w-4 h-4 text-gray-300">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span className="text-white text-sm font-medium truncate max-w-32">{file.fileName}</span>
              <button
                onClick={() => removeFile(index)}
                className="text-gray-400 hover:text-white transition-colors p-0.5"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex space-x-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={user ? "Type your message..." : "Loading user..."}
          disabled={isLoading || !user || !sessionId}
          className="flex-1 px-4 py-3 bg-black/40 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-yellow-400 focus:ring-1 focus:ring-yellow-400/50 transition-all duration-300 disabled:opacity-50"
        />
        
        {/* File attachment button */}
        <button
          onClick={handleFileSelect}
          disabled={isLoading || !user || !sessionId || attachedFiles.length >= MAX_FILES}
          className="px-3 py-3 bg-black/40 border border-gray-600 rounded-lg text-gray-400 hover:text-yellow-400 hover:border-yellow-400 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          title={attachedFiles.length >= MAX_FILES ? `Maximum ${MAX_FILES} files allowed` : "Attach files"}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>

        <button
          onClick={handleSubmit}
          disabled={isLoading || (!input.trim() && attachedFiles.length === 0) || !user || !sessionId}
          className="bg-gradient-to-r from-yellow-400 to-yellow-600 hover:from-yellow-300 hover:to-yellow-500 text-black font-semibold px-6 py-3 rounded-lg transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg shadow-yellow-400/25"
        >
          Send
        </button>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileChange}
        className="hidden"
        accept="image/*,application/pdf,.txt,.doc,.docx,.csv,.json"
      />

      {/* File validation error */}
      {fileError && (
        <div className="mt-3 bg-red-500/20 border border-red-500/40 text-red-300 px-4 py-2 rounded-lg text-sm">
          {fileError}
        </div>
      )}

      {error && (
        <div className="mt-3 bg-red-500/20 border border-red-500/40 text-red-300 px-4 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}
    </div>
  );
}