// "use client";

// import React, { useState, useCallback, useRef } from "react";

// interface DragDropProps {
//   onFilesSelected?: (files: File[]) => void;
//   maxFileSize?: number; // in bytes
//   acceptedFileTypes?: string[];
//   maxFiles?: number;
// }

// export default function DragDrop({
//   onFilesSelected,
//   maxFileSize = 10 * 1024 * 1024, // 10MB default
//   acceptedFileTypes = [".pdf", ".txt", ".doc", ".docx", ".csv", ".xlsx", ".md"],
//   maxFiles = 10,
// }: DragDropProps) {
//   const [isDragging, setIsDragging] = useState(false);
//   const [files, setFiles] = useState<File[]>([]);
//   const [uploadStatus, setUploadStatus] = useState<{
//     [key: string]: {
//       status: "pending" | "uploading" | "success" | "error";
//       progress?: number;
//       error?: string;
//       googleDriveId?: string;
//     };
//   }>({});
//   const fileInputRef = useRef<HTMLInputElement>(null);
//   const dragCounter = useRef(0);

//   const validateFile = (file: File): string | null => {
//     // Check file size
//     if (file.size > maxFileSize) {
//       return `File size exceeds ${maxFileSize / (1024 * 1024)}MB limit`;
//     }

//     // Check file type
//     const fileExtension = `.${file.name.split(".").pop()?.toLowerCase()}`;
//     if (
//       !acceptedFileTypes.some((type) => fileExtension === type.toLowerCase())
//     ) {
//       return `File type ${fileExtension} is not supported`;
//     }

//     return null;
//   };

//   const handleFiles = useCallback(
//     (newFiles: FileList | null) => {
//       if (!newFiles) return;

//       const fileArray = Array.from(newFiles);
//       const validFiles: File[] = [];
//       const newUploadStatus: typeof uploadStatus = {};

//       // Check max files limit
//       if (files.length + fileArray.length > maxFiles) {
//         alert(`Maximum ${maxFiles} files allowed`);
//         return;
//       }

//       fileArray.forEach((file) => {
//         const error = validateFile(file);
//         if (error) {
//           newUploadStatus[file.name] = { status: "error", error };
//         } else {
//           validFiles.push(file);
//           newUploadStatus[file.name] = { status: "pending" };
//         }
//       });

//       if (validFiles.length > 0) {
//         setFiles((prev) => [...prev, ...validFiles]);
//         setUploadStatus((prev) => ({ ...prev, ...newUploadStatus }));
//         onFilesSelected?.(validFiles);

//         // Start uploading files
//         validFiles.forEach((file) => uploadToGoogleDrive(file));
//       }
//     },
//     // eslint-disable-next-line react-hooks/exhaustive-deps
//     [files.length, maxFiles, onFilesSelected, acceptedFileTypes, maxFileSize]
//   );

//   const uploadToGoogleDrive = async (file: File) => {
//     // Set initial uploading status with progress animation
//     setUploadStatus((prev) => ({
//       ...prev,
//       [file.name]: { status: "uploading", progress: 0 },
//     }));

//     // Simulate progress updates while uploading
//     const progressInterval = setInterval(() => {
//       setUploadStatus((prev) => {
//         const current = prev[file.name];
//         if (current?.status === "uploading" && (current.progress || 0) < 90) {
//           return {
//             ...prev,
//             [file.name]: {
//               ...current,
//               progress: Math.min((current.progress || 0) + 10, 90),
//             },
//           };
//         }
//         return prev;
//       });
//     }, 200);

//     try {
//       const formData = new FormData();
//       formData.append("file", file);

//       console.log(`[DRAGDROP] Starting upload for ${file.name}`);
//       const response = await fetch("/api/google-drive/upload", {
//         method: "POST",
//         body: formData,
//       });

//       clearInterval(progressInterval);

//       if (!response.ok) {
//         const errorData = await response.json();
//         throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
//       }

