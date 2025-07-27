import os
import argparse
import sys
from pathlib import Path

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

    try:
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
            # Watch for changes continuously
            watcher.watch_for_changes(interval_seconds=args.interval)
            
    except KeyboardInterrupt:
        print("\nShutting down Google Drive watcher...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()