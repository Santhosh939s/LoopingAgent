"""
LightAgent V1 - Main Entry Point
Launches the Tkinter GUI and starts the prompt-driven automation agent.
Press ESC at any time for emergency stop.
"""

import sys
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import keyboard  # For global ESC hotkey

from config import load_config
from agent import LightAgent
from workflow import list_workflows
from prompt_parser import parse_prompt, build_workflow_from_prompt


# ─── Color Palette ───────────────────────────────────────────────────────────
BG_DARK       = "#1a1b26"
BG_PANEL      = "#24283b"
BG_INPUT      = "#1f2335"
FG_TEXT        = "#c0caf5"
FG_DIM        = "#565f89"
FG_ACCENT     = "#7aa2f7"
FG_GREEN      = "#9ece6a"
FG_YELLOW     = "#e0af68"
FG_RED        = "#f7768e"
FG_CYAN       = "#7dcfff"
BTN_START     = "#9ece6a"
BTN_PAUSE     = "#e0af68"
BTN_STOP      = "#f7768e"
BTN_TEXT_DARK = "#1a1b26"
BORDER        = "#3b4261"


class LightAgentGUI:
    """Minimal Tkinter GUI for LightAgent with Prompt-Driven Automation."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LightAgent V1 — LoopingAgent")
        self.root.geometry("540x720")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        # Try to set dark title bar on Windows 10/11
        try:
            self.root.attributes("-alpha", 0.97)
        except Exception:
            pass

        # Agent (pass GUI log callback)
        self.agent = LightAgent(gui_log_callback=self._log_to_gui_threadsafe)
        self.agent.on_status_change = self._update_status_threadsafe

        # Default prompt
        self.default_prompt = "ChatGPT in Chrome is instructor, Antigravity is listener"
        self.workflow_name = "ChatGPT <-> Antigravity Loop"

        # Build UI
        self._build_ui()

        # Initialize workflow from prompt
        self._sync_workflow_from_prompt()

        # Global ESC hotkey for emergency stop
        self._setup_esc_hotkey()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _sync_workflow_from_prompt(self):
        """Build and load workflow from current prompt text."""
        prompt = self.prompt_var.get().strip()
        if not prompt:
            prompt = self.default_prompt
        open_wins = self.agent.wm.list_all_windows()
        wf = build_workflow_from_prompt(prompt, self.agent.config, open_windows)
        self.agent.set_dynamic_workflow(wf)
        self.workflow_name = wf.get("name", "Dynamic Loop")
        if hasattr(self, "workflow_label"):
            self.workflow_label.config(text=self.workflow_name)

    def _build_ui(self):
        """Build the GUI layout."""
        root = self.root

        # ─── Header ──────────────────────────────────────────────────────
        header_frame = tk.Frame(root, bg=BG_DARK, pady=8)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text="⚡ LightAgent",
            font=("Segoe UI", 18, "bold"),
            fg=FG_ACCENT,
            bg=BG_DARK,
        ).pack()

        tk.Label(
            header_frame,
            text="Prompt-Driven Autonomous Desktop Loop",
            font=("Segoe UI", 9),
            fg=FG_DIM,
            bg=BG_DARK,
        ).pack()

        # ─── Prompt Input Panel (Option A) ───────────────────────────────
        prompt_frame = tk.Frame(root, bg=BG_PANEL, padx=14, pady=10, highlightbackground=BORDER, highlightthickness=1)
        prompt_frame.pack(fill="x", padx=16, pady=(0, 8))

        # Title row
        p_row1 = tk.Frame(prompt_frame, bg=BG_PANEL)
        p_row1.pack(fill="x", pady=(0, 4))
        tk.Label(
            p_row1,
            text="Prompt (Who instructs & who executes):",
            font=("Segoe UI", 9, "bold"),
            fg=FG_ACCENT,
            bg=BG_PANEL,
        ).pack(side="left")

        # Entry box
        self.prompt_var = tk.StringVar(value=self.default_prompt)
        self.prompt_entry = tk.Entry(
            prompt_frame,
            textvariable=self.prompt_var,
            font=("Segoe UI", 10),
            bg=BG_INPUT,
            fg=FG_TEXT,
            insertbackground=FG_TEXT,
            relief="flat",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.prompt_entry.pack(fill="x", ipady=3, pady=(0, 5))
        self.prompt_entry.bind("<KeyRelease>", lambda e: self._on_prompt_change())

        # Detected roles preview
        self.parse_preview_label = tk.Label(
            prompt_frame,
            text="Instructor: Chrome  →  Worker: Antigravity",
            font=("Segoe UI", 9),
            fg=FG_GREEN,
            bg=BG_PANEL,
            anchor="w",
        )
        self.parse_preview_label.pack(fill="x")

        # ─── Status Panel ────────────────────────────────────────────────
        status_frame = tk.Frame(root, bg=BG_PANEL, padx=16, pady=10, highlightbackground=BORDER, highlightthickness=1)
        status_frame.pack(fill="x", padx=16, pady=(0, 8))

        # Status row
        row1 = tk.Frame(status_frame, bg=BG_PANEL)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Status:", font=("Segoe UI", 10, "bold"), fg=FG_DIM, bg=BG_PANEL, width=10, anchor="w").pack(side="left")
        self.status_label = tk.Label(row1, text="READY", font=("Segoe UI Semibold", 11), fg=FG_GREEN, bg=BG_PANEL, anchor="w")
        self.status_label.pack(side="left", fill="x")

        # Current step row
        row2 = tk.Frame(status_frame, bg=BG_PANEL)
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Current:", font=("Segoe UI", 10, "bold"), fg=FG_DIM, bg=BG_PANEL, width=10, anchor="w").pack(side="left")
        self.current_label = tk.Label(row2, text="Waiting", font=("Segoe UI", 10), fg=FG_TEXT, bg=BG_PANEL, anchor="w")
        self.current_label.pack(side="left", fill="x")

        # Workflow row
        row3 = tk.Frame(status_frame, bg=BG_PANEL)
        row3.pack(fill="x", pady=2)
        tk.Label(row3, text="Workflow:", font=("Segoe UI", 10, "bold"), fg=FG_DIM, bg=BG_PANEL, width=10, anchor="w").pack(side="left")
        self.workflow_label = tk.Label(row3, text=self.workflow_name, font=("Segoe UI", 10), fg=FG_CYAN, bg=BG_PANEL, anchor="w")
        self.workflow_label.pack(side="left", fill="x")

        # Loop count row
        row4 = tk.Frame(status_frame, bg=BG_PANEL)
        row4.pack(fill="x", pady=2)
        tk.Label(row4, text="Loops:", font=("Segoe UI", 10, "bold"), fg=FG_DIM, bg=BG_PANEL, width=10, anchor="w").pack(side="left")
        self.loop_label = tk.Label(row4, text="0", font=("Segoe UI", 10), fg=FG_TEXT, bg=BG_PANEL, anchor="w")
        self.loop_label.pack(side="left", fill="x")

        # ─── Buttons ─────────────────────────────────────────────────────
        btn_frame = tk.Frame(root, bg=BG_DARK, pady=4)
        btn_frame.pack(fill="x", padx=16)

        btn_style = {"font": ("Segoe UI Semibold", 11), "width": 10, "height": 1, "bd": 0, "cursor": "hand2", "relief": "flat"}

        self.start_btn = tk.Button(
            btn_frame, text="▶  START", bg=BTN_START, fg=BTN_TEXT_DARK,
            command=self._on_start, activebackground="#b5e07d", **btn_style
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.pause_btn = tk.Button(
            btn_frame, text="⏸  PAUSE", bg=BTN_PAUSE, fg=BTN_TEXT_DARK,
            command=self._on_pause, activebackground="#e8c078", state="disabled", **btn_style
        )
        self.pause_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = tk.Button(
            btn_frame, text="⏹  STOP", bg=BTN_STOP, fg=BTN_TEXT_DARK,
            command=self._on_stop, activebackground="#f99aac", state="disabled", **btn_style
        )
        self.stop_btn.pack(side="left")

        # ─── ESC hint ────────────────────────────────────────────────────
        tk.Label(
            root, text="Press ESC at any time for emergency stop",
            font=("Segoe UI", 8), fg=FG_DIM, bg=BG_DARK
        ).pack(pady=(2, 0))

        # ─── Activity Log ────────────────────────────────────────────────
        log_header = tk.Frame(root, bg=BG_DARK, pady=4)
        log_header.pack(fill="x", padx=16)
        tk.Label(log_header, text="Activity", font=("Segoe UI", 10, "bold"), fg=FG_DIM, bg=BG_DARK).pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(
            root,
            width=58,
            height=14,
            bg=BG_INPUT,
            fg=FG_TEXT,
            font=("Consolas", 9),
            insertbackground=FG_TEXT,
            selectbackground=FG_ACCENT,
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1,
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Configure log text tags for colored entries
        self.log_text.tag_config("error", foreground=FG_RED)
        self.log_text.tag_config("success", foreground=FG_GREEN)
        self.log_text.tag_config("info", foreground=FG_CYAN)

    def _on_prompt_change(self):
        """Update live preview when the user edits the prompt."""
        prompt = self.prompt_var.get().strip()
        open_wins = self.agent.wm.list_all_windows()
        roles = parse_prompt(prompt, open_wins)
        inst = roles["instructor"]
        worker = roles["listener"]
        self.parse_preview_label.config(text=f"Instructor: {inst}  →  Worker: {worker}")

    def _log_to_gui(self, message):
        """Append a message to the activity log (must be called from main thread)."""
        self.log_text.configure(state="normal")

        tag = None
        msg_lower = message.lower()
        if "error" in msg_lower:
            tag = "error"
        elif "switched" in msg_lower or "completed" in msg_lower or "started" in msg_lower:
            tag = "success"
        elif "waiting" in msg_lower or "clipboard" in msg_lower:
            tag = "info"

        if tag:
            self.log_text.insert("end", message + "\n", tag)
        else:
            self.log_text.insert("end", message + "\n")

        self.log_text.see("end")
        self.log_text.configure(state="disabled")

        if self.agent.runner:
            self.loop_label.config(text=str(self.agent.runner.loop_count))

    def _log_to_gui_threadsafe(self, message):
        """Thread-safe version: schedule log update on main thread."""
        try:
            self.root.after(0, self._log_to_gui, message)
        except Exception:
            pass

    def _update_status(self, status):
        """Update status label (must be called from main thread)."""
        status_upper = status.upper()

        if "ERROR" in status_upper:
            self.status_label.config(text=status, fg=FG_RED)
            self.current_label.config(text=status)
            self._set_buttons_stopped()
        elif "RUNNING" in status_upper:
            self.status_label.config(text="RUNNING", fg=FG_GREEN)
        elif "PAUSED" in status_upper:
            self.status_label.config(text="PAUSED", fg=FG_YELLOW)
            self.current_label.config(text="Paused")
        elif "STOPPED" in status_upper or "COMPLETED" in status_upper:
            self.status_label.config(text=status, fg=FG_DIM)
            self.current_label.config(text="Idle")
            self._set_buttons_stopped()
        elif "EMERGENCY" in status_upper:
            self.status_label.config(text="EMERGENCY STOP", fg=FG_RED)
            self.current_label.config(text="Stopped by ESC")
            self._set_buttons_stopped()
        else:
            self.current_label.config(text=status)

    def _update_status_threadsafe(self, status):
        """Thread-safe status update."""
        try:
            self.root.after(0, self._update_status, status)
        except Exception:
            pass

    def _set_buttons_running(self):
        """Set button states for running."""
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="⏸  PAUSE")
        self.stop_btn.config(state="normal")
        self.prompt_entry.config(state="disabled")

    def _set_buttons_paused(self):
        """Set button states for paused."""
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="▶  RESUME")
        self.stop_btn.config(state="normal")

    def _set_buttons_stopped(self):
        """Set button states for stopped."""
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="⏸  PAUSE")
        self.stop_btn.config(state="disabled")
        self.prompt_entry.config(state="normal")

    def _on_start(self):
        """Handle START button click."""
        # Synchronize dynamic workflow from prompt
        self._sync_workflow_from_prompt()

        if self.agent.runner is None:
            messagebox.showerror("Error", "Could not build workflow from prompt.")
            return

        # Wire up status callback again
        self.agent.runner.on_status_change = self._update_status_threadsafe

        success = self.agent.start()
        if success:
            self._set_buttons_running()
            self._update_status("RUNNING")
        else:
            status = self.agent.get_status()
            self._update_status(status)

    def _on_pause(self):
        """Handle PAUSE/RESUME button click."""
        if self.agent.is_paused:
            self.agent.resume()
            self._set_buttons_running()
            self._update_status("RUNNING")
        else:
            self.agent.pause()
            self._set_buttons_paused()
            self._update_status("PAUSED")

    def _on_stop(self):
        """Handle STOP button click."""
        self.agent.stop()
        self._set_buttons_stopped()
        self._update_status("STOPPED")

    def _setup_esc_hotkey(self):
        """Register global ESC key for emergency stop."""
        try:
            keyboard.on_press_key("esc", lambda _: self._emergency_stop())
        except Exception as e:
            self._log_to_gui(f"[Warning] Could not register ESC hotkey: {e}")

    def _emergency_stop(self):
        """Emergency stop triggered by ESC key."""
        if self.agent.is_running:
            self.agent.stop()
            self._update_status_threadsafe("EMERGENCY STOP")
            self._log_to_gui_threadsafe("[!] Emergency stop triggered (ESC)")
            try:
                self.root.after(0, self._set_buttons_stopped)
            except Exception:
                pass

    def _on_close(self):
        """Handle window close."""
        self.agent.stop()
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()


def main():
    """Entry point."""
    print("=" * 50)
    print("  LightAgent V1 — LoopingAgent")
    print("  Prompt-Driven Desktop Automation")
    print("=" * 50)

    app = LightAgentGUI()
    app.run()


if __name__ == "__main__":
    main()
