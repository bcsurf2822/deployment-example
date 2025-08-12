// Server-only Google Drive service using @googleapis/drive
import { drive_v3 } from '@googleapis/drive';
import { JWT } from 'google-auth-library';
import * as fs from 'fs';

// Scopes for Google Drive API (matching RAG pipeline scopes)
const SCOPES = [
  'https://www.googleapis.com/auth/drive.file',
  'https://www.googleapis.com/auth/drive',
];

// Initialize Google Drive client with service account authentication
function createDriveClient(): drive_v3.Drive {
  console.log('[GOOGLE-DRIVE-SERVICE] Starting authentication...');
  
  const serviceAccountJson = process.env.GOOGLE_DRIVE_CREDENTIALS_JSON;
  console.log(`[GOOGLE-DRIVE-SERVICE] GOOGLE_DRIVE_CREDENTIALS_JSON environment variable: ${serviceAccountJson}`);
  
  if (!serviceAccountJson) {
    throw new Error('[GOOGLE-DRIVE-SERVICE] Google Drive credentials not configured. Please set GOOGLE_DRIVE_CREDENTIALS_JSON environment variable.');
  }

  console.log(`[GOOGLE-DRIVE-SERVICE] Found service account JSON path: ${serviceAccountJson}`);
  
  let serviceAccountInfo: any;
  
  // Check if it's a file path or JSON content (following RAG pipeline approach)
  if (serviceAccountJson.startsWith('{')) {
    // It's JSON content directly
    console.log('[GOOGLE-DRIVE-SERVICE] Environment variable contains JSON content directly');
    try {
      serviceAccountInfo = JSON.parse(serviceAccountJson);
      console.log(`[GOOGLE-DRIVE-SERVICE] Parsed JSON keys: ${Object.keys(serviceAccountInfo)}`);
      console.log(`[GOOGLE-DRIVE-SERVICE] Service account email: ${serviceAccountInfo.client_email || 'NOT_FOUND'}`);
    } catch (e) {
      console.error(`[GOOGLE-DRIVE-SERVICE] Error parsing JSON content: ${e}`);
      throw new Error(`[GOOGLE-DRIVE-SERVICE] Invalid service account credentials in environment variable: ${e}`);
    }
  } else {
    // It's a file path
    console.log(`[GOOGLE-DRIVE-SERVICE] Environment variable contains file path: ${serviceAccountJson}`);
    console.log(`[GOOGLE-DRIVE-SERVICE] File exists: ${fs.existsSync(serviceAccountJson)}`);
    
    if (fs.existsSync(serviceAccountJson)) {
      try {
        const credentialsContent = fs.readFileSync(serviceAccountJson, 'utf8');
        serviceAccountInfo = JSON.parse(credentialsContent);
        console.log(`[GOOGLE-DRIVE-SERVICE] Loaded JSON from file, keys: ${Object.keys(serviceAccountInfo)}`);
        console.log(`[GOOGLE-DRIVE-SERVICE] Service account email: ${serviceAccountInfo.client_email || 'NOT_FOUND'}`);
      } catch (e) {
        console.error(`[GOOGLE-DRIVE-SERVICE] Error loading JSON from file: ${e}`);
        throw new Error(`[GOOGLE-DRIVE-SERVICE] Invalid service account credentials file: ${e}`);
      }
    } else {
      console.error(`[GOOGLE-DRIVE-SERVICE] Service account file does not exist: ${serviceAccountJson}`);
      throw new Error(`[GOOGLE-DRIVE-SERVICE] Service account file not found: ${serviceAccountJson}`);
    }
  }

  if (!serviceAccountInfo.client_email || !serviceAccountInfo.private_key) {
    throw new Error('[GOOGLE-DRIVE-SERVICE] Invalid service account credentials. Missing client_email or private_key.');
  }

  // Create JWT auth client (following the same pattern as RAG pipeline)
  const auth = new JWT({
    email: serviceAccountInfo.client_email,
    key: serviceAccountInfo.private_key,
    scopes: SCOPES,
  });

  console.log('[GOOGLE-DRIVE-SERVICE] Service account credentials created successfully');

  // Create and return Drive client
  return new drive_v3.Drive({ auth });
}

export interface DriveUploadResult {
  success: boolean;
  fileId?: string;
  fileName?: string;
  webViewLink?: string;
  webContentLink?: string;
  error?: string;
}

export interface DriveFile {
  id?: string | null;
  name?: string | null;
  mimeType?: string | null;
  size?: string | null;
  modifiedTime?: string | null;
  webViewLink?: string | null;
}

