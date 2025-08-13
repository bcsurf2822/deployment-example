import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import * as fs from 'fs';

export async function GET() {
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

    // Get service account email from credentials
    const serviceAccountJson = process.env.GOOGLE_DRIVE_CREDENTIALS_JSON;
    
    if (!serviceAccountJson) {
      return NextResponse.json(
        { error: "Google Drive not configured" },
        { status: 503 }
      );
    }

    interface ServiceAccountInfo {
      client_email: string;
      [key: string]: unknown;
    }
    
    let serviceAccountInfo: ServiceAccountInfo;
    
    // Check if it's a file path or JSON content
    if (serviceAccountJson.startsWith('{')) {
      // It's JSON content directly
      try {
        serviceAccountInfo = JSON.parse(serviceAccountJson);
      } catch (e) {
        return NextResponse.json(
          { error: "Invalid service account configuration" },
          { status: 500 }
        );
      }
    } else {
      // It's a file path
      if (fs.existsSync(serviceAccountJson)) {
        try {
          const credentialsContent = fs.readFileSync(serviceAccountJson, 'utf8');
          serviceAccountInfo = JSON.parse(credentialsContent);
        } catch (e) {
          return NextResponse.json(
            { error: "Invalid service account configuration" },
            { status: 500 }
          );
        }
      } else {
        return NextResponse.json(
          { error: "Service account file not found" },
          { status: 500 }
        );
      }
    }

    if (!serviceAccountInfo.client_email) {
      return NextResponse.json(
        { error: "Service account email not found" },
        { status: 500 }
      );
    }

    const impersonateUser = process.env.GOOGLE_DRIVE_IMPERSONATE_USER;
    
    // Return service account email and instructions
    return NextResponse.json({
      serviceAccountEmail: serviceAccountInfo.client_email,
      impersonateUser: impersonateUser || null,
      domainDelegationEnabled: !!impersonateUser,
      instructions: {
        step1: "Go to your Google Drive and navigate to the folder you want to use",
        step2: "Right-click on the folder and select 'Share'",
        step3: impersonateUser 
          ? `Add this email address: ${impersonateUser} (the user being impersonated)`
          : `Add this email address: ${serviceAccountInfo.client_email}`,
        step4: "Give it 'Editor' permissions",
        step5: "Click 'Send' to share the folder",
        note: impersonateUser
          ? "Domain delegation is enabled - files will be uploaded as the impersonated user"
          : "Using service account directly - may encounter quota issues with new service accounts"
      },
      domainDelegationSetup: !impersonateUser ? {
        warning: "Service account quota issues detected",
        solution: "To fix quota issues, set up domain delegation:",
        steps: [
          "1. Set GOOGLE_DRIVE_IMPERSONATE_USER environment variable to a real user email",
          "2. Enable domain-wide delegation in Google Cloud Console for this service account", 
          "3. Add the service account to Google Workspace Admin (if using Workspace)",
          "4. Share your Google Drive folder with the impersonated user email instead"
        ]
      } : null,
      folderId: process.env.GOOGLE_DRIVE_FOLDER_ID || '1JfdizKUt_H1LW_G2Ze2MlQ1I5aX1ufys'
    });

  } catch (error) {
    console.error("[API-SERVICE-ACCOUNT] Error:", error);
    return NextResponse.json(
      { 
        error: error instanceof Error ? error.message : "Failed to get service account information"
      },
      { status: 500 }
    );
  }
}