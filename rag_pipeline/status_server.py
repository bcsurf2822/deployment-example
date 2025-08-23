"""
Simple HTTP status server for RAG pipeline monitoring.
Runs alongside the main pipeline to provide status information.
"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from typing import Dict, Any, Optional

class PipelineStatus:
    """Shared status storage for the pipeline."""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.data = {
            "status": "initializing",
            "pipeline_type": None,
            "last_check_time": None,
            "next_check_time": None,
            "files_processing": [],
            "files_completed": [],
            "files_failed": [],
            "total_processed": 0,
            "total_failed": 0,
            "check_interval": 60,
            "is_checking": False,
            "started_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
    
    def update(self, **kwargs):
        """Thread-safe update of status data."""
        with self.lock:
            self.data.update(kwargs)
            self.data["last_activity"] = datetime.now().isoformat()
    
    def get(self) -> Dict[str, Any]:
        """Thread-safe get of status data."""
        with self.lock:
            return self.data.copy()
    
    def add_processing_file(self, filename: str, file_id: Optional[str] = None):
        """Add a file to processing list."""
        with self.lock:
            file_info = {
                "name": filename,
                "id": file_id,
                "started_at": datetime.now().isoformat()
            }
            self.data["files_processing"].append(file_info)
            self.data["last_activity"] = datetime.now().isoformat()
    
    def complete_file(self, filename: str, success: bool = True):
        """Move file from processing to completed/failed."""
        with self.lock:
            # Find and remove from processing
            processing = [f for f in self.data["files_processing"] if f["name"] != filename]
            removed = [f for f in self.data["files_processing"] if f["name"] == filename]
            
            if removed:
                file_info = removed[0]
                file_info["completed_at"] = datetime.now().isoformat()
                
                if success:
                    self.data["files_completed"].append(file_info)
                    self.data["total_processed"] += 1
                    # Keep only last 10 completed files
                    if len(self.data["files_completed"]) > 10:
                        self.data["files_completed"] = self.data["files_completed"][-10:]
                else:
                    self.data["files_failed"].append(file_info)
                    self.data["total_failed"] += 1
                    # Keep only last 5 failed files
                    if len(self.data["files_failed"]) > 5:
                        self.data["files_failed"] = self.data["files_failed"][-5:]
            
            self.data["files_processing"] = processing
            self.data["last_activity"] = datetime.now().isoformat()

# Global status object
pipeline_status = PipelineStatus()

class StatusHandler(BaseHTTPRequestHandler):
    """HTTP request handler for status endpoint."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            status = pipeline_status.get()
            if status["next_check_time"]:

                try:
                    next_check = datetime.fromisoformat(status["next_check_time"])
                    now = datetime.now()
                    
                    # Make both timezone-naive for comparison
                    if next_check.tzinfo is not None:
                        next_check = next_check.replace(tzinfo=None)
                    if now.tzinfo is not None:
                        now = now.replace(tzinfo=None)
                    
                    if next_check > now:
                        status["seconds_until_next_check"] = int((next_check - now).total_seconds())
                    else:
                        status["seconds_until_next_check"] = 0
                except Exception as e:
                    print(f"Error calculating next check time: {e}")
                    status["seconds_until_next_check"] = 0
            
            self.wfile.write(json.dumps(status, indent=2).encode())
        
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

def start_status_server(port: int = 8003):
    """Start the status server in a background thread."""
    server = HTTPServer(("0.0.0.0", port), StatusHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Status server started on port {port}")
    return server

if __name__ == "__main__":
    # Test the status server
    server = start_status_server(8003)
    print("Status server running on http://localhost:8003/status")
    
    # Simulate some status updates
    pipeline_status.update(status="running", pipeline_type="google_drive")
    time.sleep(1)
    
    pipeline_status.add_processing_file("test.pdf", "12345")
    time.sleep(2)
    
    pipeline_status.complete_file("test.pdf", success=True)
    
    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down status server...")