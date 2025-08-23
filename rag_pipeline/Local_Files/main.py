#!/usr/bin/env python3
"""
Main entry point for the Local Files RAG pipeline.
"""

import os
import sys
import argparse
from pathlib import Path
import atexit
import signal

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_watcher import LocalFilesWatcher
from supabase_status import init_status_tracker

def main():
    """Main function to run the Local Files watcher."""
    parser = argparse.ArgumentParser(description='Local Files RAG Pipeline Watcher')
    parser.add_argument(
        '--directory',
        type=str,
        help='Directory to watch for file changes',
        default=None
    )
    parser.add_argument(
        '--interval',
        type=int,
        help='Check interval in seconds (default: 60)',
        default=60
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file',
        default=None
    )
    parser.add_argument(
        '--single-run',
        action='store_true',
        help='Run once and exit instead of continuous monitoring'
    )
    
    args = parser.parse_args()
    
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
        pipeline_id = "local-files-pipeline"
        status_tracker = init_status_tracker(pipeline_id, "local_files")
        
        # Get watch directory
        watch_dir = args.directory or os.getenv('RAG_WATCH_DIRECTORY', '/app/Local_Files/data')
        
        # Start status tracking (unless in single-run mode)
        if not args.single_run:
            status_tracker.start({
                "watch_directory": watch_dir,
                "check_interval": args.interval,
                "status": "running"
            })
        
        # Create watcher instance
        watcher = LocalFilesWatcher(
            watch_directory=args.directory,
            config_path=args.config
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
            # Run continuous monitoring
            watcher.watch_for_changes(interval_seconds=args.interval)
            
    except KeyboardInterrupt:
        print("\nShutting down Local Files watcher...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()