//       const result = await response.json();
//       console.log(`[DRAGDROP] Upload successful for ${file.name}:`, result);

//       // Mark as success
//       setUploadStatus((prev) => ({
//         ...prev,
//         [file.name]: { 
//           status: "success", 
//           progress: 100,
//           googleDriveId: result.file?.googleDriveId 
//         },
//       }));

//       // After 2 seconds, remove from upload queue
//       setTimeout(() => {
//         setFiles((prevFiles) => prevFiles.filter((f) => f.name !== file.name));
//         setUploadStatus((prev) => {
//           const newStatus = { ...prev };
//           delete newStatus[file.name];
//           return newStatus;
//         });
//       }, 2000);

//     } catch (error) {
//       clearInterval(progressInterval);
//       console.error(`[DRAGDROP] Upload failed for ${file.name}:`, error);
//       setUploadStatus((prev) => ({
//         ...prev,
//         [file.name]: {
//           status: "error",
//           error: error instanceof Error ? error.message : "Upload failed",
//         },
//       }));
//     }
//   };

//   const handleDragEnter = (e: React.DragEvent) => {
//     e.preventDefault();
//     e.stopPropagation();
//     dragCounter.current++;
//     if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
//       setIsDragging(true);
//     }
//   };

//   const handleDragLeave = (e: React.DragEvent) => {
//     e.preventDefault();
//     e.stopPropagation();
//     dragCounter.current--;
//     if (dragCounter.current === 0) {
//       setIsDragging(false);
//     }
//   };

//   const handleDragOver = (e: React.DragEvent) => {
//     e.preventDefault();
//     e.stopPropagation();
//   };

//   const handleDrop = (e: React.DragEvent) => {
//     e.preventDefault();
//     e.stopPropagation();
//     setIsDragging(false);
//     dragCounter.current = 0;
//     handleFiles(e.dataTransfer.files);
//   };

//   const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
//     handleFiles(e.target.files);
//   };

//   const removeFile = (index: number) => {
//     setFiles((prev) => prev.filter((_, i) => i !== index));
//   };

//   const formatFileSize = (bytes: number): string => {
//     if (bytes < 1024) return bytes + " bytes";
//     if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
//     return (bytes / (1024 * 1024)).toFixed(1) + " MB";
//   };

//   return (
//     <div className="w-full">
//       <div
//         className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
//           isDragging
//             ? "border-blue-500 bg-blue-50"
//             : "border-gray-300 hover:border-gray-400"
//         }`}
//         onDragEnter={handleDragEnter}
//         onDragLeave={handleDragLeave}
//         onDragOver={handleDragOver}
//         onDrop={handleDrop}
//       >
//         <input
//           ref={fileInputRef}
//           type="file"
//           multiple
//           accept={acceptedFileTypes.join(",")}
//           onChange={handleFileSelect}
//           className="hidden"
//         />

//         <div className="space-y-4">
//           <div className="flex justify-center">
//             <svg
//               className={`w-12 h-12 ${
//                 isDragging ? "text-blue-500" : "text-gray-400"
//               }`}
//               fill="none"
//               stroke="currentColor"
//               viewBox="0 0 24 24"
//             >
//               <path
//                 strokeLinecap="round"
//                 strokeLinejoin="round"
//                 strokeWidth={2}
//                 d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
//               />
//             </svg>
//           </div>

//           <div>
//             <p className="text-lg font-medium text-gray-900">
//               {isDragging ? "Drop files here" : "Drag and drop files here"}
//             </p>
//             <p className="text-sm text-gray-500 mt-1">or</p>
//             <button
//               onClick={() => fileInputRef.current?.click()}
//               className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
//             >
//               Browse Files
//             </button>
//           </div>

//           <p className="text-xs text-gray-500">
//             Supported formats: {acceptedFileTypes.join(", ")} &nbsp; Max size:{" "}
//             {maxFileSize / (1024 * 1024)}MB &nbsp; Max files: {maxFiles}
//           </p>
//         </div>
//       </div>

