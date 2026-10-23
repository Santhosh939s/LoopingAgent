"""
LightAgent V1 - Coordinate Calibration Tool
Run this ONCE to set the text area coordinates for drag-select copying.

Usage:
    python calibrate.py

How it works:
    1. Minimizes your terminal automatically so it doesn't block the screen
    2. Automatically switches to Chrome (ChatGPT) for Steps 1 & 2
    3. You click:
       - Step 1: Top-Left corner of ChatGPT response area
       - Step 2: Bottom-Right corner of ChatGPT response area
    4. Automatically switches to Antigravity IDE for Steps 3 & 4
    5. You click:
       - Step 3: Top-Left corner of Antigravity text area
       - Step 4: Bottom-Right corner of Antigravity text area
    6. Automatically restores your terminal and saves coordinates to config.json
"""

import tkinter as tk
import json
import os
import sys
import time
import ctypes
import ctypes.wintypes

from config import Config
from logger import Logger
from window_manager import WindowManager

# Win32 API functions
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

SW_MINIMIZE = 6
SW_RESTORE = 9
SW_SHOW = 5

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Calibration steps definition
STEPS = [
    {
        "key": "chatgpt_area",
        "corner": "top_left",
        "target": "chrome",
        "title": "STEP 1 of 4",
        "instruction": "Click the TOP-LEFT corner of the\nChatGPT response text area",
        "color": "#7aa2f7",
    },
    {
        "key": "chatgpt_area",
        "corner": "bottom_right",
        "target": "chrome",
        "title": "STEP 2 of 4",
        "instruction": "Click the BOTTOM-RIGHT corner of the\nChatGPT response text area",
        "color": "#7aa2f7",
    },
    {
        "key": "antigravity_area",
        "corner": "top_left",
        "target": "antigravity",
        "title": "STEP 3 of 4",
        "instruction": "Click the TOP-LEFT corner of the\nAntigravity text area",
        "color": "#9ece6a",
    },
    {
        "key": "antigravity_area",
        "corner": "bottom_right",
        "target": "antigravity",
        "title": "STEP 4 of 4",
        "instruction": "Click the BOTTOM-RIGHT corner of the\nAntigravity text area",
        "color": "#9ece6a",
    },
]


