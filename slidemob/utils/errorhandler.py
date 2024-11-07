import sys
import traceback
from datetime import datetime
import os
from pathlib import Path

def setup_error_logging():
    # Get the slidemob package directory
    current_dir = Path(__file__).parent.parent  # Go up one level from utils to slidemob
    log_dir = current_dir / "error_logs"
    
    # Create error_logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log file path with timestamp to avoid overwrites
    log_file = log_dir / f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            error_msg = f"""
=== Error Report [{timestamp}] ===
Type: {exc_type.__name__}
Message: {exc_value}
Traceback:
{''.join(traceback.format_tb(exc_traceback))}
==============================
"""
            # Use with statement to ensure proper file handling
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(error_msg)
                f.flush()  # Force write to disk
                os.fsync(f.fileno())  # Ensure it's written to disk
                
        except Exception as e:
            # If we can't write to the log file, print to stderr
            print(f"Error writing to log file: {e}", file=sys.stderr)
            print(f"Attempted to write to: {log_file}", file=sys.stderr)
            
        # Call the original excepthook to maintain default behavior
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
        # Force flush stdout and stderr
        sys.stdout.flush()
        sys.stderr.flush()
    
    sys.excepthook = exception_handler