/**
 * Upload a file to a specific folder in Google Drive
 * @param file - The file to upload
 * @param folderId - The Google Drive folder ID (defaults to pydantic_library folder)
 * @returns Promise with upload result
 */
export async function uploadFileToDrive(
  file: File,
  folderId: string = '1JfdizKUt_H1LW_G2Ze2MlQ1I5aX1ufys' // pydantic_library folder
): Promise<DriveUploadResult> {
  try {
    console.log(`[GOOGLE-DRIVE-SERVICE] Starting upload for file: ${file.name}`);
    
    const drive = createDriveClient();
    
    // Convert File to Buffer
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    
    // Create file metadata
    const fileMetadata: drive_v3.Schema$File = {
      name: file.name,
      parents: [folderId], // Upload to specific folder
    };

    // Determine MIME type
    const mimeType = file.type || 'application/octet-stream';

    console.log(`[GOOGLE-DRIVE-SERVICE] Uploading to folder: ${folderId}, MIME type: ${mimeType}`);

    // Create a readable stream from the buffer
    const { Readable } = require('stream');
    const stream = new Readable();
    stream.push(buffer);
    stream.push(null); // Signal end of stream

    // Upload file to Google Drive
    const response = await drive.files.create({
      requestBody: fileMetadata,
      media: {
        mimeType: mimeType,
        body: stream,
      },
      fields: 'id, name, webViewLink, webContentLink',
    });

    const result: DriveUploadResult = {
      success: true,
      fileId: response.data.id || undefined,
      fileName: response.data.name || undefined,
      webViewLink: response.data.webViewLink || undefined,
      webContentLink: response.data.webContentLink || undefined,
    };

    console.log(`[GOOGLE-DRIVE-SERVICE] Successfully uploaded file with ID: ${result.fileId}`);
    return result;

  } catch (error) {
    console.error('[GOOGLE-DRIVE-SERVICE] Upload error:', error);
    
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    
    return {
      success: false,
      error: `Failed to upload file to Google Drive: ${errorMessage}`,
    };
  }
}

/**
 * List files in a specific Google Drive folder
 * @param folderId - The folder ID to list files from
 * @param maxResults - Maximum number of results to return (default: 100)
 * @returns Promise with array of drive files
 */
export async function listFilesInFolder(
  folderId: string = '1JfdizKUt_H1LW_G2Ze2MlQ1I5aX1ufys',
  maxResults: number = 100
): Promise<DriveFile[]> {
  try {
    console.log(`[GOOGLE-DRIVE-SERVICE] Listing files in folder: ${folderId}`);
    
    const drive = createDriveClient();
    
    const response = await drive.files.list({
      q: `'${folderId}' in parents and trashed = false`,
      fields: 'files(id, name, mimeType, size, modifiedTime, webViewLink)',
      orderBy: 'modifiedTime desc',
      pageSize: maxResults,
    });

    const files = response.data.files || [];
    console.log(`[GOOGLE-DRIVE-SERVICE] Found ${files.length} files in folder`);
    
    return files;

  } catch (error) {
    console.error('[GOOGLE-DRIVE-SERVICE] List files error:', error);
    throw new Error(`Failed to list files from Google Drive: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Delete a file from Google Drive
 * @param fileId - The ID of the file to delete
 * @returns Promise with success status
 */
export async function deleteFileFromDrive(fileId: string): Promise<{ success: boolean; error?: string }> {
  try {
    console.log(`[GOOGLE-DRIVE-SERVICE] Deleting file: ${fileId}`);
    
    const drive = createDriveClient();
    
    await drive.files.delete({
      fileId: fileId,
    });
    
    console.log(`[GOOGLE-DRIVE-SERVICE] Successfully deleted file: ${fileId}`);
    return { success: true };

  } catch (error) {
    console.error('[GOOGLE-DRIVE-SERVICE] Delete error:', error);
    
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    
    return {
      success: false,
      error: `Failed to delete file from Google Drive: ${errorMessage}`,
    };
  }
}

/**
 * Get information about the user's Google Drive
 * @returns Promise with drive information
 */
export async function getDriveAbout() {
  try {
    console.log('[GOOGLE-DRIVE-SERVICE] Getting Drive about information');
    
    const drive = createDriveClient();
    
    const response = await drive.about.get({
      fields: 'user, storageQuota',
    });

    console.log('[GOOGLE-DRIVE-SERVICE] Successfully retrieved Drive about information');
    return response.data;

  } catch (error) {
    console.error('[GOOGLE-DRIVE-SERVICE] Get about error:', error);
    throw new Error(`Failed to get Drive information: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}