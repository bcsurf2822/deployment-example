#!/usr/bin/env python3
"""
Main entry point for the Local Files RAG pipeline.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_watcher import LocalFilesWatcher

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
    
    try:
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