"use client";

import React, { useState, useCallback } from "react";
import FileDropzone from "./FileDropzone";
import UploadQueue, { FileUploadStatus } from "./UploadQueue";
import ProcessingStatus, { ProcessingFile } from "./ProcessingStatus";

export default function FileUploadManager() {
  const [uploadQueue, setUploadQueue] = useState<FileUploadStatus[]>([]);
  const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([]);

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
    
    // Add to processing status
    const processingFile: ProcessingFile = {
      fileName: file.name,
      googleDriveId,
      status: "processing",
      startedAt: new Date(),
    };
    
    setProcessingFiles((prev) => [...prev, processingFile]);
    
    // TODO: Here you would typically poll the RAG pipeline status
    // For now, we'll simulate processing completion after 10 seconds
    setTimeout(() => {
      setProcessingFiles((prev) =>
        prev.map((pf) =>
          pf.googleDriveId === googleDriveId
            ? { ...pf, status: "completed" as const, completedAt: new Date() }
            : pf
        )
      );
    }, 10000);
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
      
      {/* Processing Status */}
      <ProcessingStatus files={processingFiles} />
    </div>
  );
}