//       {/* File List */}
//       {files.length > 0 && (
//         <div className="mt-6 space-y-2">
//           <h3 className="text-sm font-medium text-gray-900">
//             Upload Queue
//           </h3>
//           <ul className="space-y-2">
//             {files.map((file, index) => {
//               const status = uploadStatus[file.name];
//               return (
//                 <li
//                   key={`${file.name}-${index}`}
//                   className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
//                 >
//                   <div className="flex items-center space-x-3 flex-1">
//                     <div className="flex-shrink-0">
//                       {status?.status === "uploading" && (
//                         <svg
//                           className="animate-spin h-5 w-5 text-blue-500"
//                           fill="none"
//                           viewBox="0 0 24 24"
//                         >
//                           <circle
//                             className="opacity-25"
//                             cx="12"
//                             cy="12"
//                             r="10"
//                             stroke="currentColor"
//                             strokeWidth="4"
//                           />
//                           <path
//                             className="opacity-75"
//                             fill="currentColor"
//                             d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
//                           />
//                         </svg>
//                       )}
//                       {status?.status === "success" && (
//                         <svg
//                           className="h-5 w-5 text-green-500"
//                           fill="currentColor"
//                           viewBox="0 0 20 20"
//                         >
//                           <path
//                             fillRule="evenodd"
//                             d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
//                             clipRule="evenodd"
//                           />
//                         </svg>
//                       )}
//                       {status?.status === "error" && (
//                         <svg
//                           className="h-5 w-5 text-red-500"
//                           fill="currentColor"
//                           viewBox="0 0 20 20"
//                         >
//                           <path
//                             fillRule="evenodd"
//                             d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
//                             clipRule="evenodd"
//                           />
//                         </svg>
//                       )}
//                       {status?.status === "pending" && (
//                         <svg
//                           className="h-5 w-5 text-gray-400"
//                           fill="currentColor"
//                           viewBox="0 0 20 20"
//                         >
//                           <path
//                             fillRule="evenodd"
//                             d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
//                             clipRule="evenodd"
//                           />
//                         </svg>
//                       )}
//                     </div>
//                     <div className="flex-1 min-w-0">
//                       <p className="text-sm font-medium text-gray-900 truncate">
//                         {file.name}
//                       </p>
//                       <p className="text-sm text-gray-500">
//                         {formatFileSize(file.size)}
//                         {status?.status === "uploading" &&
//                           status.progress !== undefined && (
//                             <span className="ml-2">Uploading... {status.progress}%</span>
//                           )}
//                         {status?.status === "success" && (
//                           <span className="ml-2 text-green-500">
//                             Upload complete!
//                           </span>
//                         )}
//                         {status?.status === "error" && status.error && (
//                           <span className="ml-2 text-red-500">
//                             {status.error}
//                           </span>
//                         )}
//                       </p>
//                     </div>
//                   </div>
//                   {status?.status !== "uploading" && 
//                    status?.status !== "success" && (
//                     <button
//                       onClick={() => removeFile(index)}
//                       className="ml-4 text-gray-400 hover:text-gray-500"
//                     >
//                       <svg
//                         className="h-5 w-5"
//                         fill="currentColor"
//                         viewBox="0 0 20 20"
//                       >
//                         <path
//                           fillRule="evenodd"
//                           d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
//                           clipRule="evenodd"
//                         />
//                       </svg>
//                     </button>
//                   )}
//                   {status?.status === "uploading" && (
//                     <div className="ml-4 w-24">
//                       <div className="bg-gray-200 rounded-full h-2">
//                         <div
//                           className="bg-blue-500 h-2 rounded-full transition-all"
//                           style={{ width: `${status.progress || 0}%` }}
//                         />
//                       </div>
//                     </div>
//                   )}
//                 </li>
//               );
//             })}
//           </ul>
//         </div>
//       )}
//     </div>
//   );
// }
