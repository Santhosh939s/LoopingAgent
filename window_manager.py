"""
LightAgent V1 - Window Manager
Finds and activates existing windows by title. NEVER launches applications.
Uses pygetwindow for lightweight Windows window management.
"""

import time

try:
    import pygetwindow as gw
except ImportError:
    gw = None
    print("[WindowManager] pygetwindow not installed. Run: pip install pygetwindow")


class WindowManager:
    """Manages finding and switching to existing windows. Never launches anything."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.chrome_title = config.get("chrome_title", "Google Chrome")
        self.antigravity_title = config.get("antigravity_title", "Antigravity")

    def _find_window(self, title_substring):
        """
        Find an open window whose title contains the given substring.
        Returns the window object or None.
        """
        if gw is None:
            self.logger.log("ERROR: pygetwindow not available.")
            return None

        try:
            windows = gw.getWindowsWithTitle(title_substring)
            if windows:
                # Return the first matching window
                return windows[0]
        except Exception as e:
            self.logger.log(f"ERROR finding window '{title_substring}': {e}")

        return None

    def _activate_window(self, window, name):
        """Bring a window to the foreground."""
        try:
            # If minimized, restore it first
            if window.isMinimized:
                window.restore()
                time.sleep(0.3)

            # Activate (bring to front)
            window.activate()
            time.sleep(0.5)  # Give Windows time to switch

            self.logger.log(f"Switched to {name}")
            return True

        except Exception as e:
            self.logger.log(f"ERROR activating {name}: {e}")
            return False

    def switch_to_chrome(self):
        """Find and activate the Chrome window. Returns True on success."""
        window = self._find_window(self.chrome_title)
        if window is None:
            self.logger.log(f"Chrome window not found. (Looking for: '{self.chrome_title}')")
            return False
        return self._activate_window(window, "Chrome")

    def switch_to_antigravity(self):
        """Find and activate the Antigravity window. Returns True on success."""
        window = self._find_window(self.antigravity_title)
        if window is None:
            self.logger.log(f"Antigravity window not found. (Looking for: '{self.antigravity_title}')")
            return False
        return self._activate_window(window, "Antigravity")

    def switch_to(self, target):
        """
        Switch to a named target.
        Args:
            target: "chrome" or "antigravity"
        Returns: True on success, False on failure.
        """
        target = target.lower().strip()
        if target == "chrome":
            return self.switch_to_chrome()
        elif target == "antigravity":
            return self.switch_to_antigravity()
        else:
            self.logger.log(f"Unknown switch target: '{target}'")
            return False

    def check_windows_exist(self):
        """
        Check that both Chrome and Antigravity windows are open.
        Returns (chrome_found, antigravity_found) tuple.
        """
        chrome = self._find_window(self.chrome_title) is not None
        antigravity = self._find_window(self.antigravity_title) is not None
        return chrome, antigravity

    def list_all_windows(self):
        """List all open window titles (for debugging)."""
        if gw is None:
            return []
        try:
            return [w.title for w in gw.getAllWindows() if w.title.strip()]
        except Exception:
            return []
