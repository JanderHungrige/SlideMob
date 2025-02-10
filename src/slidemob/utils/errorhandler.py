from datetime import datetime
import os
from pathlib import Path
import sys
import traceback


def setup_error_logging():
    # Get the slidemob package directory
    current_dir = Path(__file__).parent.parent  # Go up one level from utils to slidemob
    log_dir = current_dir / "error_logs"

    # Create error_logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    print(f"Created error log directory at: {log_dir}")

    # Create log file path with timestamp to avoid overwrites
    log_file = log_dir / f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    print(f"Will log errors to: {log_file}")

    def exception_handler(exc_type, exc_value, exc_traceback):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_msg = f"""
=== Error Report [{timestamp}] ===
Type: {exc_type.__name__}
Message: {exc_value}
Traceback:
{''.join(traceback.format_tb(exc_traceback))}
==============================
"""
            print(f"Attempting to log error to: {log_file}")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(error_msg)
                f.flush()
                os.fsync(f.fileno())
            print("Error successfully logged")

        except Exception as e:
            print(f"Error writing to log file: {e}", file=sys.stderr)
            print(f"Attempted to write to: {log_file}", file=sys.stderr)

        # Call the original excepthook to maintain default behavior
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler
    return log_dir  # Return the log directory path for verification
