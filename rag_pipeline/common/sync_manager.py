"""
Synchronization manager for RAG pipeline state.
Handles persistence and synchronization of file tracking across pipeline restarts.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timezone
import traceback
from supabase import Client


class PipelineSyncManager:
    """Manages synchronization between pipeline sources and Supabase database."""
    
    def __init__(self, supabase_client: Client, pipeline_id: str, pipeline_type: str):
        """
        Initialize the sync manager.
        
        Args:
            supabase_client: Supabase client instance
            pipeline_id: Unique identifier for this pipeline instance
            pipeline_type: Type of pipeline ('google_drive' or 'local_files')
        """
        self.supabase = supabase_client
        self.pipeline_id = pipeline_id
        self.pipeline_type = pipeline_type
        
    def load_pipeline_state(self) -> Dict[str, Any]:
        """
        Load the pipeline state from the database.
        
        Returns:
            Dictionary containing known_files and other state information
        """
        try:
            response = self.supabase.table("rag_pipeline_state").select("*").eq("pipeline_id", self.pipeline_id).execute()
            
            if response.data and len(response.data) > 0:
                state = response.data[0]
                print(f"[SYNC_MANAGER-LOAD_STATE] Loaded state for pipeline {self.pipeline_id}")
                return {
                    'known_files': state.get('known_files', {}),
                    'last_check_time': state.get('last_check_time'),
                    'last_run': state.get('last_run')
                }
            else:
                print(f"[SYNC_MANAGER-LOAD_STATE] No existing state for pipeline {self.pipeline_id}")
                return {
                    'known_files': {},
                    'last_check_time': None,
                    'last_run': None
                }
        except Exception as e:
            print(f"[SYNC_MANAGER-LOAD_STATE] Error loading pipeline state: {e}")
            return {
                'known_files': {},
                'last_check_time': None,
                'last_run': None
            }
    
    def save_pipeline_state(self, known_files: Dict[str, Any], last_check_time: Optional[datetime] = None) -> bool:
        """
        Save the pipeline state to the database.
        
        Args:
            known_files: Dictionary of known files and their metadata
            last_check_time: Last time the pipeline checked for changes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if state exists
            response = self.supabase.table("rag_pipeline_state").select("pipeline_id").eq("pipeline_id", self.pipeline_id).execute()
            
            state_data = {
                "pipeline_id": self.pipeline_id,
                "pipeline_type": self.pipeline_type,
                "known_files": known_files,
                "last_run": datetime.now(timezone.utc).isoformat()
            }
            
            if last_check_time:
                state_data["last_check_time"] = last_check_time.isoformat() if isinstance(last_check_time, datetime) else last_check_time
            
            if response.data and len(response.data) > 0:
                # Update existing state
                self.supabase.table("rag_pipeline_state").update(state_data).eq("pipeline_id", self.pipeline_id).execute()
                print(f"[SYNC_MANAGER-SAVE_STATE] Updated state for pipeline {self.pipeline_id}")
            else:
                # Insert new state
                self.supabase.table("rag_pipeline_state").insert(state_data).execute()
                print(f"[SYNC_MANAGER-SAVE_STATE] Created new state for pipeline {self.pipeline_id}")
            
            return True
        except Exception as e:
            print(f"[SYNC_MANAGER-SAVE_STATE] Error saving pipeline state: {e}")
            traceback.print_exc()
            return False
    
    def get_all_document_file_ids(self) -> Set[str]:
        """
        Get all file IDs currently stored in the documents table.
        
        Returns:
            Set of file IDs from the documents table
        """
        try:
            # Query distinct file_ids from documents table
            response = self.supabase.table("documents").select("metadata->>file_id").execute()
            
            file_ids = set()
            for row in response.data:
                file_id = row.get('file_id')
                if file_id:
                    file_ids.add(file_id)
            
            print(f"[SYNC_MANAGER-GET_DOCS] Found {len(file_ids)} unique file IDs in documents table")
            return file_ids
        except Exception as e:
            print(f"[SYNC_MANAGER-GET_DOCS] Error getting document file IDs: {e}")
            return set()
    
    def find_orphaned_documents(self, current_file_ids: Set[str]) -> Set[str]:
        """
        Find documents in Supabase that no longer exist in the source.
        
        Args:
            current_file_ids: Set of file IDs that currently exist in the source
            
        Returns:
            Set of file IDs that exist in Supabase but not in the source
        """
        try:
            # Get all document file IDs from Supabase
            supabase_file_ids = self.get_all_document_file_ids()
            
            # Find orphaned documents (in Supabase but not in source)
            orphaned_ids = supabase_file_ids - current_file_ids
            
            if orphaned_ids:
                print(f"[SYNC_MANAGER-ORPHANED] Found {len(orphaned_ids)} orphaned documents")
                for file_id in list(orphaned_ids)[:10]:  # Log first 10
                    print(f"[SYNC_MANAGER-ORPHANED] Orphaned file ID: {file_id}")
            else:
                print(f"[SYNC_MANAGER-ORPHANED] No orphaned documents found")
            
            return orphaned_ids
        except Exception as e:
            print(f"[SYNC_MANAGER-ORPHANED] Error finding orphaned documents: {e}")
            return set()
    
    def sync_deletions(self, current_file_ids: Set[str], delete_handler_func) -> Dict[str, int]:
        """
        Synchronize deletions by removing orphaned documents.
        
        Args:
            current_file_ids: Set of file IDs that currently exist in the source
            delete_handler_func: Function to call to delete a document by file ID
            
        Returns:
            Statistics about the sync operation
        """
        stats = {
            'orphaned_found': 0,
            'deleted_success': 0,
            'deleted_failed': 0
        }
        
        try:
            # Find orphaned documents
            orphaned_ids = self.find_orphaned_documents(current_file_ids)
            stats['orphaned_found'] = len(orphaned_ids)
            
            # Delete orphaned documents
            for file_id in orphaned_ids:
                try:
                    delete_handler_func(file_id)
                    stats['deleted_success'] += 1
                    print(f"[SYNC_MANAGER-DELETE] Successfully deleted orphaned document: {file_id}")
                except Exception as e:
                    stats['deleted_failed'] += 1
                    print(f"[SYNC_MANAGER-DELETE] Failed to delete orphaned document {file_id}: {e}")
            
            if stats['orphaned_found'] > 0:
                print(f"[SYNC_MANAGER-SYNC] Sync completed: {stats['deleted_success']}/{stats['orphaned_found']} orphaned documents deleted")
            
            return stats
        except Exception as e:
            print(f"[SYNC_MANAGER-SYNC] Error during sync: {e}")
            return stats
    
    def get_document_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific document from Supabase.
        
        Args:
            file_id: The file ID to look up
            
        Returns:
            Document metadata or None if not found
        """
        try:
            response = self.supabase.table("document_metadata").select("*").eq("id", file_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"[SYNC_MANAGER-METADATA] Error getting metadata for {file_id}: {e}")
            return None
    
    def validate_sync_state(self, known_files: Dict[str, Any], current_files: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate the synchronization state between known and current files.
        
        Args:
            known_files: Previously known files from state
            current_files: Currently existing files from source
            
        Returns:
            Dictionary with lists of added, modified, and deleted file IDs
        """
        validation = {
            'added': [],
            'modified': [],
            'deleted': []
        }
        
        known_ids = set(known_files.keys())
        current_ids = set(current_files.keys())
        
        # Files that were added
        validation['added'] = list(current_ids - known_ids)
        
        # Files that were deleted
        validation['deleted'] = list(known_ids - current_ids)
        
        # Files that were modified (exist in both but have different timestamps)
        for file_id in known_ids & current_ids:
            known_time = known_files[file_id].get('modifiedTime') if isinstance(known_files[file_id], dict) else known_files[file_id]
            current_time = current_files[file_id].get('modifiedTime') if isinstance(current_files[file_id], dict) else current_files[file_id]
            
            if known_time != current_time:
                validation['modified'].append(file_id)
        
        # Log summary
        if validation['added'] or validation['modified'] or validation['deleted']:
            print(f"[SYNC_MANAGER-VALIDATE] Changes detected - Added: {len(validation['added'])}, "
                  f"Modified: {len(validation['modified'])}, Deleted: {len(validation['deleted'])}")
        
        return validation