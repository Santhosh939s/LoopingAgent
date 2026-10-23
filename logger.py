"""
LightAgent V1 - Logger
Lightweight logging to file and GUI callback.
NEVER logs actual clipboard content - only character count.
"""

import os
import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class AgentLogger:
    """Simple logger that writes to a log file and optionally calls a GUI callback."""

    def __init__(self, gui_callback=None):
        """
        Args:
            gui_callback: Optional function(message: str) to display log in GUI.
        """
        self.gui_callback = gui_callback

        # Ensure log directory exists
        os.makedirs(LOG_DIR, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(LOG_DIR, f"lightagent_{timestamp}.log")

    def log(self, message):
        """Log a message with timestamp."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{now}] {message}"

        # Write to file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass  # Don't crash on log failure

        # Send to GUI
        if self.gui_callback:
            try:
                self.gui_callback(line)
            except Exception:
                pass

        # Also print to console safely on Windows
        try:
            print(line)
        except UnicodeEncodeError:
            try:
                print(line.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8"))
            except Exception:
                pass

    def log_clipboard_size(self, content):
        """Log clipboard content size WITHOUT logging the actual content."""
        if content:
            self.log(f"Clipboard: {len(content)} characters")
        else:
            self.log("Clipboard: empty")
