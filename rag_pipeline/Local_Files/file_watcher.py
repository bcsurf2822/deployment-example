from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import os
import sys
import json
import time
import hashlib
import mimetypes
from pathlib import Path
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.text_processor import extract_text_from_file, chunk_text, create_embeddings
from common.db_handler import process_file_for_rag, delete_document_by_file_id, create_sync_manager, perform_full_sync

class LocalFilesWatcher:
    def __init__(self, watch_directory: str = None, config_path: str = None):
        """
        Initialize the Local Files watcher.
        
        Args:
            watch_directory: Directory to watch for file changes
            config_path: Path to the configuration file
        """
        self.watch_directory = watch_directory
        self.known_files = {}  # Store file paths and their last modified time
        self.initialized = False
        
        # Initialize sync manager with a unique pipeline ID
        pipeline_id = os.getenv('RAG_PIPELINE_ID', f'local_files_{watch_directory or "default"}')
        self.sync_manager = create_sync_manager(pipeline_id, 'local_files')
        
        # Load configuration
        self.config = {}
        if config_path:
            self.config_path = config_path
        else:
            # Default to config.json in the same directory as this script
            self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        self.load_config()
        
        # Override watch directory from environment if available (takes priority)
        env_watch_dir = os.getenv('RAG_WATCH_DIRECTORY')
        if env_watch_dir:
            self.watch_directory = env_watch_dir
            print(f"Using watch directory from environment: {self.watch_directory}")
        elif not self.watch_directory:
            # Only use config if no environment variable and no watch_directory set
            self.watch_directory = self.config.get('watch_directory', '/app/Local_Files/data')
            print(f"Using watch directory from config: {self.watch_directory}")
        
        # Ensure watch directory exists
        if self.watch_directory and not os.path.exists(self.watch_directory):
            os.makedirs(self.watch_directory, exist_ok=True)
            print(f"Created watch directory: {self.watch_directory}")
    
    def load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            print(f"Loaded configuration from {self.config_path}")
            
            # Load the last check time from config
            last_check_time_str = self.config.get('last_check_time', '2025-01-01T00:00:00Z')
            try:
                self.last_check_time = datetime.strptime(last_check_time_str, '%Y-%m-%dT%H:%M:%S%z')
            except ValueError:
                try:
                    # Try without timezone
                    self.last_check_time = datetime.strptime(last_check_time_str, '%Y-%m-%dT%H:%M:%SZ')
                    self.last_check_time = self.last_check_time.replace(tzinfo=timezone.utc)
                except ValueError:
                    # If the date format is invalid, use the default
                    self.last_check_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
                    print("Invalid last check time format in config, using default")
            
            print(f"Resuming from last check time: {self.last_check_time}")
            
            # Load pipeline state from database
            state = self.sync_manager.load_pipeline_state()
            if state['known_files']:
                self.known_files = state['known_files']
                print(f"[FILE_WATCHER-LOAD_CONFIG] Loaded {len(self.known_files)} known files from pipeline state")
                self.initialized = True  # Skip initial scan if we have state
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = self._get_default_config()
            self.last_check_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
            print("Using default configuration")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "supported_mime_types": [
                "application/pdf",
                "text/plain",
                "text/html",
                "text/csv",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/markdown",
                "application/json",
                "text/xml",
                "application/xml"
            ],
            "tabular_mime_types": [
                "text/csv",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ],
            "text_processing": {
                "chunk_size": 1000,
                "default_chunk_overlap": 0
            },
            "last_check_time": "2025-01-01T00:00:00Z",
            "watch_directory": "/Users/benjamincorbett/Desktop/local_rag_drive"
        }
    
    def save_config(self) -> None:
        """Save the current configuration including last check time."""
        try:
            # Update the last check time in config
            self.config['last_check_time'] = self.last_check_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
                
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get_file_id(self, file_path: str) -> str:
        """Generate a unique ID for a file based on its path."""
        # Use a hash of the absolute path as the file ID
        abs_path = os.path.abspath(file_path)
        return hashlib.md5(abs_path.encode(), usedforsecurity=False).hexdigest()
    
    def get_file_mime_type(self, file_path: str) -> str:
        """Get the MIME type of a file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            # Default to text/plain for unknown types
            mime_type = 'text/plain'
        return mime_type
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if a file is supported based on its MIME type."""
        mime_type = self.get_file_mime_type(file_path)
        supported_types = self.config.get('supported_mime_types', [])
        return mime_type in supported_types
    
    def scan_directory(self) -> List[Dict[str, Any]]:
        """Scan the watch directory for all files."""
        files = []
        
        if not self.watch_directory or not os.path.exists(self.watch_directory):
            print(f"Watch directory does not exist: {self.watch_directory}")
            return files
        
        for root, dirs, filenames in os.walk(self.watch_directory):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                file_path = os.path.join(root, filename)
                
                # Skip if not supported
                if not self.is_supported_file(file_path):
                    continue
                
                try:
                    stat = os.stat(file_path)
                    modified_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    
                    files.append({
                        'id': self.get_file_id(file_path),
                        'name': filename,
                        'path': file_path,
                        'mimeType': self.get_file_mime_type(file_path),
                        'modifiedTime': modified_time.isoformat(),
                        'size': stat.st_size
                    })
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
                    continue
        
        return files
    
    def get_changes(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Get files that have changed since the last check.
        
        Returns:
            Tuple of (changed_files, deleted_file_ids)
        """
        changed_files = []
        current_files = {}
        
        # Scan directory for current files
        all_files = self.scan_directory()
        
        for file in all_files:
            file_id = file['id']
            current_files[file_id] = file['modifiedTime']
            
            # Check if file is new or modified
            if file_id not in self.known_files:
                # New file
                changed_files.append(file)
                print(f"New file detected: {file['name']}")
            else:
                # Check if modified
                known_modified = self.known_files[file_id]
                if file['modifiedTime'] > known_modified:
                    changed_files.append(file)
                    print(f"Modified file detected: {file['name']}")
        
        # Check for deleted files
        deleted_file_ids = []
        for file_id in list(self.known_files.keys()):
            if file_id not in current_files:
                deleted_file_ids.append(file_id)
                print(f"Deleted file detected: {file_id}")
        
        return changed_files, deleted_file_ids
    
    def process_file(self, file_info: Dict[str, Any]) -> bool:
        """
        Process a single file for RAG pipeline.
        
        Args:
            file_info: Dictionary containing file information
            
        Returns:
            bool: True if successfully processed, False otherwise
        """
        try:
            file_path = file_info['path']
            file_id = file_info['id']
            
            print(f"Processing file: {file_info['name']} (ID: {file_id})")
            
            # Read file content
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                return False
            
            # Create metadata
            metadata = {
                'file_id': file_id,
                'file_name': file_info['name'],
                'file_path': file_path,
                'mime_type': file_info['mimeType'],
                'file_size': file_info['size'],
                'modified_time': file_info['modifiedTime'],
                'source': 'local_files'
            }
            
            # Extract text from file
            print(f"[file_watcher-process_file] Extracting text from {file_info['name']} (MIME: {file_info['mimeType']})")
            text_content = extract_text_from_file(content, file_info['mimeType'], file_info['name'], self.config)
            
            if not text_content:
                print(f"[file_watcher-process_file] No text could be extracted from file '{file_info['name']}'")
                return False
            
            print(f"[file_watcher-process_file] Extracted {len(text_content)} characters from file")
            
            # Process the file content
            print(f"[file_watcher-process_file] Processing file for RAG pipeline...")
            success = process_file_for_rag(
                file_content=content,
                text=text_content,
                file_id=file_id,
                file_url=f"file://{file_path}",
                file_title=file_info['name'],
                mime_type=file_info['mimeType'],
                config=self.config
            )
            
            if not success:
                print(f"[file_watcher-process_file] Failed to process file for RAG: {file_info['name']}")
                return False
            
            print(f"[file_watcher-process_file] Successfully completed processing {file_info['name']}")
            
            # Update known files
            self.known_files[file_id] = file_info['modifiedTime']
            
            print(f"Successfully processed: {file_info['name']}")
            return True
            
        except Exception as e:
            print(f"Error processing file {file_info.get('name', 'unknown')}: {e}")
            traceback.print_exc()
            return False
    
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
        
        try:
            # Get changed and deleted files
            changed_files, deleted_file_ids = self.get_changes()
            
            # Process changed files
            for file_info in changed_files:
                if self.process_file(file_info):
                    stats['files_processed'] += 1
                else:
                    stats['errors'] += 1
            
            # Handle deleted files
            for file_id in deleted_file_ids:
                try:
                    delete_document_by_file_id(file_id)
                    # Remove from known files
                    self.known_files.pop(file_id, None)
                    stats['files_deleted'] += 1
                except Exception as e:
                    print(f"Error deleting document for file ID {file_id}: {e}")
                    stats['errors'] += 1
            
            # Perform full synchronization to catch orphaned documents
            # Get all current file IDs from local directory
            current_file_ids = set(self.known_files.keys())
            
            # Run synchronization to delete orphaned documents
            sync_stats = self.sync_manager.sync_deletions(current_file_ids, delete_document_by_file_id)
            stats['orphaned_deleted'] = sync_stats['deleted_success']
            
            # Update last check time
            self.last_check_time = datetime.now(timezone.utc)
            
            # Save updated configuration
            self.save_config()
            
            # Save the updated pipeline state
            self.sync_manager.save_pipeline_state(self.known_files, self.last_check_time)
            
        except Exception as e:
            print(f"Error during change check: {e}")
            traceback.print_exc()
            stats['errors'] += 1
        
        stats['duration'] = time.time() - start_time
        
        # Log extended statistics if there were orphaned documents
        if stats['orphaned_deleted'] > 0:
            print(f"[FILE_WATCHER-SYNC] Removed {stats['orphaned_deleted']} orphaned documents from Supabase")
        
        return stats
    
    def watch_for_changes(self, interval_seconds: int = 60) -> None:
        """
        Watch for changes in the local directory at regular intervals.
        
        Args:
            interval_seconds: The interval in seconds between checks
        """
        print(f"Starting Local Files watcher for directory: {self.watch_directory}")
        print(f"Checking for changes every {interval_seconds} seconds...")
        
        try:
            # Initial scan to build the known_files dictionary
            if not self.initialized:
                print("Performing initial scan of files...")
                initial_files = self.scan_directory()
                
                # For initial scan, process ALL files regardless of last_check_time
                # This ensures new installations process all existing files
                print(f"Found {len(initial_files)} files in initial scan.")
                
                if initial_files:
                    print(f"Processing all {len(initial_files)} files in initial scan...")
                    for file in initial_files:
                        try:
                            print(f"Processing: {file['name']}")
                            self.process_file(file)
                            # Add to known files after successful processing
                            self.known_files[file['id']] = file['modifiedTime']
                        except Exception as e:
                            print(f"Error processing file {file['name']}: {e}")
                            traceback.print_exc()
                else:
                    # Still add to known files even if not processing
                    for file in initial_files:
                        self.known_files[file['id']] = file['modifiedTime']
                
                self.initialized = True
                
                # Update last check time after processing
                self.last_check_time = datetime.now(timezone.utc)
                self.save_config()
            
            while True:
                # Wait for the specified interval
                time.sleep(interval_seconds)
                
                # Check for changes
                stats = self.check_for_changes()
                
                # Log statistics
                if stats['files_processed'] > 0 or stats['files_deleted'] > 0:
                    print(f"Change check completed: {stats['files_processed']} files processed, "
                          f"{stats['files_deleted']} files deleted, {stats['errors']} errors, "
                          f"duration: {stats['duration']:.2f}s")
                
        except KeyboardInterrupt:
            print("\nStopping file watcher...")
        except Exception as e:
            print(f"Error in watch loop: {e}")
            traceback.print_exc()
            raise