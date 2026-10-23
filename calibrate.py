"""
LightAgent V1 - Coordinate Calibration Tool
Run this ONCE to set the text area coordinates for drag-select copying.

Usage:
    python calibrate.py

How it works:
    1. Shows a transparent overlay on your screen
    2. You click 4 points in order:
       - ChatGPT response area: top-left corner
       - ChatGPT response area: bottom-right corner
       - Antigravity text area: top-left corner
       - Antigravity text area: bottom-right corner
    3. Coordinates are saved to config.json automatically
    4. The agent uses these coordinates to drag-select text

Tips:
    - Position your windows where they'll stay during automation
    - Click at the START of where text appears (top-left)
    - Click at the END of where text ends (bottom-right)
    - Leave some margin inside the text area
"""

import tkinter as tk
import json
import os
import sys

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Calibration steps
STEPS = [
    {
        "key": "chatgpt_area",
        "corner": "top_left",
        "title": "STEP 1 of 4",
        "instruction": "Click the TOP-LEFT corner of the\nChatGPT response text area",
        "color": "#7aa2f7",
    },
    {
        "key": "chatgpt_area",
        "corner": "bottom_right",
        "title": "STEP 2 of 4",
        "instruction": "Click the BOTTOM-RIGHT corner of the\nChatGPT response text area",
        "color": "#7aa2f7",
    },
    {
        "key": "antigravity_area",
        "corner": "top_left",
        "title": "STEP 3 of 4",
        "instruction": "Click the TOP-LEFT corner of the\nAntigravity text area",
        "color": "#9ece6a",
    },
    {
        "key": "antigravity_area",
        "corner": "bottom_right",
        "title": "STEP 4 of 4",
        "instruction": "Click the BOTTOM-RIGHT corner of the\nAntigravity text area",
        "color": "#9ece6a",
    },
]


class CalibrationTool:
    """Full-screen transparent overlay for clicking coordinates."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LightAgent Calibration")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.35)
        self.root.configure(bg="#000000")
        self.root.config(cursor="crosshair")

        self.step_index = 0
        self.results = {}

        # Instruction label
        self.label = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 22, "bold"),
            fg="#ffffff",
            bg="#000000",
            justify="center",
        )
        self.label.place(relx=0.5, rely=0.15, anchor="center")

        # Sub-instruction
        self.sub_label = tk.Label(
            self.root,
            text="Click on the screen to mark the position\nPress ESC to cancel",
            font=("Segoe UI", 12),
            fg="#888888",
            bg="#000000",
            justify="center",
        )
        self.sub_label.place(relx=0.5, rely=0.25, anchor="center")

        # Coordinate display
        self.coord_label = tk.Label(
            self.root,
            text="",
            font=("Consolas", 14),
            fg="#e0af68",
            bg="#000000",
            justify="left",
        )
        self.coord_label.place(relx=0.5, rely=0.85, anchor="center")

        # Bind events
        self.root.bind("<Button-1>", self._on_click)
        self.root.bind("<Escape>", lambda e: self._cancel())
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
        # Get absolute screen coordinates
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        self.sub_label.config(text=f"Mouse: ({x}, {y})\nClick to capture  |  ESC to cancel")

    def _on_click(self, event):
        """Capture a click coordinate."""
        # Get absolute screen coordinates (not relative to window)
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
        self._show_step()

    def _finish(self):
        """Save results to config.json and exit."""
        self.root.destroy()

        # Load existing config
        config = {}
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Add coordinate data
        # Format: {"chatgpt_area": {"top_left": [x,y], "bottom_right": [x,y]}, ...}
        for key in ["chatgpt_area", "antigravity_area"]:
            if key in self.results:
                config[key] = {
                    "top_left": list(self.results[key]["top_left"]),
                    "bottom_right": list(self.results[key]["bottom_right"]),
                }

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
        print(f"\nYou can now run: python main.py")

    def _cancel(self):
        """Cancel calibration."""
        print("[Calibrate] Cancelled by user.")
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


def main():
    print("=" * 50)
    print("  LightAgent - Coordinate Calibration")
    print("=" * 50)
    print()
    print("A transparent overlay will appear.")
    print("Click the 4 corners of your text areas.")
    print("Press ESC to cancel at any time.")
    print()

    tool = CalibrationTool()
    tool.run()


if __name__ == "__main__":
    main()
