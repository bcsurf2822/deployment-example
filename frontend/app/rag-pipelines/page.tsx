"use client";

import DragDrop from "@/components/rag-pipelines/DragDrop";

export default function RAGPipelinesPage() {
  const handleFilesSelected = (files: File[]) => {
    console.log("[RAG-PIPELINES-PAGE] Files selected:", files.map(f => f.name));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">RAG Pipelines</h1>
        <p className="text-gray-600">
          Upload documents to Google Drive for processing through the RAG pipeline
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-1">
        {/* Upload Section */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Upload Documents
          </h2>
          <p className="text-sm text-gray-600 mb-6">
            Drag and drop files or click to browse. Uploaded files will be
            automatically processed and indexed for retrieval.
          </p>
          <DragDrop onFilesSelected={handleFilesSelected} />
        </div>

        {/* Processing Status Section */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Processing Status
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="text-sm">No documents processing</p>
            <p className="text-xs text-gray-400 mt-2">
              Upload documents to start processing
            </p>
          </div>
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