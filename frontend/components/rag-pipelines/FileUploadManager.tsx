"use client";

import React, { useState, useCallback, useEffect } from "react";
import FileDropzone from "./FileDropzone";
import UploadQueue, { FileUploadStatus } from "./UploadQueue";
import RAGPipelineStatus from "./RAGPipelineStatus";

interface PipelineFile {
  name: string;
  id?: string;
  started_at: string;
  completed_at?: string;
}

interface PipelineStatus {
  files_processing: PipelineFile[];
  files_completed: PipelineFile[];
  files_failed: PipelineFile[];
}

export default function FileUploadManager() {
  const [uploadQueue, setUploadQueue] = useState<FileUploadStatus[]>([]);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);

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

  // Poll RAG pipeline status to track file processing
  useEffect(() => {
    const fetchPipelineStatus = async () => {
      try {
        const response = await fetch("/api/rag-status");
        if (response.ok) {
          const data = await response.json();
          if (!data.error) {
            setPipelineStatus(data);
            
            // Remove files that have completed processing from upload queue
            if (data.files_completed && data.files_completed.length > 0) {
              setUploadQueue((prev) => {
                return prev.filter((item) => {
                  // Check if this file is in the completed list
                  const isCompleted = data.files_completed.some((completed: PipelineFile) => 
                    completed.name === item.file.name
                  );
                  
                  if (isCompleted) {
                    console.log(`[FILE-UPLOAD-MANAGER] Removing completed file: ${item.file.name}`);
                  }
                  
                  return !isCompleted;
                });
              });
            }
          }
        }
      } catch (error) {
        console.error("[FILE-UPLOAD-MANAGER] Error fetching pipeline status:", error);
      }
    };

    // Poll every 2 seconds
    const interval = setInterval(fetchPipelineStatus, 2000);
    fetchPipelineStatus(); // Initial fetch

    return () => clearInterval(interval);
  }, []);

  // Update upload queue items to show current processing status
  const enrichedUploadQueue = uploadQueue.map((item) => {
    if (item.status === "processing" && pipelineStatus) {
      // Check if file is currently being processed
      const isProcessing = pipelineStatus.files_processing.some(
        (processing) => processing.name === item.file.name
      );
      
      if (isProcessing) {
        return { ...item, processingStep: "vectorizing" as const };
      }
      
      // Check if file failed processing
      const hasFailed = pipelineStatus.files_failed.some(
        (failed) => failed.name === item.file.name
      );
      
      if (hasFailed) {
        return { ...item, status: "error" as const, error: "Processing failed" };
      }
    }
    
    return item;
  });

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