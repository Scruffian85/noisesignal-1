"""
Scheduler wrapper script for automated NoiseSignal execution.
Handles retries, logging, and email notifications.
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main as main_module
from email_notifier import EmailNotifier
from config import (
    EMAIL_ENABLED, LOG_LEVEL, LOG_FILE, MAX_RETRIES, RETRY_DELAY,
    EXECUTION_TIMEOUT, PLAYLIST_TITLE
)

class ScheduledExecutor:
    def __init__(self):
        self.execution_start_time = datetime.now()
        self.setup_logging()

        # Initialize email notifier if enabled
        self.email_notifier = None
        if EMAIL_ENABLED:
            try:
                self.email_notifier = EmailNotifier()
                logging.info("Email notifications enabled")
            except Exception as e:
                logging.warning(f"Failed to initialize email notifier: {e}")
                self.email_notifier = None

    def setup_logging(self):
        """Configure logging for scheduled execution."""
        # Ensure log directory exists
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )

        logging.info(f"Scheduled execution started at {self.execution_start_time}")

    def run_with_timeout(self, timeout_seconds: int) -> bool:
        """Run the main process with a timeout."""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(f"Execution timed out after {timeout_seconds} seconds")

        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        try:
            main_module.main()
            return True
        except TimeoutError as e:
            logging.error(f"Execution timeout: {e}")
            return False
        except Exception as e:
            logging.error(f"Execution failed: {e}")
            return False
        finally:
            signal.alarm(0)  # Cancel the alarm

    def execute_with_retries(self) -> bool:
        """Execute main process with retry logic."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logging.info(f"Execution attempt {attempt}/{MAX_RETRIES}")

                # Run with timeout
                success = self.run_with_timeout(EXECUTION_TIMEOUT)

                if success:
                    logging.info("Execution completed successfully")
                    return True
                else:
                    logging.warning(f"Attempt {attempt} failed")

            except Exception as e:
                logging.error(f"Attempt {attempt} failed with exception: {e}")
                logging.error(traceback.format_exc())

            # Wait before retry (except on last attempt)
            if attempt < MAX_RETRIES:
                logging.info(f"Waiting {RETRY_DELAY} seconds before retry...")
                time.sleep(RETRY_DELAY)

        logging.error(f"All {MAX_RETRIES} attempts failed")
        return False

    def get_execution_summary(self) -> dict:
        """Get summary of the execution results."""
        try:
            # Try to read the results CSV to get track count
            import pandas as pd
            results_file = "emerging_playlist_results.csv"
            # main() doesn't rewrite the CSV when it finds nothing, so a file
            # older than this run is last week's results - don't resend it.
            if os.path.getmtime(results_file) < self.execution_start_time.timestamp():
                tracks = []
            else:
                tracks = pd.read_csv(results_file).to_dict('records')

            playlist_id = self.get_playlist_id()
            return {
                'success': True,
                'tracks_count': len(tracks),
                'tracks': tracks,
                'playlist_url': f"https://www.youtube.com/playlist?list={playlist_id}" if playlist_id else None
            }
        except Exception as e:
            logging.warning(f"Could not read execution results: {e}")
            return {
                'success': False,
                'tracks_count': 0,
                'tracks': [],
                'playlist_url': None
            }

    def get_playlist_id(self) -> Optional[str]:
        """Get the playlist ID from file."""
        try:
            with open("playlist_id.txt", "r") as f:
                return f.read().strip()
        except Exception:
            return None

    def send_notification(self, success: bool, summary: dict, error_message: str = None):
        """Send email notification about execution results."""
        if not self.email_notifier:
            return

        execution_time = self.execution_start_time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            if success and summary['tracks_count'] > 0:
                # Send weekly summary
                self.email_notifier.send_weekly_summary(
                    tracks=summary['tracks'],
                    playlist_url=summary['playlist_url'],
                    execution_time=execution_time
                )
            elif success and summary['tracks_count'] == 0:
                # Send notification that no new tracks were found
                self.email_notifier.send_success_notification(
                    tracks_added=0,
                    playlist_url=summary.get('playlist_url') or 'N/A',
                    execution_time=execution_time
                )
            else:
                # Send error alert
                self.email_notifier.send_error_alert(
                    error_type="Execution Failed",
                    error_message=error_message or "Unknown error occurred",
                    execution_time=execution_time
                )
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")

    def run(self):
        """Main execution method."""
        success = False
        error_message = None

        try:
            success = self.execute_with_retries()

            if success:
                summary = self.get_execution_summary()
                logging.info(f"Execution completed. Found {summary['tracks_count']} tracks.")
                self.send_notification(True, summary)
            else:
                error_message = "All retry attempts failed"
                self.send_notification(False, {}, error_message)

        except Exception as e:
            error_message = f"Critical error: {e}\n{traceback.format_exc()}"
            logging.error(error_message)
            self.send_notification(False, {}, error_message)

        finally:
            execution_duration = datetime.now() - self.execution_start_time
            logging.info(f"Scheduled execution completed. Duration: {execution_duration}")

        return success

def main():
    """Entry point for scheduled execution."""
    executor = ScheduledExecutor()
    success = executor.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()