import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { uploadFileToDrive } from "@/lib/google-drive-service";

export async function POST(request: NextRequest) {
  try {
    // Get the current user
    const supabase = await createClient();
    
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    
    if (authError || !user) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    // Parse the form data
    const formData = await request.formData();
    const file = formData.get("file") as File;
    
    if (!file) {
      return NextResponse.json(
        { error: "No file provided" },
        { status: 400 }
      );
    }

    // Validate file size (10MB max)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: "File size exceeds 10MB limit" },
        { status: 400 }
      );
    }

    // Upload file to Google Drive using service module
    console.log(`[API-UPLOAD] Uploading ${file.name} to Google Drive...`);
    const driveResult = await uploadFileToDrive(file);
    
    if (!driveResult.success) {
      return NextResponse.json(
        { error: driveResult.error || "Failed to upload file to Google Drive" },
        { status: 500 }
      );
    }
    
    console.log(`[API-UPLOAD] Successfully uploaded to Google Drive with ID: ${driveResult.fileId}`);

    // Store file metadata in the database with Google Drive file ID
    const { data: fileRecord, error: dbError } = await supabase
      .from("document_metadata")
      .insert({
        name: file.name,
        size: file.size,
        mime_type: file.type,
        user_id: user.id,
        source: "google_drive",
        external_id: driveResult.fileId || null, // Google Drive file ID
        metadata: {
          uploaded_at: new Date().toISOString(),
          original_name: file.name,
          google_drive_id: driveResult.fileId,
          web_view_link: driveResult.webViewLink,
          web_content_link: driveResult.webContentLink,
        }
      })
      .select()
      .single();

    if (dbError) {
      console.error("[API-UPLOAD] Database error:", dbError);
      // Note: File is already uploaded to Google Drive at this point
      return NextResponse.json(
        { 
          warning: "File uploaded to Google Drive but failed to save metadata",
          file: {
            name: file.name,
            googleDriveId: driveResult.fileId,
            webViewLink: driveResult.webViewLink,
          }
        },
        { status: 207 } // Multi-Status
      );
    }

    console.log(`[API-UPLOAD] File metadata saved to database with ID: ${fileRecord.id}`);
    
    return NextResponse.json({
      success: true,
      file: {
        id: fileRecord.id,
        name: fileRecord.name,
        size: fileRecord.size,
        googleDriveId: driveResult.fileId,
        webViewLink: driveResult.webViewLink,
        uploadedAt: fileRecord.created_at,
      }
    });

  } catch (error) {
    console.error("[API-UPLOAD] Error uploading file:", error);
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : "Failed to upload file to Google Drive"
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json(
    { error: "Method not allowed" },
    { status: 405 }
  );
}