# Google OAuth Setup Instructions

## 1. Google Cloud Console Setup

### Create OAuth 2.0 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client IDs**

### Configure OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type (unless you have a Google Workspace)
3. Fill in required fields:
   - **App name**: RAG Demo App
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Add scopes (required):
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
   - `openid`
5. Save and continue

### Create OAuth 2.0 Client ID
1. **Application type**: Web application
2. **Name**: RAG Demo Web Client
3. **Authorized JavaScript origins**:
   - `http://localhost:3000` (for development)
   - `https://yourdomain.com` (for production)
4. **Authorized redirect URIs**:
   - `http://localhost:3000/auth/callback` (for development)
   - `https://yourdomain.com/auth/callback` (for production)

## 2. Supabase Dashboard Configuration

1. Go to your Supabase project dashboard
2. Navigate to **Authentication** → **Providers**
3. Find **Google** provider and click **Enable**
4. Add your Google OAuth credentials:
   - **Client ID**: Copy from Google Cloud Console
   - **Client Secret**: Copy from Google Cloud Console
5. **Redirect URL** should be:
   ```
   https://[your-project-ref].supabase.co/auth/v1/callback
   ```
6. Save the configuration

## 3. Environment Variables

Add to your `.env.local` file:
```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Site Configuration (for OAuth redirects)
NEXT_PUBLIC_SITE_URL=http://localhost:3000

# API Configuration
PYDANTIC_AGENT_API_URL=http://localhost:8001/api/pydantic-agent
```

## 4. Important URLs

### For Development:
- **Authorized JavaScript origins**: `http://localhost:3000`
- **Authorized redirect URIs**: `http://localhost:3000/auth/callback`
- **Site URL**: `http://localhost:3000`

### For Production:
- **Authorized JavaScript origins**: `https://yourdomain.com`
- **Authorized redirect URIs**: `https://yourdomain.com/auth/callback`
- **Site URL**: `https://yourdomain.com`

### Supabase Callback URL (use in Google Console):
```
https://[your-project-ref].supabase.co/auth/v1/callback
```

## 5. Testing

1. Start your development server: `npm run dev`
2. Go to `http://localhost:3000/auth/login`
3. Click "Continue with Google"
4. Complete OAuth flow
5. Should redirect back to your app with user authenticated

## 6. Troubleshooting

**Common Issues:**
- **"redirect_uri_mismatch"**: Check that redirect URIs match exactly
- **"access_blocked"**: Ensure OAuth consent screen is properly configured
- **"invalid_client"**: Verify Client ID and Secret are correct in Supabase

**Debug Steps:**
1. Check browser console for errors
2. Verify environment variables are loaded
3. Confirm Supabase provider is enabled
4. Test with different browsers/incognito mode