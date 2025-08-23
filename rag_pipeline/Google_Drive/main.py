import os
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import atexit
import signal

# Add parent directory to path for status_server import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import status_server first so it's available for drive_watcher
from status_server import start_status_server, pipeline_status
from supabase_status import init_status_tracker
from drive_watcher import GoogleDriveWatcher

def main():
    """
    Main entry point for the RAG pipeline.
    """

    # Directory where script is located
    script_dir = Path(__file__).resolve().parent

    # parse command line arguments
    parser = argparse.ArgumentParser(description="Google Drive RAG Pipeline")
    parser.add_argument('--credentials', type=str, default=str(script_dir / 'credentials.json'),
                        help='Path to Google Drive API credentials file')
    parser.add_argument('--token', type=str, default=str(script_dir / 'token.json'),
                        help='Path to Google Drive API token file')
    parser.add_argument('--config', type=str, default=str(script_dir / 'config.json'),
                        help='Path to the configuration JSON file')
    parser.add_argument('--interval', type=int, default=60,
                        help='Interval in seconds between checks for changes')
    parser.add_argument('--folder-id', type=str, default=os.getenv('RAG_WATCH_FOLDER_ID'),
                        help='ID of the specific Google Drive folder to watch (and its subfolders)')
    parser.add_argument('--single-run', action='store_true',
                        help='Run once and exit instead of continuous monitoring')
                        
    args = parser.parse_args()
    
    # Check RUN_MODE environment variable if --single-run not specified
    if not args.single_run and os.getenv('RUN_MODE') == 'single':
        args.single_run = True

    # Initialize Supabase status tracker
    status_tracker = None
    
    def cleanup():
        """Clean up on exit."""
        if status_tracker:
            status_tracker.stop()
    
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
    
    try:
        # Initialize Supabase status tracker - use existing pipeline ID
        pipeline_id = "google-drive-pipeline"
        status_tracker = init_status_tracker(pipeline_id, "google_drive")
        
        # Start status tracking (unless in single-run mode)
        if not args.single_run:
            # Start the old status server for backward compatibility (will phase out)
            start_status_server(port=8003)
            pipeline_status.update(
                status="running",
                pipeline_type="google_drive",
                check_interval=args.interval,
                folder_id=args.folder_id
            )
            
            # Start Supabase status tracking
            status_tracker.start({
                "folder_id": args.folder_id,
                "check_interval": args.interval,
                "status": "running"
            })
        
        # Start Google Drive Watcher
        watcher = GoogleDriveWatcher(
            credentials_path=args.credentials,
            token_path=args.token,
            config_path=args.config,
            folder_id=args.folder_id
        )
        
        if args.single_run:
            # Run once and exit
            print("Running in single-run mode...")
            stats = watcher.check_for_changes()
            
            print(f"\nSingle run completed:")
            print(f"  Files processed: {stats['files_processed']}")
            print(f"  Files deleted: {stats['files_deleted']}")
            print(f"  Errors: {stats['errors']}")
            print(f"  Duration: {stats['duration']:.2f} seconds")
            
            # Exit with appropriate code
            if stats['errors'] > 0:
                sys.exit(1)  # Exit with error if there were any errors
            else:
                sys.exit(0)  # Success
        else:
            # Watch for changes continuously with status updates
            import time
            
            while True:
                # Update status before check
                next_check = datetime.now() + timedelta(seconds=args.interval)
                pipeline_status.update(
                    status="running",
                    is_checking=True,
                    last_check_time=datetime.now().isoformat(),
                    next_check_time=next_check.isoformat()
                )
                
                # Run the check
                stats = watcher.check_for_changes()
                
                # Update status after check
                pipeline_status.update(
                    status="running",
                    is_checking=False,
                    total_processed=pipeline_status.data.get("total_processed", 0) + stats['files_processed'],
                    total_failed=pipeline_status.data.get("total_failed", 0) + stats['errors']
                )
                
                # Log if there were changes
                if stats['files_processed'] > 0 or stats['files_deleted'] > 0:
                    print(f"Change check completed: {stats['files_processed']} files processed, "
                          f"{stats['files_deleted']} files deleted, {stats['errors']} errors, "
                          f"duration: {stats['duration']:.2f}s")
                
                # Wait for next check
                print(f"Waiting {args.interval} seconds until next check...")
                time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\nShutting down Google Drive watcher...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()