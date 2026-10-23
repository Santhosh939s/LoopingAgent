"""
LightAgent V1 - Window Manager
Finds and activates existing windows by title. NEVER launches applications.
Uses ctypes Win32 API for reliable window switching on Windows.
"""

import time
import ctypes
import ctypes.wintypes

# Win32 API functions
user32 = ctypes.windll.user32

EnumWindows = user32.EnumWindows
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
IsWindowVisible = user32.IsWindowVisible
SetForegroundWindow = user32.SetForegroundWindow
ShowWindow = user32.ShowWindow
IsIconic = user32.IsIconic  # Check if minimized
BringWindowToTop = user32.BringWindowToTop

# ShowWindow constants
SW_RESTORE = 9
SW_SHOW = 5

# Callback type for EnumWindows
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)


def _enum_windows():
    """Enumerate all visible windows with titles. Returns list of (hwnd, title)."""
    results = []

    def callback(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if title.strip():
                    results.append((hwnd, title))
        return True

    EnumWindows(WNDENUMPROC(callback), 0)
    return results


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
        Returns the hwnd (window handle) or None.
        """
        try:
            windows = _enum_windows()
            for hwnd, title in windows:
                if title_substring.lower() in title.lower():
                    return hwnd
        except Exception as e:
            self.logger.log(f"ERROR finding window '{title_substring}': {e}")

        return None

    def _activate_window(self, hwnd, name):
        """Bring a window to the foreground using Win32 API."""
        try:
            # If minimized, restore it first
            if IsIconic(hwnd):
                ShowWindow(hwnd, SW_RESTORE)
                time.sleep(0.3)

            # Try SetForegroundWindow (most reliable)
            # Trick: attach to foreground thread to bypass Windows restriction
            try:
                foreground_hwnd = user32.GetForegroundWindow()
                foreground_tid = user32.GetWindowThreadProcessId(foreground_hwnd, None)
                current_tid = ctypes.windll.kernel32.GetCurrentThreadId()

                if foreground_tid != current_tid:
                    user32.AttachThreadInput(current_tid, foreground_tid, True)
                    SetForegroundWindow(hwnd)
                    BringWindowToTop(hwnd)
                    user32.AttachThreadInput(current_tid, foreground_tid, False)
                else:
                    SetForegroundWindow(hwnd)
                    BringWindowToTop(hwnd)
            except Exception:
                # Fallback: just try SetForegroundWindow directly
                SetForegroundWindow(hwnd)

            ShowWindow(hwnd, SW_SHOW)
            time.sleep(0.5)  # Give Windows time to switch

            self.logger.log(f"Switched to {name}")
            return True

        except Exception as e:
            self.logger.log(f"ERROR activating {name}: {e}")
            return False

    def switch_to_chrome(self):
        """Find and activate the Chrome window. Returns True on success."""
        hwnd = self._find_window(self.chrome_title)
        if hwnd is None:
            # Try fallback search terms
            for alt in ["Chrome", "ChatGPT", "Google Chrome"]:
                hwnd = self._find_window(alt)
                if hwnd:
                    break
        if hwnd is None:
            self.logger.log(f"Chrome window not found. (Looking for: '{self.chrome_title}')")
            return False
        return self._activate_window(hwnd, "Chrome")

    def switch_to_antigravity(self):
        """Find and activate the Antigravity window. Returns True on success."""
        hwnd = self._find_window(self.antigravity_title)
        if hwnd is None:
            # Try fallback search terms
            for alt in ["Antigravity", "Visual Studio Code", "Code"]:
                hwnd = self._find_window(alt)
                if hwnd:
                    break
        if hwnd is None:
            self.logger.log(f"Antigravity window not found. (Looking for: '{self.antigravity_title}')")
            return False
        return self._activate_window(hwnd, "Antigravity")

    def switch_to(self, target):
        """
        Switch to a named target or any open window matching target.
        Args:
            target: "chrome", "antigravity", "whatsapp", "notepad", etc.
        Returns: True on success, False on failure.
        """
        target_lower = target.lower().strip()
        if target_lower == "chrome":
            return self.switch_to_chrome()
        elif target_lower == "antigravity":
            return self.switch_to_antigravity()

        # Generic lookup for ANY open application
        hwnd = self._find_window(target)
        if hwnd:
            return self._activate_window(hwnd, target)

        # Check fuzzy matching among all open windows
        windows = _enum_windows()
        for h, title in windows:
            if target_lower in title.lower():
                return self._activate_window(h, title)

        self.logger.log(f"Window matching '{target}' not found.")
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
        try:
            return [title for _, title in _enum_windows()]
        except Exception:
            return []
