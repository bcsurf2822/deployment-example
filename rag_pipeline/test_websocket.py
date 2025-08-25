#!/usr/bin/env python3
"""
Test WebSocket server functionality.
"""

import json
import time
from status_server import start_status_server, pipeline_status

def test_websocket_events():
    """Test WebSocket event emission functionality."""
    print("[TEST] Starting WebSocket server test...")
    
    # Start the server
    server = start_status_server(8003)
    
    # Wait for server to start
    time.sleep(2)
    
    print("[TEST] Server started, testing status updates...")
    
    # Test basic status update
    pipeline_status.update(
        status="running", 
        pipeline_type="google_drive",
        check_interval=30
    )
    
    time.sleep(1)
    
    # Test file processing events
    print("[TEST] Testing file processing events...")
    pipeline_status.add_processing_file("test_document.pdf", "12345")
    
    time.sleep(1)
    
    # Test file completion
    pipeline_status.complete_file("test_document.pdf", success=True)
    
    time.sleep(1)
    
    # Test file failure
    pipeline_status.add_processing_file("error_document.pdf", "67890")
    time.sleep(0.5)
    pipeline_status.complete_file("error_document.pdf", success=False)
    
    time.sleep(1)
    
    print("[TEST] WebSocket events tested successfully!")
    print(f"[TEST] Current status: {json.dumps(pipeline_status.get(), indent=2)}")
    
    return server

def main():
    """Run the WebSocket test."""
    try:
        server = test_websocket_events()
        
        print("[TEST] Test completed. Server is running...")
        print("[TEST] Connect to:")
        print("[TEST]   HTTP Status: http://localhost:8003/status")
        print("[TEST]   Health Check: http://localhost:8003/health")
        print("[TEST]   WebSocket: ws://localhost:8004/socket.io/")
        print("[TEST]   Namespaces: /google_drive, /local_files, /pipeline")
        print("[TEST] Press Ctrl+C to stop...")
        
        # Keep the test running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[TEST] Shutting down test server...")
    except Exception as e:
        print(f"[TEST-ERROR] Test failed: {e}")

if __name__ == "__main__":
    main()