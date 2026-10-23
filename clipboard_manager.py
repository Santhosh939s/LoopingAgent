"""
LightAgent V1 - Clipboard Manager
Handles copy/paste via keyboard shortcuts and mouse-drag selection.
NEVER stores or logs clipboard contents permanently.
"""

import time
import pyperclip
import pyautogui


class ClipboardManager:
    """Manages clipboard operations via Ctrl+C / Ctrl+V with safety checks."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.copy_delay = config.get("copy_delay", 0.5)
        self.paste_delay = config.get("paste_delay", 0.3)
        self.clipboard_timeout = config.get("clipboard_timeout", 5)

    def _get_clipboard(self):
        """Get current clipboard content safely."""
        try:
            return pyperclip.paste()
        except Exception:
            return ""

    def drag_select(self, area_config):
        """
        Select text by mouse-dragging from top-left to bottom-right.
        Args:
            area_config: dict with 'top_left': [x,y] and 'bottom_right': [x,y]
        """
        if not area_config:
            self.logger.log("ERROR: No area coordinates configured. Run calibrate.py first.")
            return False

        top_left = area_config.get("top_left")
        bottom_right = area_config.get("bottom_right")

        if not top_left or not bottom_right:
            self.logger.log("ERROR: Incomplete area coordinates. Run calibrate.py first.")
            return False

        x1, y1 = top_left
        x2, y2 = bottom_right

        self.logger.log(f"Drag selecting: ({x1},{y1}) -> ({x2},{y2})")

        # Move to start position
        pyautogui.moveTo(x1, y1, duration=0.15)
        time.sleep(0.1)

        # Click and drag to end position
        pyautogui.click(x1, y1)
        time.sleep(0.05)
        pyautogui.moveTo(x1, y1, duration=0.05)
        pyautogui.mouseDown(button='left')
        time.sleep(0.05)
        pyautogui.moveTo(x2, y2, duration=0.3)
        time.sleep(0.05)
        pyautogui.mouseUp(button='left')
        time.sleep(0.2)

        self.logger.log("Drag select complete.")
        return True

    def drag_select_and_copy(self, area_config):
        """
        Drag-select text in an area, then Ctrl+C to copy.
        Args:
            area_config: dict with 'top_left' and 'bottom_right' coordinates.
        Returns: clipboard content string, or None on failure.
        """
        success = self.drag_select(area_config)
        if not success:
            return None

        # Small pause before copy
        time.sleep(0.15)

        return self.copy_current()

    def copy_current(self):
        """
        Press Ctrl+C and wait for clipboard to update.
        Returns the new clipboard content, or None if clipboard didn't change.
        """
        # Save previous clipboard value
        old_clipboard = self._get_clipboard()

        self.logger.log("Copying (Ctrl+C)...")

        # Press Ctrl+C
        pyautogui.hotkey("ctrl", "c")

        # Wait for clipboard to update
        start_time = time.time()
        timeout = self.clipboard_timeout

        while time.time() - start_time < timeout:
            time.sleep(0.2)
            new_clipboard = self._get_clipboard()

            # Check if clipboard changed or has valid content
            if new_clipboard and new_clipboard != old_clipboard:
                self.logger.log_clipboard_size(new_clipboard)
                return new_clipboard

        # Timeout: check if clipboard has any content at all
        final = self._get_clipboard()
        if final and final.strip():
            self.logger.log("Clipboard did not change, but has content.")
            self.logger.log_clipboard_size(final)
            return final

        self.logger.log("ERROR: Clipboard did not update within timeout.")
        return None

    def paste_current(self):
        """Press Ctrl+V to paste current clipboard content."""
        self.logger.log("Pasting (Ctrl+V)...")
        pyautogui.hotkey("ctrl", "v")
        time.sleep(self.paste_delay)

    def press_enter(self):
        """Press Enter key."""
        self.logger.log("Pressing Enter...")
        pyautogui.press("enter")

    def paste_and_enter(self):
        """Paste, wait briefly, then press Enter."""
        self.paste_current()
        time.sleep(self.paste_delay)
        self.press_enter()

    def select_all(self):
        """Press Ctrl+A to select all content."""
        self.logger.log("Selecting all (Ctrl+A)...")
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)

    def select_all_and_copy(self):
        """Press Ctrl+A then Ctrl+C."""
        self.select_all()
        return self.copy_current()