class CalibrationTool:
    """Full-screen transparent overlay for clicking coordinates with auto-window management."""

    def __init__(self, terminal_hwnd=None, wm=None):
        self.terminal_hwnd = terminal_hwnd
        self.wm = wm
        self.step_index = 0
        self.results = {}

        self.root = tk.Tk()
        self.root.title("LightAgent Calibration")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.22)  # High clarity so text behind overlay is clear
        self.root.configure(bg="#000000")
        self.root.config(cursor="crosshair")

        # Instruction label
        self.label = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 22, "bold"),
            fg="#ffffff",
            bg="#000000",
            justify="center",
        )
        self.label.place(relx=0.5, rely=0.14, anchor="center")

        # Sub-instruction
        self.sub_label = tk.Label(
            self.root,
            text="Click on the screen to mark the position\nTAB to toggle window  |  ESC to cancel",
            font=("Segoe UI", 12),
            fg="#aaaaaa",
            bg="#000000",
            justify="center",
        )
        self.sub_label.place(relx=0.5, rely=0.23, anchor="center")

        # Coordinate display
        self.coord_label = tk.Label(
            self.root,
            text="",
            font=("Consolas", 14),
            fg="#e0af68",
            bg="#000000",
            justify="left",
        )
        self.coord_label.place(relx=0.5, rely=0.88, anchor="center")

        # Bind events
        self.root.bind("<Button-1>", self._on_click)
        self.root.bind("<Escape>", lambda e: self._cancel())
        self.root.bind("<Tab>", lambda e: self._toggle_window())
        self.root.bind("<Motion>", self._on_motion)

        # Show first step
        self._show_step()

    def _show_step(self):
        """Display the current step instruction."""
        if self.step_index >= len(STEPS):
            self._finish()
            return

        step = STEPS[self.step_index]
        self.label.config(
            text=f"{step['title']}\n\n{step['instruction']}",
            fg=step["color"],
        )

        # Show already captured coordinates
        captured = []
        for i, s in enumerate(STEPS[:self.step_index]):
            key = s["key"]
            corner = s["corner"]
            if key in self.results and corner in self.results[key]:
                x, y = self.results[key][corner]
                captured.append(f"  ✓ {s['title']}: ({x}, {y})")
        if captured:
            self.coord_label.config(text="\n".join(captured))

    def _on_motion(self, event):
        """Show live mouse coordinates."""
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        self.sub_label.config(
            text=f"Mouse: ({x}, {y})\nClick to capture  |  TAB to switch window  |  ESC to cancel"
        )

    def _toggle_window(self):
        """Allow user to manually switch between Chrome and Antigravity via TAB."""
        if not self.wm:
            return
        step = STEPS[self.step_index] if self.step_index < len(STEPS) else None
        target = "antigravity" if (step and step["target"] == "chrome") else "chrome"
        self._switch_app(target)

    def _switch_app(self, target):
        """Temporarily hide overlay to bring target window to front."""
        if not self.wm:
            return
        self.root.withdraw()
        time.sleep(0.15)
        self.wm.switch_to(target)
        time.sleep(0.4)
        self.root.deiconify()
        self.root.attributes("-topmost", True)

    def _on_click(self, event):
        """Capture a click coordinate."""
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()

        step = STEPS[self.step_index]
        key = step["key"]
        corner = step["corner"]

        if key not in self.results:
            self.results[key] = {}
        self.results[key][corner] = (x, y)

        print(f"[Calibrate] {step['title']}: ({x}, {y})")

        self.step_index += 1

        # If transitioning from ChatGPT (step 2) to Antigravity (step 3), auto-switch window
        if self.step_index == 2:
            print("[Calibrate] ChatGPT area saved. Switching to Antigravity IDE...")
            self.root.after(100, lambda: self._transition_to_antigravity())
        else:
            self._show_step()

    def _transition_to_antigravity(self):
        """Smoothly switch foreground to Antigravity before Step 3."""
        self._switch_app("antigravity")
        self._show_step()

    def _restore_terminal(self):
        """Bring the launching terminal window back to foreground."""
        if self.terminal_hwnd:
            try:
                user32.ShowWindow(self.terminal_hwnd, SW_RESTORE)
                user32.SetForegroundWindow(self.terminal_hwnd)
            except Exception:
                pass

    def _finish(self):
        """Save results to config.json and exit."""
        self.root.destroy()
        self._restore_terminal()

        # Load existing config
        config = {}
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Add coordinate data with aliases for prompt-driven loops
        for key in ["chatgpt_area", "antigravity_area"]:
            if key in self.results:
                coords = {
                    "top_left": list(self.results[key]["top_left"]),
                    "bottom_right": list(self.results[key]["bottom_right"]),
                }
                config[key] = coords
                if key == "chatgpt_area":
                    config["instructor_area"] = coords
                elif key == "antigravity_area":
                    config["listener_area"] = coords
                    config["worker_area"] = coords

        # Save
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        print("\n" + "=" * 50)
        print("  Calibration Complete!")
        print("=" * 50)
        print(f"\nSaved to: {CONFIG_PATH}")
        print(f"\nChatGPT area:")
        print(f"  Top-left:     {self.results.get('chatgpt_area', {}).get('top_left', '?')}")
        print(f"  Bottom-right: {self.results.get('chatgpt_area', {}).get('bottom_right', '?')}")
        print(f"\nAntigravity area:")
        print(f"  Top-left:     {self.results.get('antigravity_area', {}).get('top_left', '?')}")
        print(f"  Bottom-right: {self.results.get('antigravity_area', {}).get('bottom_right', '?')}")
        print(f"\nYou can now run: python main.py\n")

    def _cancel(self):
        """Cancel calibration."""
        print("[Calibrate] Cancelled by user.")
        self.root.destroy()
        self._restore_terminal()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


def get_current_terminal_hwnd():
    """Find the handle of the current terminal/console window."""
    hwnd = kernel32.GetConsoleWindow()
    if not hwnd or not user32.IsWindowVisible(hwnd):
        hwnd = user32.GetForegroundWindow()
    return hwnd


def main():
    print("=" * 50)
    print("  LightAgent - Coordinate Calibration")
    print("=" * 50)
    print()
    print("1. Terminal will automatically minimize in 2 seconds.")
    print("2. Google Chrome (ChatGPT) will be brought to the front.")
    print("3. Click Top-Left & Bottom-Right of ChatGPT response area.")
    print("4. Antigravity IDE will then be brought to the front.")
    print("5. Click Top-Left & Bottom-Right of Antigravity text area.")
    print("6. Press ESC at any time to cancel.")
    print()

    # Capture terminal handle before minimizing
    term_hwnd = get_current_terminal_hwnd()

    # Initialize WindowManager
    cfg = Config()
    log = Logger(debug=False)
    wm = WindowManager(cfg.get_all(), log)

    print("Minimizing terminal in 2 seconds...")
    time.sleep(2)

    # Minimize terminal
    if term_hwnd:
        try:
            user32.ShowWindow(term_hwnd, SW_MINIMIZE)
            # Also minimize console if different
            con_hwnd = kernel32.GetConsoleWindow()
            if con_hwnd and con_hwnd != term_hwnd:
                user32.ShowWindow(con_hwnd, SW_MINIMIZE)
        except Exception:
            pass

    # Bring Chrome (ChatGPT) to front
    time.sleep(0.3)
    wm.switch_to_chrome()
    time.sleep(0.4)

    # Start calibration tool
    tool = CalibrationTool(terminal_hwnd=term_hwnd, wm=wm)
    tool.run()


if __name__ == "__main__":
    main()
