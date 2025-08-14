"use client";

import React, { useState, useCallback } from "react";
import FileDropzone from "./FileDropzone";
import UploadQueue, { FileUploadStatus } from "./UploadQueue";
import RAGPipelineStatus from "./RAGPipelineStatus";

export default function FileUploadManager() {
  const [uploadQueue, setUploadQueue] = useState<FileUploadStatus[]>([]);

  const handleFilesSelected = useCallback((files: File[]) => {
    console.log(`[FILE-UPLOAD-MANAGER] Adding ${files.length} files to upload queue`);
    
    // Add files to upload queue with pending status
    const newUploadItems: FileUploadStatus[] = files.map((file) => ({
      file,
      status: "pending" as const,
    }));
    
    setUploadQueue((prev) => [...prev, ...newUploadItems]);
  }, []);

  const handleFileComplete = useCallback((file: File, googleDriveId: string) => {
    console.log(`[FILE-UPLOAD-MANAGER] File upload complete: ${file.name} (${googleDriveId})`);
    
    // Remove from upload queue
    setUploadQueue((prev) => prev.filter((item) => item.file.name !== file.name));
    
    // The RAG pipeline will automatically detect and process the file
    // The RAGPipelineStatus component will show it in processing
  }, []);

  const handleFileRemove = useCallback((file: File) => {
    console.log(`[FILE-UPLOAD-MANAGER] Removing file from queue: ${file.name}`);
    setUploadQueue((prev) => prev.filter((item) => item.file.name !== file.name));
  }, []);

  return (
    <div className="space-y-6">
      {/* File Dropzone */}
      <FileDropzone onFilesSelected={handleFilesSelected} />
      
      {/* Upload Queue */}
      <UploadQueue
        files={uploadQueue}
        onFileComplete={handleFileComplete}
        onFileRemove={handleFileRemove}
      />
      
      {/* RAG Pipeline Status - Shows real-time pipeline status */}
      <RAGPipelineStatus />
    </div>
  );
}