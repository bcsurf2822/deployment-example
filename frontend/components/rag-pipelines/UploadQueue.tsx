"use client";

import React, { useState, useEffect } from "react";

export interface FileUploadStatus {
  file: File;
  status: "pending" | "uploading" | "success" | "error";
  progress?: number;
  error?: string;
  googleDriveId?: string;
}

interface UploadQueueProps {
  files: FileUploadStatus[];
  onFileComplete?: (file: File, googleDriveId: string) => void;
  onFileRemove?: (file: File) => void;
}

export default function UploadQueue({
  files,
  onFileComplete,
  onFileRemove,
}: UploadQueueProps) {
  const [uploadStatuses, setUploadStatuses] = useState<FileUploadStatus[]>([]);

  useEffect(() => {
    setUploadStatuses(files);
  }, [files]);

  useEffect(() => {
    // Start uploading pending files
    uploadStatuses.forEach((fileStatus) => {
      if (fileStatus.status === "pending") {
        uploadToGoogleDrive(fileStatus);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uploadStatuses.length]);

  const uploadToGoogleDrive = async (fileStatus: FileUploadStatus) => {
    const { file } = fileStatus;
    
    // Update to uploading status
    updateFileStatus(file, { status: "uploading", progress: 0 });

    // Simulate progress updates while uploading
    const progressInterval = setInterval(() => {
      setUploadStatuses((prev) => {
        const current = prev.find((fs) => fs.file.name === file.name);
        if (current?.status === "uploading" && (current.progress || 0) < 90) {
          return prev.map((fs) =>
            fs.file.name === file.name
              ? { ...fs, progress: Math.min((fs.progress || 0) + 10, 90) }
              : fs
          );
        }
        return prev;
      });
    }, 200);

    try {
      const formData = new FormData();
      formData.append("file", file);

      console.log(`[UPLOAD-QUEUE] Starting upload for ${file.name}`);
      const response = await fetch("/api/google-drive/upload", {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      console.log(`[UPLOAD-QUEUE] Upload successful for ${file.name}:`, result);

      // Mark as success
      updateFileStatus(file, {
        status: "success",
        progress: 100,
        googleDriveId: result.file?.googleDriveId,
      });

      // Notify parent and remove after 2 seconds
      if (onFileComplete && result.file?.googleDriveId) {
        setTimeout(() => {
          onFileComplete(file, result.file.googleDriveId);
        }, 2000);
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error(`[UPLOAD-QUEUE] Upload failed for ${file.name}:`, error);
      updateFileStatus(file, {
        status: "error",
        error: error instanceof Error ? error.message : "Upload failed",
      });
    }
  };

  const updateFileStatus = (
    file: File,
    updates: Partial<FileUploadStatus>
  ) => {
    setUploadStatuses((prev) =>
      prev.map((fs) =>
        fs.file.name === file.name ? { ...fs, ...updates } : fs
      )
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + " bytes";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  if (uploadStatuses.length === 0) {
    return null;
  }

  return (
    <div className="mt-6 space-y-2">
      <h3 className="text-sm font-medium text-gray-900">Upload Queue</h3>
      <ul className="space-y-2">
        {uploadStatuses.map((fileStatus, index) => (
          <li
            key={`${fileStatus.file.name}-${index}`}
            className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
          >
            <div className="flex items-center space-x-3 flex-1">
              <div className="flex-shrink-0">
                {fileStatus.status === "uploading" && (
                  <svg
                    className="animate-spin h-5 w-5 text-blue-500"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                )}
                {fileStatus.status === "success" && (
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
                {fileStatus.status === "error" && (
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
                {fileStatus.status === "pending" && (
                  <svg
                    className="h-5 w-5 text-gray-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {fileStatus.file.name}
                </p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(fileStatus.file.size)}
                  {fileStatus.status === "uploading" &&
                    fileStatus.progress !== undefined && (
                      <span className="ml-2">
                        Uploading... {fileStatus.progress}%
                      </span>
                    )}
                  {fileStatus.status === "success" && (
                    <span className="ml-2 text-green-500">Upload complete!</span>
                  )}
                  {fileStatus.status === "error" && fileStatus.error && (
                    <span className="ml-2 text-red-500">{fileStatus.error}</span>
                  )}
                </p>
              </div>
            </div>
            {fileStatus.status !== "uploading" &&
              fileStatus.status !== "success" && (
                <button
                  onClick={() => onFileRemove?.(fileStatus.file)}
                  className="ml-4 text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              )}
            {fileStatus.status === "uploading" && (
              <div className="ml-4 w-24">
                <div className="bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: `${fileStatus.progress || 0}%` }}
                  />
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}