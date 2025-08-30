from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import random
import time
import json
import sys
import os
import io
from pathlib import Path
import socketio
import threading
from threading import Lock


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.text_processor import extract_text_from_file, chunk_text, create_embeddings
from common.db_handler import process_file_for_rag, delete_document_by_file_id, create_sync_manager, perform_full_sync
from status_server import pipeline_status, start_status_server
from supabase_status import status_tracker


SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.readonly']

class GoogleDriveWatcher:
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json', folder_id: str = None, config_path: str = None):
        """
        Initialize the Google Drive watcher.
        
        Args:
            credentials_path: Path to the credentials.json file
            token_path: Path to the token.json file
            folder_id: ID of the specific Google Drive folder to watch (None to watch all files)
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.folder_id = folder_id
        self.service = None
        self.known_files = {}  # Store file IDs and their last modified time
        self.initialized = False  # Flag to track if we've done the initial scan
        
        # Processing state tracking for double-processing prevention
        self.processing_files = set()  # Track files currently being processed
        self.processing_lock = Lock()  # Thread safety for processing_files
        
        # Track files processed via socket to prevent timer-based reprocessing
        self.recently_socket_processed = {}  # {file_id: timestamp} for socket-processed files
        self.socket_processed_lock = Lock()  # Thread safety for recently_socket_processed
        self.socket_processed_timeout = timedelta(minutes=10)  # Time to skip timer processing after socket processing
        
        # Socket client for immediate processing notifications
        self.socket_client = None
        self.socket_connected = False
        
        # Initialize sync manager with a unique pipeline ID
        pipeline_id = os.getenv('RAG_PIPELINE_ID', f'google_drive_{folder_id or "all"}')
        self.sync_manager = create_sync_manager(pipeline_id, 'google_drive')
        
        # Initialize pipeline status
        pipeline_status.update(
            status="initializing",
            pipeline_type="google_drive",
            check_interval=60
        )
        
        self.config = {}
        if config_path:
            self.config_path = config_path
        else:
            # Default to config.json in the same directory as this script
            self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        self.load_config()
        
    def load_config(self) -> None:
        """
        Load configuration from JSON file.
        """
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            print(f"Loaded configuration from {self.config_path}")
            
            # Load the last check time from config
            last_check_time_str = self.config.get('last_check_time', '1970-01-01T00:00:00.000Z')
            try:
                self.last_check_time = datetime.strptime(last_check_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                print(f"Resuming from last check time: {self.last_check_time}")
            except ValueError:
                # If the date format is invalid, use the default
                self.last_check_time = datetime.strptime('1970-01-01T00:00:00.000Z', '%Y-%m-%dT%H:%M:%S.%fZ')
                print("Invalid last check time format in config, using default")

            if not self.folder_id:
                # Check environment variable first, then config file
                self.folder_id = os.getenv('RAG_WATCH_FOLDER_ID') or self.config.get('watch_folder_id', None)
                
            # Load pipeline state from database
            state = self.sync_manager.load_pipeline_state()
            if state['known_files']:
                self.known_files = state['known_files']
                print(f"[DRIVE_WATCHER-LOAD_CONFIG] Loaded {len(self.known_files)} known files from pipeline state")
                self.initialized = True  # Skip initial scan if we have state
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {
                "supported_mime_types": [
                    "application/pdf",
                    "text/plain",
                    "text/html",
                    "text/csv",
                    "application/vnd.google-apps.document",
                    "application/vnd.google-apps.spreadsheet",
                    "application/vnd.google-apps.presentation"
                ],
                "export_mime_types": {
                    "application/vnd.google-apps.document": "text/plain",
                    "application/vnd.google-apps.spreadsheet": "text/csv",
                    "application/vnd.google-apps.presentation": "text/plain"
                },
                "text_processing": {
                    "default_chunk_size": 400,
                    "default_chunk_overlap": 0
                },
                "last_check_time": "1970-01-01T00:00:00.000Z"
            }
            self.last_check_time = datetime.strptime('1970-01-01T00:00:00.000Z', '%Y-%m-%dT%H:%M:%S.%fZ')
            print("Using default configuration")
            
    def setup_socket_client(self) -> None:
        """
        Set up socket client connection for immediate processing notifications.
        """
        print(f"[DRIVE_WATCHER-SOCKET] ===== STARTING SOCKET CLIENT SETUP =====")
        try:
            socket_url = os.getenv('RAG_SOCKET_URL', 'http://localhost:8002')
            print(f"[DRIVE_WATCHER-SOCKET] Socket URL from environment: {socket_url}")
            print(f"[DRIVE_WATCHER-SOCKET] Attempting to connect to socket server at {socket_url}")
            
            self.socket_client = socketio.Client(
                logger=True,  # Enable logging for debugging
                engineio_logger=True
            )
            
            @self.socket_client.event
            def connect():
                print("[DRIVE_WATCHER-SOCKET] ===== SUCCESSFULLY CONNECTED TO SOCKET SERVER =====")
                self.socket_connected = True
                # Send identification message
                self.socket_client.emit('message', {
                    'type': 'identify',
                    'client': 'google-drive-watcher',
                    'message': 'Google Drive watcher connected and ready'
                })
            
            @self.socket_client.event
            def disconnect():
                print("[DRIVE_WATCHER-SOCKET] ===== DISCONNECTED FROM SOCKET SERVER =====")
                self.socket_connected = False
            
            @self.socket_client.event
            def message(data):
                print(f"[DRIVE_WATCHER-SOCKET] Received message: {data}")
            
            @self.socket_client.on('upload-complete')
            def on_upload_complete(data):
                print(f"[DRIVE_WATCHER-SOCKET] ===== RECEIVED UPLOAD-COMPLETE EVENT =====")
                print(f"[DRIVE_WATCHER-SOCKET] Data: {data}")
                self.handle_upload_complete(data)
            
            # Also listen for the underscore version just in case
            @self.socket_client.on('upload_complete')
            def on_upload_complete_underscore(data):
                print(f"[DRIVE_WATCHER-SOCKET] ===== RECEIVED UPLOAD_COMPLETE EVENT (underscore) =====")
                print(f"[DRIVE_WATCHER-SOCKET] Data: {data}")
                self.handle_upload_complete(data)
            
            # Connect to socket server in a separate thread to avoid blocking
            def connect_socket():
                try:
                    print(f"[DRIVE_WATCHER-SOCKET] Starting connection attempt to {socket_url}")
                    self.socket_client.connect(socket_url)
                    print(f"[DRIVE_WATCHER-SOCKET] Connection thread: socket client connected")
                    # Keep the connection alive
                    self.socket_client.wait()
                except Exception as e:
                    print(f"[DRIVE_WATCHER-SOCKET] Failed to connect: {e}")
                    import traceback
                    traceback.print_exc()
                    self.socket_connected = False
            
            socket_thread = threading.Thread(target=connect_socket, daemon=True)
            socket_thread.start()
            
            # Give the socket a moment to connect
            time.sleep(2)
            print(f"[DRIVE_WATCHER-SOCKET] Socket connected status: {self.socket_connected}")
            
        except Exception as e:
            print(f"[DRIVE_WATCHER-SOCKET] Error setting up socket client: {e}")
            import traceback
            traceback.print_exc()
            self.socket_connected = False
            
    def save_last_check_time(self) -> None:
        """
        Save the last check time to the config file.
        """
        try:
            # Update the last_check_time in the config
            self.config['last_check_time'] = self.last_check_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            # Write the updated config back to the file
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            print(f"Saved last check time: {self.last_check_time}")
        except Exception as e:
            print(f"Error saving last check time: {e}")
            
    def handle_upload_complete(self, data: Dict[str, Any]) -> None:
        """
        Handle upload completion notification from socket server.
        
        Args:
            data: Upload completion data containing fileName, googleDriveId, fileSize
        """
        try:
            file_name = data.get('fileName', 'Unknown')
            google_drive_id = data.get('googleDriveId')
            file_size = data.get('fileSize', 0)
            
            print(f"[DRIVE_WATCHER-UPLOAD_COMPLETE] Processing immediate upload: {file_name} (ID: {google_drive_id})")
            
            if not google_drive_id:
                print("[DRIVE_WATCHER-UPLOAD_COMPLETE] No Google Drive ID provided, skipping")
                return
                
            # Process the file immediately
            success = self.process_file_immediately(google_drive_id, file_name)
            
            if success:
                print(f"[DRIVE_WATCHER-UPLOAD_COMPLETE] Successfully processed {file_name} immediately")
            else:
                print(f"[DRIVE_WATCHER-UPLOAD_COMPLETE] Failed to process {file_name} immediately, will retry in next timer cycle")
                
        except Exception as e:
            print(f"[DRIVE_WATCHER-UPLOAD_COMPLETE] Error handling upload complete: {e}")
    
    def cleanup_old_socket_processed_entries(self) -> None:
        """
        Clean up old entries from recently_socket_processed to prevent memory buildup.
        Removes entries older than socket_processed_timeout.
        """
        with self.socket_processed_lock:
            current_time = datetime.now(timezone.utc)
            expired_files = []
            
            for file_id, processed_time in self.recently_socket_processed.items():
                if current_time - processed_time > self.socket_processed_timeout:
                    expired_files.append(file_id)
            
            for file_id in expired_files:
                del self.recently_socket_processed[file_id]
            
            if expired_files:
                print(f"[DRIVE_WATCHER-CLEANUP] Removed {len(expired_files)} expired socket-processed entries")

    def process_file_immediately(self, google_drive_id: str, file_name: str) -> bool:
        """
        Process a specific file immediately by its Google Drive ID.
        
        Args:
            google_drive_id: The Google Drive file ID
            file_name: The file name for logging
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Check if file is already being processed
            with self.processing_lock:
                if google_drive_id in self.processing_files:
                    print(f"[DRIVE_WATCHER-IMMEDIATE] File {file_name} (ID: {google_drive_id}) is already being processed, skipping")
                    return True 
      
                self.processing_files.add(google_drive_id)
            
            # Track this file as being processed via socket
            with self.socket_processed_lock:
                self.recently_socket_processed[google_drive_id] = datetime.now(timezone.utc)
                print(f"[DRIVE_WATCHER-IMMEDIATE] Marking {file_name} as socket-processed to prevent timer reprocessing")
                
            try:
                # Authenticate if needed
                if not self.service:
                    self.authenticate()
                
                # Get file metadata from Google Drive
                print(f"[DRIVE_WATCHER-IMMEDIATE] Fetching metadata for {file_name} (ID: {google_drive_id})")
                file_metadata = self.service.files().get(
                    fileId=google_drive_id,
                    fields="id, name, mimeType, webViewLink, modifiedTime, createdTime, trashed"
                ).execute()
                
                # Check if file was recently processed
                current_modified_time = file_metadata.get('modifiedTime')
                if google_drive_id in self.known_files:
                    known_modified_time = self.known_files[google_drive_id]
                    if current_modified_time == known_modified_time:
                        print(f"[DRIVE_WATCHER-IMMEDIATE] File {file_name} already processed (same modifiedTime), skipping")
                        return True
                
                # Check if file is in correct folder (if folder watching is enabled)
                if self.folder_id:
                    # Get file's parent folders
                    parents_response = self.service.files().get(
                        fileId=google_drive_id,
                        fields="parents"
                    ).execute()
                    
                    file_parents = parents_response.get('parents', [])
                    if self.folder_id not in file_parents:
                        print(f"[DRIVE_WATCHER-IMMEDIATE] File {file_name} not in watched folder {self.folder_id}, skipping")
                        return True
                
                # Remove from processing_files temporarily so process_file doesn't skip it
                # We'll re-add it inside process_file
                with self.processing_lock:
                    self.processing_files.discard(google_drive_id)
                
                # Process the file using existing process_file method (with socket notifications)
                print(f"[DRIVE_WATCHER-IMMEDIATE] Processing {file_name} immediately")
                self.process_file(file_metadata, send_socket_notifications=True)
                
                return True
                
            finally:
                with self.processing_lock:
                    self.processing_files.discard(google_drive_id)
                    
        except Exception as e:
            print(f"[DRIVE_WATCHER-IMMEDIATE] Error processing file immediately: {e}")
            return False
    
    def authenticate(self) -> None:
        """
        Authenticate with Google Drive API.
        Supports both service account (for cloud deployment) and OAuth2 (for local development).
        """
        creds = None
        
        service_account_json = os.getenv('GOOGLE_DRIVE_CREDENTIALS_JSON')
        print(f"[DRIVE_WATCHER-AUTHENTICATE] GOOGLE_DRIVE_CREDENTIALS_JSON environment variable: {service_account_json}")
        
        if service_account_json:
            print(f"[DRIVE_WATCHER-AUTHENTICATE] Found service account JSON path: {service_account_json}")

            if service_account_json.startswith('{'):
                # It's JSON content directly
                print("[DRIVE_WATCHER-AUTHENTICATE] Environment variable contains JSON content directly")
                try:
                    service_account_info = json.loads(service_account_json)
                    print(f"[DRIVE_WATCHER-AUTHENTICATE] Parsed JSON keys: {list(service_account_info.keys())}")
                    print(f"[DRIVE_WATCHER-AUTHENTICATE] Service account email: {service_account_info.get('client_email', 'NOT_FOUND')}")
                    
                    creds = ServiceAccountCredentials.from_service_account_info(
                        service_account_info, scopes=SCOPES)
                    print("[DRIVE_WATCHER-AUTHENTICATE] Service account credentials created from JSON content")
                    
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"[DRIVE_WATCHER-AUTHENTICATE] Error parsing JSON content: {e}")
                    raise RuntimeError(f"Invalid service account credentials in environment variable: {e}")
            else:
                # It's a file path
                print(f"[DRIVE_WATCHER-AUTHENTICATE] Environment variable contains file path: {service_account_json}")
                print(f"[DRIVE_WATCHER-AUTHENTICATE] File exists: {os.path.exists(service_account_json)}")
                
                if os.path.exists(service_account_json):
                    try:
                        with open(service_account_json, 'r') as f:
                            service_account_info = json.load(f)
                        print(f"[DRIVE_WATCHER-AUTHENTICATE] Loaded JSON from file, keys: {list(service_account_info.keys())}")
                        print(f"[DRIVE_WATCHER-AUTHENTICATE] Service account email: {service_account_info.get('client_email', 'NOT_FOUND')}")
                        
                        creds = ServiceAccountCredentials.from_service_account_info(
                            service_account_info, scopes=SCOPES)
                        print("[DRIVE_WATCHER-AUTHENTICATE] Service account credentials created from file")
                        
                    except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
                        print(f"[DRIVE_WATCHER-AUTHENTICATE] Error loading JSON from file: {e}")
                        raise RuntimeError(f"Invalid service account credentials file: {e}")
                else:
                    print(f"[DRIVE_WATCHER-AUTHENTICATE] Service account file does not exist: {service_account_json}")
                    raise RuntimeError(f"Service account file not found: {service_account_json}")
            
            try:
                print("[DRIVE_WATCHER-AUTHENTICATE] Testing service account credentials...")
                test_service = build('drive', 'v3', credentials=creds)
            
                user_info = test_service.about().get(fields='user').execute()
                print(f"[DRIVE_WATCHER-AUTHENTICATE] Service account credentials validated successfully for user: {user_info.get('user', {}).get('emailAddress', 'unknown')}")
                print("[DRIVE_WATCHER-AUTHENTICATE] Using service account authentication for Google Drive")
                
            except Exception as e:
                print(f"[DRIVE_WATCHER-AUTHENTICATE] Error validating service account credentials: {e}")
                print(f"[DRIVE_WATCHER-AUTHENTICATE] Error type: {type(e).__name__}")
                raise RuntimeError(f"Service account authentication failed: {e}")
        
        # Check for existing OAuth2 token
        if not creds and os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_info(
                    json.loads(open(self.token_path).read()), SCOPES)
                print("Using existing OAuth2 token for Google Drive")
            except Exception as e:
                print(f"Error loading OAuth2 token: {e}")
        
        # OAuth2 flow for interactive authentication (local development)
        if not creds or (hasattr(creds, 'valid') and not creds.valid):
            if creds and hasattr(creds, 'expired') and creds.expired and hasattr(creds, 'refresh_token') and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("Refreshed OAuth2 token for Google Drive")
                except RefreshError:
                    print("OAuth2 token refresh failed, re-authenticating...")
                    creds = self._oauth2_authenticate()
            else:
                # Only attempt OAuth2 if no service account was provided
                if not service_account_json:
                    print("No service account credentials found, starting OAuth2 authentication...")
                    creds = self._oauth2_authenticate()
                else:
                    # Service account was provided but failed - don't fall back to OAuth2
                    raise RuntimeError("Service account authentication failed and no OAuth2 fallback available in containerized environment")
        
        # Build the Drive API service
        self.service = build('drive', 'v3', credentials=creds)
        print("Google Drive API service initialized successfully")
    
    def _oauth2_authenticate(self) -> Credentials:
        """
        Perform OAuth2 authentication flow.
        
        Returns:
            Authenticated credentials
        """
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Google Drive credentials file not found: {self.credentials_path}. "
                f"Either provide OAuth2 credentials file or set GOOGLE_DRIVE_CREDENTIALS_JSON environment variable."
            )
        
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        try:
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
            print(f"OAuth2 token saved to {self.token_path}")
        except Exception as e:
            print(f"Warning: Could not save OAuth2 token: {e}")
        
        return creds
    
    def get_folder_contents(self, folder_id: str, time_str: str) -> List[Dict[str, Any]]:
        """
        Get all files and subfolders in a folder that have been modified or created after the specified time.
        
        Args:
            folder_id: The ID of the folder to check
            time_str: The time string in RFC 3339 format
            
        Returns:
            List of files and folders with their metadata
        """
        # Query for files in this folder that were modified OR created after the specified time
        query = f"(modifiedTime > '{time_str}' or createdTime > '{time_str}') and '{folder_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, createdTime, trashed)"
        ).execute()
        
        items = results.get('files', [])
        
        # Find all subfolders in this folder (regardless of modification time)
        folder_query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        folder_results = self.service.files().list(
            q=folder_query,
            pageSize=100,
            fields="files(id)"
        ).execute()
        
        subfolders = folder_results.get('files', [])
        
        # Recursively get contents of each subfolder
        for subfolder in subfolders:
            subfolder_items = self.get_folder_contents(subfolder['id'], time_str)
            items.extend(subfolder_items)
        
        return items
    
    def get_changes(self) -> List[Dict[str, Any]]:
        """
        Get changes in Google Drive since the last check.
        
        Returns:
            List of changed files with their metadata
        """
        if not self.service:
            self.authenticate()
        
        # Convert last_check_time to RFC 3339 format
        time_str = self.last_check_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        files = []
        
        # If a specific folder is specified, recursively get all files in that folder and its subfolders
        if self.folder_id:
            files = self.get_folder_contents(self.folder_id, time_str)
        else:
            # If no folder is specified, get all files in the drive that were modified OR created after the specified time
            query = f"modifiedTime > '{time_str}' or createdTime > '{time_str}'"
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, createdTime, trashed)"
            ).execute()
            
            files = results.get('files', [])
        
        # Update the last check time
        self.last_check_time = datetime.now(timezone.utc)
        
        # Save the updated last check time to config
        self.save_last_check_time()
        
        return files
    
    def download_file(self, file_id: str, mime_type: str) -> Optional[bytes]:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: The ID of the file to download
            mime_type: The MIME type of the file
            
        Returns:
            The file content as bytes, or None if download failed
        """
        if not self.service:
            self.authenticate()
        
        try:
            file_content = io.BytesIO()
            
            # Check if this is a Google Workspace file that needs to be exported
            export_mime_types = self.config.get('export_mime_types', {})
            if mime_type in export_mime_types:
                # Export the file in the appropriate format
                request = self.service.files().export_media(
                    fileId=file_id, 
                    mimeType=export_mime_types[mime_type]
                )
            else:
                # For regular files, download directly
                request = self.service.files().get_media(fileId=file_id)
            
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            file_content.seek(0)
            return file_content.read()
        
        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return None
    
    def process_file(self, file: Dict[str, Any], send_socket_notifications: bool = False) -> None:
        """
        Process a file for the RAG pipeline.
        
        Args:
            file: The file metadata from Google Drive
            send_socket_notifications: Whether to send socket notifications (True for socket-triggered, False for timer-based)
        """
        file_id = file['id']
        file_name = file['name']
        mime_type = file['mimeType']
        web_view_link = file.get('webViewLink', '')
        is_trashed = file.get('trashed', False)
        
        # Check if file is already being processed (for timer-based processing)
        with self.processing_lock:
            if file_id in self.processing_files:
                print(f"[DRIVE_WATCHER-PROCESS] File {file_name} (ID: {file_id}) is already being processed, skipping")
                return
            
            # Mark as processing
            self.processing_files.add(file_id)
        
        try:
            # Notify status server that we're starting to process this file
            pipeline_status.add_processing_file(file_name, file_id)
            
            # Send socket notification that processing has started
            if send_socket_notifications and self.socket_client and self.socket_connected:
                print(f"[DRIVE_WATCHER-PROCESS] Sending processing-started notification for {file_name} (socket-triggered)")
                self.socket_client.emit("processing-started", {
                    "fileName": file_name,
                    "googleDriveId": file_id,
                    "timestamp": datetime.now().isoformat(),
                    "pipelineType": "google_drive"
                })
            
            # Update Supabase status
            if status_tracker:
                file_info = {
                    "name": file_name,
                    "id": file_id,
                    "started_at": datetime.now().isoformat()
                }
                status_tracker.update_processing_status(files_processing=[file_info])
            
            # Check if the file is in the trash
            if is_trashed:
                print(f"File '{file_name}' (ID: {file_id}) has been trashed. Removing from database...")
                delete_document_by_file_id(file_id)
                if file_id in self.known_files:
                    del self.known_files[file_id]
                return
            
            # Skip unsupported file types
            supported_mime_types = self.config.get('supported_mime_types', [])
            if not any(mime_type.startswith(t) for t in supported_mime_types):
                print(f"Skipping unsupported file type: {mime_type}")
                # Remove from processing since we're skipping it
                pipeline_status.complete_file(file_name, False)
                
                # Send socket notification for unsupported file type
                if send_socket_notifications and self.socket_client and self.socket_connected:
                    print(f"[DRIVE_WATCHER-PROCESS] Sending processing-failed notification for {file_name} (unsupported type, socket-triggered)")
                    self.socket_client.emit("processing-failed", {
                        "fileName": file_name,
                        "googleDriveId": file_id,
                        "timestamp": datetime.now().isoformat(),
                        "pipelineType": "google_drive",
                        "error": f"Unsupported file type: {mime_type}"
                    })
                return
            
            # Download the file
            file_content = self.download_file(file_id, mime_type)
            if not file_content:
                print(f"Failed to download file '{file_name}' (ID: {file_id})")
                # Mark as failed in status
                pipeline_status.complete_file(file_name, False)
                
                # Send socket notification for download failure
                if send_socket_notifications and self.socket_client and self.socket_connected:
                    print(f"[DRIVE_WATCHER-PROCESS] Sending processing-failed notification for {file_name} (download failed, socket-triggered)")
                    self.socket_client.emit("processing-failed", {
                        "fileName": file_name,
                        "googleDriveId": file_id,
                        "timestamp": datetime.now().isoformat(),
                        "pipelineType": "google_drive",
                        "error": "Failed to download file"
                    })
                return
            
            # Extract text from the file
            text = extract_text_from_file(file_content, mime_type, file_name, self.config)
            if not text:
                print(f"No text could be extracted from file '{file_name}' (ID: {file_id})")
                # Mark as failed in status
                pipeline_status.complete_file(file_name, False)
                
                # Send socket notification for text extraction failure (only for socket-triggered processing)
                if send_socket_notifications and self.socket_client and self.socket_connected:
                    print(f"[DRIVE_WATCHER-PROCESS] Sending processing-failed notification for {file_name} (text extraction failed, socket-triggered)")
                    self.socket_client.emit("processing-failed", {
                        "fileName": file_name,
                        "googleDriveId": file_id,
                        "timestamp": datetime.now().isoformat(),
                        "pipelineType": "google_drive",
                        "error": "No text could be extracted from file"
                    })
                
                # Also update Supabase status
                if status_tracker:
                    file_info = {
                        "name": file_name,
                        "id": file_id,
                        "completed_at": datetime.now().isoformat()
                    }
                    status_tracker.update_processing_status(
                        files_processing=[],  # Clear processing
                        files_failed=[file_info]  # Add to failed
                    )
                return
            
            # Process the file for RAG
            success = process_file_for_rag(file_content, text, file_id, web_view_link, file_name, mime_type, self.config, 'google_drive')
            
            # Update the known files dictionary
            self.known_files[file_id] = file.get('modifiedTime')
            
            # Notify status server of completion
            pipeline_status.complete_file(file_name, success)
            
            # Send socket notification based on success/failure (only for socket-triggered processing)
            if send_socket_notifications and self.socket_client and self.socket_connected:
                if success:
                    print(f"[DRIVE_WATCHER-PROCESS] Sending processing-complete notification for {file_name} (socket-triggered)")
                    self.socket_client.emit("processing-complete", {
                        "fileName": file_name,
                        "googleDriveId": file_id,
                        "timestamp": datetime.now().isoformat(),
                        "pipelineType": "google_drive"
                    })
                else:
                    print(f"[DRIVE_WATCHER-PROCESS] Sending processing-failed notification for {file_name} (socket-triggered)")
                    self.socket_client.emit("processing-failed", {
                        "fileName": file_name,
                        "googleDriveId": file_id,
                        "timestamp": datetime.now().isoformat(),
                        "pipelineType": "google_drive",
                        "error": "Failed to process file for RAG"
                    })
            
            # Also update Supabase status - move file from processing to completed/failed
            if status_tracker:
                file_info = {
                    "name": file_name,
                    "id": file_id,
                    "completed_at": datetime.now().isoformat()
                }
                
                if success:
                    status_tracker.update_processing_status(
                        files_processing=[],  # Clear processing
                        files_completed=[file_info]  # Add to completed
                    )
                else:
                    status_tracker.update_processing_status(
                        files_processing=[],  # Clear processing
                        files_failed=[file_info]  # Add to failed
                    )
            
            if success:
                print(f"Successfully processed file '{file_name}' (ID: {file_id})")
            else:
                print(f"Failed to process file '{file_name}' (ID: {file_id})")
        
        finally:
            # Always remove file from processing set
            with self.processing_lock:
                self.processing_files.discard(file_id)
    
    def check_for_deleted_files(self) -> List[str]:
        """
        Check for files that have been deleted from Google Drive.
        
        Returns:
            List of IDs of deleted files
        """
        if not self.service:
            self.authenticate()
            
        # We'll only check files we know about
        deleted_files = []
        
        # Only check if we have known files
        if not self.known_files:
            return deleted_files
            
        # Check each known file to see if it still exists or has been trashed
        for file_id in list(self.known_files.keys()):
            try:
                # Get the file metadata
                file = self.service.files().get(
                    fileId=file_id,
                    fields="trashed,name"
                ).execute()
                
                if file.get('trashed', False):
                    print(f"File '{file.get('name', 'Unknown')}' (ID: {file_id}) is in trash")
                    deleted_files.append(file_id)
            except Exception as e:
                if 'File not found' in str(e) or '404' in str(e):
                    deleted_files.append(file_id)
                else:
                    print(f"Error checking file {file_id}: {e}")
        
        return deleted_files
    
    def check_for_changes(self) -> Dict[str, int]:
        """
        Check for file changes once and process them.
        
        Returns:
            Dictionary with statistics: {
                'files_processed': int,
                'files_deleted': int,
                'errors': int,
                'duration': float
            }
        """
        start_time = time.time()
        stats = {
            'files_processed': 0,
            'files_deleted': 0,
            'errors': 0,
            'duration': 0.0,
            'orphaned_deleted': 0
        }
        
        # Update status to indicate we're checking for changes
        pipeline_status.update(is_checking=True, status="running")
        
        # Clean up old socket-processed entries before processing
        self.cleanup_old_socket_processed_entries()
        
        try:
            # Authenticate if needed
            if not self.service:
                self.authenticate()
            
            # Get changes since the last check
            changed_files = self.get_changes()
            
            # Check for deleted files (from known_files)
            deleted_file_ids = self.check_for_deleted_files()
            
            # Process changed files
            if changed_files:
                print(f"Found {len(changed_files)} changed files.")
                for file in changed_files:
                    try:
                        file_id = file.get('id')
                        file_name = file.get('name', 'Unknown')
                        
                        # Skip files that are already being processed immediately
                        with self.processing_lock:
                            if file_id in self.processing_files:
                                print(f"[DRIVE_WATCHER-TIMER] Skipping {file_name} - already being processed immediately")
                                continue
                        
                        # Skip files that were recently processed via socket
                        with self.socket_processed_lock:
                            if file_id in self.recently_socket_processed:
                                processed_time = self.recently_socket_processed[file_id]
                                time_since_processing = datetime.now(timezone.utc) - processed_time
                                if time_since_processing < self.socket_processed_timeout:
                                    print(f"[DRIVE_WATCHER-TIMER] Skipping {file_name} - recently processed via socket ({time_since_processing.total_seconds():.1f}s ago)")
                                    continue
                                else:
                                    # File is old enough, remove from tracking and allow processing
                                    print(f"[DRIVE_WATCHER-TIMER] Socket processing timeout expired for {file_name}, allowing timer processing")
                                    del self.recently_socket_processed[file_id]
                        
                        print(f"[DRIVE_WATCHER-TIMER] Processing: {file_name} (timer-based, no socket notifications)")
                        self.process_file(file)  # send_socket_notifications defaults to False
                        # Update known_files with just the modifiedTime
                        self.known_files[file['id']] = file.get('modifiedTime')
                        stats['files_processed'] += 1
                    except Exception as e:
                        print(f"Error processing file {file.get('name', 'Unknown')}: {e}")
                        stats['errors'] += 1
            
            # Process deleted files from known_files
            if deleted_file_ids:
                print(f"Found {len(deleted_file_ids)} deleted files.")
                for file_id in deleted_file_ids:
                    try:
                        print(f"File with ID: {file_id} has been deleted. Removing from database...")
                        delete_document_by_file_id(file_id)
                        # Remove from known_files
                        del self.known_files[file_id]
                        stats['files_deleted'] += 1
                    except Exception as e:
                        print(f"Error deleting document for file ID {file_id}: {e}")
                        stats['errors'] += 1
            
            # Check if orphan deletion is enabled in config
            sync_settings = self.config.get('sync_settings', {})
            if sync_settings.get('enable_orphan_deletion', True):
                # Perform full synchronization to catch orphaned documents
                # Get all current file IDs from Google Drive
                current_file_ids = set(self.known_files.keys())
                
                # Run synchronization to delete orphaned documents
                sync_stats = self.sync_manager.sync_deletions(current_file_ids, delete_document_by_file_id)
                stats['orphaned_deleted'] = sync_stats['deleted_success']
            
            # Save the updated pipeline state
            self.sync_manager.save_pipeline_state(self.known_files, self.last_check_time)
            
        except Exception as e:
            print(f"Error during change check: {e}")
            stats['errors'] += 1
        
        stats['duration'] = time.time() - start_time
        
        # Update status with next check time and clear is_checking flag
        next_check_time = datetime.now(timezone.utc) + timedelta(seconds=60)
        pipeline_status.update(
            is_checking=False,
            last_check_time=datetime.now(timezone.utc).isoformat(),
            next_check_time=next_check_time.isoformat()
        )
        
        # Log extended statistics if there were orphaned documents
        if stats['orphaned_deleted'] > 0:
            print(f"[DRIVE_WATCHER-SYNC] Removed {stats['orphaned_deleted']} orphaned documents from Supabase")
        
        return stats

    #  WATCH FOR CHANGES IN GOOGLE DRIVE

    def watch_for_changes(self, interval_seconds: int = 60) -> None:
        """
        Watch for changes in Google Drive at regular intervals.
        
        Args:
            interval_seconds: The interval in seconds between checks
        """
        folder_msg = f" in folder ID: {self.folder_id}" if self.folder_id else ""
        print(f"Starting Google Drive watcher{folder_msg}. Checking for changes every {interval_seconds} seconds...")
        
        # Update pipeline status (status server should be started by main.py)
        pipeline_status.update(
            status="running",
            pipeline_type="google_drive",
            check_interval=interval_seconds
        )
        
        try:
            # Authenticate if needed
            if not self.service:
                self.authenticate()
            
            # Set up socket client for immediate processing
            self.setup_socket_client()
            
            # Initial scan to build the known_files dictionary
            if not self.initialized:
                print("Performing initial scan of files...")
                # Get all files in the watched folder
                # Use the last check time from config or default to 1970-01-01
                time_str = self.last_check_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                if self.folder_id:
                    files = self.get_folder_contents(self.folder_id, time_str)  # Get all files
                else:
                    # If watching all of Drive, get all files
                    results = self.service.files().list(
                        pageSize=1000,
                        fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, trashed)"
                    ).execute()
                    files = results.get('files', [])
                
                # Build the known_files dictionary - only store the modifiedTime
                for file in files:
                    if not file.get('trashed', False):  # Skip files in trash
                        # Only store the modifiedTime to avoid processing all files
                        self.known_files[file['id']] = file.get('modifiedTime')
                
                print(f"Found {len(self.known_files)} files in initial scan.")
                
                # Perform startup sync if enabled
                sync_settings = self.config.get('sync_settings', {})
                if sync_settings.get('sync_on_startup', True):
                    print("[DRIVE_WATCHER-STARTUP] Running startup synchronization...")
                    current_file_ids = set(self.known_files.keys())
                    sync_stats = self.sync_manager.sync_deletions(current_file_ids, delete_document_by_file_id)
                    if sync_stats['deleted_success'] > 0:
                        print(f"[DRIVE_WATCHER-STARTUP] Removed {sync_stats['deleted_success']} orphaned documents during startup")
                
                self.initialized = True
            
            while True:
                # Use check_for_changes method
                stats = self.check_for_changes()
                
                # Log statistics if there were any changes
                if stats['files_processed'] > 0 or stats['files_deleted'] > 0:
                    print(f"Change check completed: {stats['files_processed']} files processed, "
                          f"{stats['files_deleted']} files deleted, {stats['errors']} errors, "
                          f"duration: {stats['duration']:.2f}s")
                
                # Wait for the next check
                print(f"Waiting {interval_seconds} seconds until next check...")
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print("Watcher stopped by user.")
        except Exception as e:
            print(f"Error in watcher: {e}")
            raise
        finally:
            self.disconnect_socket_client()
            
    def disconnect_socket_client(self) -> None:
        """
        Disconnect the socket client gracefully.
        """
        try:
            if self.socket_client and self.socket_connected:
                print("[DRIVE_WATCHER-SOCKET] Disconnecting from socket server")
                self.socket_client.disconnect()
                self.socket_connected = False
        except Exception as e:
            print(f"[DRIVE_WATCHER-SOCKET] Error disconnecting socket client: {e}")
