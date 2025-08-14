"use client";

import React from "react";

export interface ProcessingFile {
  fileName: string;
  googleDriveId: string;
  status: "processing" | "completed" | "failed";
  progress?: number;
  error?: string;
  startedAt: Date;
  completedAt?: Date;
}

interface ProcessingStatusProps {
  files: ProcessingFile[];
}

export default function ProcessingStatus({ files }: ProcessingStatusProps) {
  const formatTime = (date: Date): string => {
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(date);
  };

  const getElapsedTime = (startedAt: Date, completedAt?: Date): string => {
    const end = completedAt || new Date();
    const elapsed = Math.floor((end.getTime() - startedAt.getTime()) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <div className="mt-6 space-y-2">
      <h3 className="text-sm font-medium text-gray-900">Processing Status</h3>
      <ul className="space-y-2">
        {files.map((file, index) => (
          <li
            key={`${file.googleDriveId}-${index}`}
            className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
          >
            <div className="flex items-center space-x-3 flex-1">
              <div className="flex-shrink-0">
                {file.status === "processing" && (
                  <svg
                    className="animate-pulse h-5 w-5 text-purple-500"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
                {file.status === "completed" && (
                  <svg
                    className="h-5 w-5 text-green-500"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
                {file.status === "failed" && (
                  <svg
                    className="h-5 w-5 text-red-500"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {file.fileName}
                </p>
                <p className="text-sm text-gray-500">
                  {file.status === "processing" && (
                    <span className="text-purple-500">
                      Processing in RAG pipeline...{" "}
                      {file.progress && `(${file.progress}%)`}
                    </span>
                  )}
                  {file.status === "completed" && (
                    <span className="text-green-500">
                      Completed in {getElapsedTime(file.startedAt, file.completedAt)}
                    </span>
                  )}
                  {file.status === "failed" && (
                    <span className="text-red-500">
                      {file.error || "Processing failed"}
                    </span>
                  )}
                </p>
              </div>
              <div className="text-xs text-gray-400">
                {formatTime(file.startedAt)}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}