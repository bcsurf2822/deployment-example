# Google Drive RAG Pipeline Setup

## Easy Setup (Recommended)

The easiest way to configure Google Drive authentication is to use a service account JSON file:

1. **Download your service account JSON** from Google Cloud Console
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Navigate to IAM & Admin > Service Accounts
   - Create or select a service account
   - Create a new key (JSON format)
   - Download the JSON file

2. **Copy the JSON file to your project**
   ```bash
   # Copy your downloaded service account JSON to the project root
   cp ~/Downloads/your-service-account-key.json ./service-account.json
   ```

3. **Update your .env file**
   ```bash
   # Add this line to your .env file (or leave the default)
   GOOGLE_SERVICE_ACCOUNT_FILE=./service-account.json
   ```

4. **Run the deployment**
   ```bash
   python deploy.py --mode dev --with-rag
   ```

That's it! The service account JSON will be automatically mounted into the container.

## Alternative Methods

### Method 2: Inline JSON (Not Recommended)

If you must use inline JSON in the .env file, it MUST be on a single line:

```bash
# In .env file - must be on ONE line
GOOGLE_DRIVE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"..."}
```

Note: This is error-prone and hard to maintain.

### Method 3: Different File Location

You can also specify a different path for your service account file:

```bash
# In .env file
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/your/service-account.json
```

## Troubleshooting

### Common Issues

1. **"Missing required fields" error**
   - Ensure your service account JSON has all required fields
   - Check that the file was copied correctly

2. **"File not found" error**
   - Verify the path in GOOGLE_SERVICE_ACCOUNT_FILE is correct
   - Ensure the file exists at that location

3. **"Invalid credentials" error**
   - Verify the service account has the necessary Google Drive API permissions
   - Enable the Google Drive API in your Google Cloud project

### Security Best Practices

- Never commit service-account.json to git (it's in .gitignore)
- Use environment-specific service accounts for dev/staging/production
- Regularly rotate service account keys
- Grant minimal necessary permissions to the service account