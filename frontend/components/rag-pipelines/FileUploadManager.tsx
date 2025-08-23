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
    
    // Update file status to show it's waiting for processing
    setUploadQueue((prev) => 
      prev.map((item) => 
        item.file.name === file.name 
          ? { ...item, status: "processing" as const, googleDriveId }
          : item
      )
    );
    
    // The RAG pipeline will automatically detect and process the file
    // We'll track its progress through the pipeline status
  }, []);

  const handleFileRemove = useCallback((file: File) => {
    console.log(`[FILE-UPLOAD-MANAGER] Removing file from queue: ${file.name}`);
    setUploadQueue((prev) => prev.filter((item) => item.file.name !== file.name));
  }, []);

  // REMOVED: Polling is now handled by the RAGPipelineStatus component
  // This component no longer polls to avoid duplicate requests
  // The RAGPipelineStatus component below handles all status polling

  // Note: Processing status is now tracked by the RAGPipelineStatus component
  // Upload queue shows upload status only, not processing status
  const enrichedUploadQueue = uploadQueue;

  return (
    <div className="space-y-6">
      {/* File Dropzone */}
      <FileDropzone onFilesSelected={handleFilesSelected} />
      
      {/* Upload Queue */}
      <UploadQueue
        files={enrichedUploadQueue}
        onFileComplete={handleFileComplete}
        onFileRemove={handleFileRemove}
      />
      
      {/* RAG Pipeline Status - Shows real-time pipeline status */}
      <RAGPipelineStatus />
    </div>
  );
}