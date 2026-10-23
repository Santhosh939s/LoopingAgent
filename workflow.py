"""
LightAgent V1 - Workflow Engine
Loads and executes JSON-defined workflows step by step.
Supports: switch, copy, paste, enter, wait actions.
"""

import json
import os
import time

WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows")


def load_workflow(filename):
    """
    Load a workflow from a JSON file.
    Args:
        filename: Name of the JSON file (looked up in workflows/ directory).
    Returns:
        dict with 'name', 'steps', 'repeat' keys, or None on error.
    """
    # Try as-is first, then in workflows directory
    if os.path.isabs(filename):
        filepath = filename
    else:
        filepath = os.path.join(WORKFLOWS_DIR, filename)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        # Validate required fields
        if "steps" not in workflow:
            print(f"[Workflow] ERROR: No 'steps' in {filepath}")
            return None

        if not workflow["steps"]:
            print(f"[Workflow] ERROR: Empty 'steps' in {filepath}")
            return None

        # Set defaults
        workflow.setdefault("name", "Unnamed Workflow")
        workflow.setdefault("repeat", False)
        workflow.setdefault("description", "")

        return workflow

    except FileNotFoundError:
        print(f"[Workflow] ERROR: File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"[Workflow] ERROR: Invalid JSON in {filepath}: {e}")
        return None


def list_workflows():
    """List all available workflow JSON files."""
    workflows = []
    try:
        for f in os.listdir(WORKFLOWS_DIR):
            if f.endswith(".json"):
                workflows.append(f)
    except FileNotFoundError:
        pass
    return workflows


class WorkflowRunner:
    """Executes workflow steps using window_manager and clipboard_manager."""

    def __init__(self, workflow, window_manager, clipboard_manager, config, logger):
        self.workflow = workflow
        self.wm = window_manager
        self.cm = clipboard_manager
        self.config = config
        self.logger = logger

        self.current_step = 0
        self.loop_count = 0
        self.running = False
        self.paused = False
        self.error = None

        # Status callback for GUI updates
        self.on_status_change = None

    def _set_status(self, status):
        """Notify GUI of status change."""
        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception:
                pass

    def execute_step(self, step):
        """
        Execute a single workflow step.
        Returns True on success, False on failure (should stop).
        """
        action = step.get("action", "").lower()
        desc = step.get("description", action)

        self.logger.log(f"Step: {desc}")
        self._set_status(desc)

        if action == "switch":
            target = step.get("target", "")
            success = self.wm.switch_to(target)
            if not success:
                self.error = f"Window not found: {target}"
                return False
            return True

        elif action == "copy":
            result = self.cm.copy_current()
            if result is None:
                self.error = "Clipboard did not update after copy."
                return False
            return True

        elif action == "paste":
            self.cm.paste_current()
            return True

        elif action == "enter":
            self.cm.press_enter()
            return True

        elif action == "paste_enter":
            # Combined paste + enter
            self.cm.paste_and_enter()
            return True

        elif action == "wait":
            seconds = step.get("seconds", 1)
            self.logger.log(f"Waiting {seconds} seconds...")
            self._set_status(f"Waiting {seconds}s...")

            # Split long waits into short chunks so we can check for stop/pause
            elapsed = 0.0
            chunk = 0.5  # Check every 0.5 seconds
            while elapsed < seconds:
                if not self.running:
                    return False
                while self.paused:
                    time.sleep(0.2)
                    if not self.running:
                        return False
                time.sleep(min(chunk, seconds - elapsed))
                elapsed += chunk

            return True

        elif action == "drag_copy":
            # Drag-select text using calibrated coordinates, then copy
            area_name = step.get("area", "")
            fallback_area = step.get("fallback_area", "")
            area_config = self.config.get(area_name)
            if not area_config and fallback_area:
                area_config = self.config.get(fallback_area)
            if not area_config:
                if "instructor" in area_name or "chatgpt" in area_name:
                    area_config = self.config.get("instructor_area") or self.config.get("chatgpt_area")
                elif "listener" in area_name or "worker" in area_name or "antigravity" in area_name:
                    area_config = self.config.get("listener_area") or self.config.get("worker_area") or self.config.get("antigravity_area")

            if not area_config:
                self.error = f"No coordinates for '{area_name}'. Run: python calibrate.py"
                return False
            result = self.cm.drag_select_and_copy(area_config)
            if result is None:
                self.error = "Clipboard did not update after drag-copy."
                return False
            return True

        elif action == "select_all":
            self.cm.select_all()
            return True

        elif action == "select_all_copy":
            result = self.cm.select_all_and_copy()
            if result is None:
                self.error = "Clipboard did not update after select all + copy."
                return False
            return True

        else:
            self.logger.log(f"WARNING: Unknown action '{action}', skipping.")
            return True

    def run(self):
        """
        Run the complete workflow. Call this from a thread.
        Respects self.running and self.paused flags.
        """
        self.running = True
        self.paused = False
        self.error = None
        self.loop_count = 0

        steps = self.workflow["steps"]
        repeat = self.workflow.get("repeat", False)
        max_loops = self.config.get("max_loops", 0)  # 0 = infinite
        loop_delay = self.config.get("loop_delay", 1.0)

        self.logger.log(f"Workflow started: {self.workflow['name']}")
        self.logger.log(f"Steps: {len(steps)}, Repeat: {repeat}, Max loops: {max_loops if max_loops > 0 else 'infinite'}")
        self._set_status("RUNNING")

        try:
            while self.running:
                self.loop_count += 1
                self.logger.log(f"--- Loop {self.loop_count} ---")

                for i, step in enumerate(steps):
                    # Check if stopped
                    if not self.running:
                        self.logger.log("Workflow stopped by user.")
                        self._set_status("STOPPED")
                        return

                    # Check if paused
                    while self.paused:
                        self._set_status("PAUSED")
                        time.sleep(0.2)
                        if not self.running:
                            self.logger.log("Workflow stopped while paused.")
                            self._set_status("STOPPED")
                            return

                    self.current_step = i

                    # Execute the step
                    success = self.execute_step(step)
                    if not success:
                        if self.error:
                            self.logger.log(f"ERROR: {self.error}")
                        self.logger.log("Workflow stopped due to error.")
                        self._set_status(f"ERROR: {self.error}")
                        self.running = False
                        return

                # Check if we should repeat
                if not repeat:
                    self.logger.log("Workflow completed (no repeat).")
                    self._set_status("COMPLETED")
                    self.running = False
                    return

                # Check max loops
                if max_loops > 0 and self.loop_count >= max_loops:
                    self.logger.log(f"Workflow completed after {max_loops} loops.")
                    self._set_status("COMPLETED")
                    self.running = False
                    return

                # Brief pause between loops
                self.logger.log(f"Loop {self.loop_count} complete. Pausing {loop_delay}s before next loop...")
                time.sleep(loop_delay)

        except Exception as e:
            self.error = str(e)
            self.logger.log(f"UNEXPECTED ERROR: {e}")
            self._set_status(f"ERROR: {e}")
            self.running = False

    def stop(self):
        """Stop the workflow at the next safe point."""
        self.running = False
        self.logger.log("Stop requested.")

    def pause(self):
        """Pause the workflow."""
        self.paused = True
        self.logger.log("Pause requested.")

    def resume(self):
        """Resume the workflow from where it paused."""
        self.paused = False
        self.logger.log("Resume requested.")
