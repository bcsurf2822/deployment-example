# Google Drive Service Account Upload Fix - Complete Solution Guide

## Problem Statement

We encountered the persistent error: **"Service Accounts do not have storage quota. Leverage shared drives or use OAuth delegation instead"** when trying to upload files to Google Drive using a service account in our Next.js application.

## Root Cause Analysis

### The Issue
Google implemented a **policy change in mid-2024** where newly created service accounts are assigned **zero storage quota**. This affects developers who:

1. Create new Google Cloud service accounts after this policy change
2. Try to upload files directly using the service account's own storage
3. Even when folders are properly shared with the service account

### Why Traditional Solutions Failed
- **`supportsAllDrives: true`**: Helps with shared drives but doesn't solve quota issues
- **Folder sharing**: Works for permissions but doesn't give the service account storage quota
- **Shared Drive creation**: Requires Google Workspace (paid)

## Solution: Domain-Wide Delegation with User Impersonation

We implemented **domain-wide delegation** to allow the service account to impersonate a real user account that has actual storage quota.

### How It Works
1. **Service account impersonates a real user** (you) using the `subject` parameter in JWT
2. **Uses the real user's storage quota** instead of the service account's (zero) quota
3. **Files are uploaded as if the real user did it** - they appear in your Google Drive
4. **Maintains automation** - no manual intervention required

## Implementation Details

### 1. Code Changes Made

#### A. Updated Authentication (`lib/google-drive-service.ts`)

**Before (Failing):**
```typescript
const auth = new JWT({
  email: serviceAccountInfo.client_email,
  key: serviceAccountInfo.private_key,
  scopes: SCOPES,
});
```

**After (Working with Domain Delegation):**
```typescript
const jwtOptions: {
  email: string;
  key: string;
  scopes: string[];
  subject?: string; // Key addition for impersonation
} = {
  email: serviceAccountInfo.client_email,
  key: serviceAccountInfo.private_key,
  scopes: SCOPES,
};

// Add domain delegation (user impersonation) if configured
if (impersonateUser) {
  jwtOptions.subject = impersonateUser; // This makes the service account impersonate the user
  console.log(`[GOOGLE-DRIVE-SERVICE] Using domain delegation to impersonate user: ${impersonateUser}`);
}

const auth = new JWT(jwtOptions);
```

#### B. Environment Configuration
Added new environment variable:
```bash
GOOGLE_DRIVE_IMPERSONATE_USER=your-real-email@gmail.com
```

#### C. Enhanced Error Handling and User Interface
- Updated API endpoints to show domain delegation status
- Added clear warnings about quota issues when domain delegation isn't configured  
- Provided step-by-step setup instructions in the UI

### 2. Google Cloud Console Configuration

