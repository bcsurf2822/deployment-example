import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import {
  uploadFileToDrive,
  checkFolderAccess,
} from "@/lib/google-drive-service";

export async function POST(request: NextRequest) {
  try {
    // Get the current user
    const supabase = await createClient();

    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Parse the form data
    const formData = await request.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Validate file size (10MB max)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: "File size exceeds 10MB limit" },
        { status: 400 }
      );
    }

    // Check folder access before attempting upload
    const folderId =
      process.env.GOOGLE_DRIVE_FOLDER_ID || "1JfdizKUt_H1LW_G2Ze2MlQ1I5aX1ufys";
    console.log(`[API-UPLOAD] Checking access to folder: ${folderId}`);

    const folderCheck = await checkFolderAccess(folderId);
    if (!folderCheck.accessible) {
      console.error(`[API-UPLOAD] Folder not accessible: ${folderCheck.error}`);
      return NextResponse.json(
        {
          error:
            folderCheck.error ||
            "Cannot access Google Drive folder. Please ensure the folder is shared with the service account.",
          serviceAccountTip:
            "Share the folder with the service account email from your Google Drive settings.",
        },
        { status: 403 }
      );
    }

    console.log(
      `[API-UPLOAD] Folder is accessible (${folderCheck.folderName}), is shared drive: ${folderCheck.isSharedDrive}`
    );

    // Upload file to Google Drive using service module
    // Always use shared drive support to avoid quota issues
    console.log(`[API-UPLOAD] Uploading ${file.name} to Google Drive...`);
    const driveResult = await uploadFileToDrive(
      file,
      folderId,
      true // Always use shared drive support to avoid service account quota issues
    );

    if (!driveResult.success) {
      return NextResponse.json(
        { error: driveResult.error || "Failed to upload file to Google Drive" },
        { status: 500 }
      );
    }

    console.log(
      `[API-UPLOAD] Successfully uploaded to Google Drive with ID: ${driveResult.fileId}`
    );

    // Return success response with Google Drive file details
    // The RAG pipeline will handle database operations when it processes the file
    return NextResponse.json({
      success: true,
      file: {
        title: file.name,
        googleDriveId: driveResult.fileId,
        webViewLink: driveResult.webViewLink,
        webContentLink: driveResult.webContentLink,
        uploadedAt: new Date().toISOString(),
        metadata: {
          file_name: file.name,
          file_size: file.size,
          mime_type: file.type,
          user_id: user.id,
          source: "google_drive",
        },
      },
    });
  } catch (error) {
    console.error("[API-UPLOAD] Error uploading file:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Failed to upload file to Google Drive",
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({ error: "Method not allowed" }, { status: 405 });
}
