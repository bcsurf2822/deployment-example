"use client";

import FileUploadManager from "@/components/rag-pipelines/FileUploadManager";
import GoogleDriveSetupInstructions from "@/components/rag-pipelines/google-drive/SetupInstructions";

export default function RAGPipelinesPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">RAG Pipelines</h1>
        <p className="text-gray-600">
          Upload documents to Google Drive for processing through the RAG
          pipeline
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-1">
        {/* Google Drive Setup Instructions */}
        {/* <GoogleDriveSetupInstructions /> */}

        {/* File Upload Manager - Handles dropzone, upload queue, and processing status */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Document Processing
          </h2>
          <p className="text-sm text-gray-600 mb-6">
            Drag and drop files or click to browse. Files will be uploaded to Google Drive
            and automatically processed through the RAG pipeline for indexing.
          </p>
          <FileUploadManager />
        </div>

        {/* Indexed Documents Section */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Indexed Documents
          </h2>
          <div className="text-center py-12 text-gray-500">
            <svg
              className="mx-auto h-12 w-12 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <p className="text-sm">No indexed documents yet</p>
            <p className="text-xs text-gray-400 mt-2">
              Processed documents will appear here
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
