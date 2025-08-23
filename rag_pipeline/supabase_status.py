"""
Supabase status tracking for RAG pipeline.
Replaces constant API polling with database-based status tracking.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from supabase import create_client, Client
import threading
import time

class SupabaseStatusTracker:
    """Manages RAG pipeline status in Supabase."""
    
    def __init__(self, pipeline_id: str, pipeline_type: str):
        self.pipeline_id = pipeline_id
        self.pipeline_type = pipeline_type
        
        # Initialize Supabase client
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.supabase: Client = create_client(url, key)
        self.heartbeat_thread = None
        self.stop_heartbeat = False
        
    def start(self, status_details: Optional[Dict[str, Any]] = None):
        """Mark the pipeline as online and start heartbeat."""
        try:
            # Update or insert pipeline status
            data = {
                "pipeline_id": self.pipeline_id,
                "pipeline_type": self.pipeline_type,
                "server_status": "online",
                "status_details": status_details or {},
                "last_heartbeat": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Try to update first, if no rows affected then insert
            result = self.supabase.table("rag_pipeline_state").upsert(
                data,
                on_conflict="pipeline_id"
            ).execute()
            
            print(f"[SUPABASE-STATUS] Pipeline {self.pipeline_id} marked as online")
            
            # Start heartbeat thread
            self.stop_heartbeat = False
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            return result.data
        except Exception as e:
            print(f"[SUPABASE-STATUS] Error starting pipeline: {e}")
            return None
    
    def stop(self):
        """Mark the pipeline as offline and stop heartbeat."""
        try:
            # Stop heartbeat thread
            self.stop_heartbeat = True
            if self.heartbeat_thread:
                self.heartbeat_thread.join(timeout=2)
            
            # Update pipeline status to offline
            result = self.supabase.table("rag_pipeline_state").update({
                "server_status": "offline",
                "last_heartbeat": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).eq("pipeline_id", self.pipeline_id).execute()
            
            print(f"[SUPABASE-STATUS] Pipeline {self.pipeline_id} marked as offline")
            return result.data
        except Exception as e:
            print(f"[SUPABASE-STATUS] Error stopping pipeline: {e}")
            return None
    
    def update_status(self, status_details: Dict[str, Any]):
        """Update the pipeline status details."""
        try:
            result = self.supabase.table("rag_pipeline_state").update({
                "status_details": status_details,
                "last_heartbeat": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).eq("pipeline_id", self.pipeline_id).execute()
            
            return result.data
        except Exception as e:
            print(f"[SUPABASE-STATUS] Error updating status: {e}")
            return None
    
    def _heartbeat_loop(self):
        """Background thread to send heartbeats."""
        while not self.stop_heartbeat:
            try:
                # Send heartbeat every 30 seconds
                time.sleep(30)
                
                if not self.stop_heartbeat:
                    self.supabase.table("rag_pipeline_state").update({
                        "last_heartbeat": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }).eq("pipeline_id", self.pipeline_id).execute()
                    
                    print(f"[SUPABASE-STATUS] Heartbeat sent for {self.pipeline_id}")
            except Exception as e:
                print(f"[SUPABASE-STATUS] Heartbeat error: {e}")
    
    def update_processing_status(self, 
                                files_processing: list = None,
                                files_completed: list = None,
                                files_failed: list = None,
                                is_checking: bool = None,
                                next_check_time: str = None):
        """Update detailed processing status."""
        try:
            status_details = {}
            
            if files_processing is not None:
                status_details["files_processing"] = files_processing
            if files_completed is not None:
                status_details["files_completed"] = files_completed[-10:]  # Keep last 10
            if files_failed is not None:
                status_details["files_failed"] = files_failed[-5:]  # Keep last 5
            if is_checking is not None:
                status_details["is_checking"] = is_checking
            if next_check_time is not None:
                status_details["next_check_time"] = next_check_time
            
            status_details["last_activity"] = datetime.now().isoformat()
            
            # Merge with existing status_details
            current = self.supabase.table("rag_pipeline_state").select("status_details").eq(
                "pipeline_id", self.pipeline_id
            ).execute()
            
            if current.data and current.data[0].get("status_details"):
                existing = current.data[0]["status_details"]
                existing.update(status_details)
                status_details = existing
            
            return self.update_status(status_details)
        except Exception as e:
            print(f"[SUPABASE-STATUS] Error updating processing status: {e}")
            return None

# Global instance (will be initialized by main pipeline)
status_tracker: Optional[SupabaseStatusTracker] = None

def init_status_tracker(pipeline_id: str, pipeline_type: str) -> SupabaseStatusTracker:
    """Initialize the global status tracker."""
    global status_tracker
    status_tracker = SupabaseStatusTracker(pipeline_id, pipeline_type)
    return status_tracker