#### Step 1: Enable Domain-Wide Delegation
1. Go to [Google Cloud Console → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Select your service account: `pydantic-example-deployment@pydantic-agent-464810.iam.gserviceaccount.com`
3. Go to **Details** tab
4. Scroll to **"Domain-wide delegation"**
5. ✅ Check **"Enable Google Workspace Domain-wide Delegation"**
6. Save changes

#### Step 2: Note the Client ID
After enabling delegation, copy the **Client ID** (long number) - you'll need this for Workspace setup if applicable.

#### Step 3: Google Workspace Authorization (if using Workspace)
If you have Google Workspace:
1. Go to [Google Workspace Admin Console](https://admin.google.com)
2. **Security** → **API Controls** → **Domain-wide Delegation**
3. **Add new** with:
   - **Client ID**: From Step 2
   - **OAuth Scopes**: `https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/drive.file`
4. **Authorize**

### 3. Folder Sharing Configuration

**Important Change**: Share the folder with **your real email** (the impersonated user), NOT the service account email.

**Before:**
- Share folder with: `pydantic-example-deployment@pydantic-agent-464810.iam.gserviceaccount.com` ❌

**After:**
- Share folder with: `your-real-email@gmail.com` ✅ (Editor or Owner permissions)

## Technical Deep Dive

### Authentication Flow
1. **Service account authenticates** with Google using its private key
2. **JWT includes `subject` parameter** pointing to the real user email
3. **Google validates** that the service account has domain-wide delegation enabled
4. **Google issues access token** as if the real user made the request
5. **File operations use real user's quota** and appear in their Drive

### Key Parameters Used
- **`supportsAllDrives: true`**: Ensures compatibility with all Drive types
- **`subject: impersonateUser`**: The critical parameter that enables user impersonation
- **Proper scopes**: `https://www.googleapis.com/auth/drive` and `https://www.googleapis.com/auth/drive.file`

## Error Messages and Solutions

### Error: "unauthorized_client: Client is unauthorized..."
**Cause**: Domain-wide delegation not enabled or configured properly  
**Solution**: Follow Google Cloud Console configuration steps above

### Error: "Service Accounts do not have storage quota"
**Cause**: Domain delegation not working, falling back to service account's own quota  
**Solution**: Verify `GOOGLE_DRIVE_IMPERSONATE_USER` is set and user has storage

### Error: "Folder not found or not accessible"
**Cause**: Folder shared with service account email instead of impersonated user email  
**Solution**: Share folder with the email specified in `GOOGLE_DRIVE_IMPERSONATE_USER`

## Benefits of This Approach

### ✅ Advantages
- **Solves quota issue completely** - uses real user's storage
- **Maintains automation** - no manual steps required
- **Files appear in user's Drive** - easy to access and manage
- **Secure** - service account still requires proper authentication
- **Scalable** - works for any number of uploads

### ⚠️ Considerations
- **Requires Google Cloud setup** - domain-wide delegation configuration
- **Uses impersonated user's quota** - counts against their storage limit
- **Files owned by impersonated user** - they appear in their Drive

## Alternative Solutions Considered

### 1. OAuth2 User Credentials
**Pros**: No domain delegation setup required  
**Cons**: Requires user to manually authorize, not fully automated

### 2. Google Workspace Shared Drives
**Pros**: Team-based storage, higher quotas  
**Cons**: Requires paid Google Workspace account

### 3. Different Cloud Storage Provider
**Pros**: Might have simpler service account handling  
**Cons**: Would require complete rewrite, loss of Google Drive integration

## Final Architecture

```
┌─────────────────┐    impersonates    ┌──────────────────┐
│ Service Account │ ──────────────────► │ Real User        │
│ (zero quota)    │                     │ (has 15GB+ quota)│
└─────────────────┘                     └──────────────────┘
         │                                       │
         │ authenticates with                    │ owns files
         │ private key                           │ in Google Drive
         ▼                                       ▼
┌─────────────────┐                     ┌──────────────────┐
│ Google Drive    │ ◄─────upload────────│ Google Drive     │
│ API             │                     │ Storage          │
└─────────────────┘                     └──────────────────┘
```

## Environment Variables Summary

Add to your `.env` file:
```bash
# Existing variables
GOOGLE_DRIVE_CREDENTIALS_JSON=/path/to/service-account.json
GOOGLE_DRIVE_FOLDER_ID=1JfdizKUt_H1LW_G2Ze2MlQ1I5aX1ufys

# New variable for domain delegation
GOOGLE_DRIVE_IMPERSONATE_USER=your-real-email@gmail.com
```

## Testing and Validation

### Successful Upload Logs Should Show:
```
[GOOGLE-DRIVE-SERVICE] Using domain delegation to impersonate user: your-email@gmail.com
[GOOGLE-DRIVE-SERVICE] Successfully uploaded file with ID: 1ABC123...
```

### UI Should Display:
- ✅ **Domain Delegation Enabled** status
- Green success message indicating impersonation is working
- Service account email and impersonated user email

## Conclusion

The domain-wide delegation approach successfully resolves Google's new service account quota limitations while maintaining the automated, server-side functionality we need. This solution is robust, secure, and scales well for production use.

The key insight was understanding that Google's policy change affects the service account's **storage quota**, not just **permissions**. By using domain delegation to impersonate a real user, we bypass the quota limitation entirely while preserving all the benefits of service account automation.