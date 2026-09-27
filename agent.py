"""
LightAgent V1 - Agent Core
Ties together window_manager, clipboard_manager, workflow engine.
The main controller that the GUI talks to.
"""

import threading

from config import load_config
from logger import AgentLogger
from window_manager import WindowManager
from clipboard_manager import ClipboardManager
from workflow import WorkflowRunner, load_workflow


class LightAgent:
    """Core agent that manages the automation workflow."""

    def __init__(self, gui_log_callback=None):
        # Load config
        self.config = load_config()

        # Create logger
        self.logger = AgentLogger(gui_callback=gui_log_callback)

        # Create managers
        self.wm = WindowManager(self.config, self.logger)
        self.cm = ClipboardManager(self.config, self.logger)

        # Workflow runner (created when a workflow is loaded)
        self.runner = None
        self.worker_thread = None

        # Status callback for GUI
        self.on_status_change = None

    def load_workflow(self, workflow_file):
        """Load a workflow from file."""
        workflow = load_workflow(workflow_file)
        if workflow is None:
            self.logger.log(f"Failed to load workflow: {workflow_file}")
            return False

        self.logger.log(f"Loaded workflow: {workflow['name']}")
        self.runner = WorkflowRunner(
            workflow=workflow,
            window_manager=self.wm,
            clipboard_manager=self.cm,
            config=self.config,
            logger=self.logger,
        )

        # Wire up status callback
        if self.on_status_change:
            self.runner.on_status_change = self.on_status_change

        return True

    def preflight_check(self):
        """
        Check that required windows are open before starting.
        Returns (ok, message) tuple.
        """
        chrome_found, antigravity_found = self.wm.check_windows_exist()

        issues = []
        if not chrome_found:
            issues.append(f"Chrome window not found. (Looking for: '{self.config['chrome_title']}')")
        if not antigravity_found:
            issues.append(f"Antigravity window not found. (Looking for: '{self.config['antigravity_title']}')")

        if issues:
            msg = "\n".join(issues)
            self.logger.log(f"Preflight FAILED:\n{msg}")
            return False, msg

        self.logger.log("Preflight OK: Both windows found.")
        return True, "All windows found."

    def start(self):
        """Start running the loaded workflow in a background thread."""
        if self.runner is None:
            self.logger.log("ERROR: No workflow loaded.")
            return False

        if self.worker_thread and self.worker_thread.is_alive():
            self.logger.log("Workflow is already running.")
            return False

        # Preflight check
        ok, msg = self.preflight_check()
        if not ok:
            if self.on_status_change:
                self.on_status_change(f"ERROR: {msg}")
            return False

        # Run in background thread so GUI doesn't freeze
        self.worker_thread = threading.Thread(target=self.runner.run, daemon=True)
        self.worker_thread.start()

        self.logger.log("Workflow thread started.")
        return True

    def stop(self):
        """Stop the workflow."""
        if self.runner:
            self.runner.stop()
        self.logger.log("Agent stopped.")

    def pause(self):
        """Pause the workflow."""
        if self.runner:
            self.runner.pause()

    def resume(self):
        """Resume the workflow."""
        if self.runner:
            self.runner.resume()

    @property
    def is_running(self):
        return self.runner is not None and self.runner.running

    @property
    def is_paused(self):
        return self.runner is not None and self.runner.paused

    def get_status(self):
        """Get current agent status string."""
        if self.runner is None:
            return "NO WORKFLOW"
        if self.runner.error:
            return f"ERROR: {self.runner.error}"
        if self.runner.paused:
            return "PAUSED"
        if self.runner.running:
            return "RUNNING"
        return "READY"
