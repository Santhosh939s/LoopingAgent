"""Quick integration test for all LightAgent modules."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_config
from logger import AgentLogger
from window_manager import WindowManager
from clipboard_manager import ClipboardManager
from workflow import load_workflow, list_workflows
from agent import LightAgent

def test():
    print("=== LightAgent V1 Module Test ===\n")

    # Test config
    config = load_config()
    print("[OK] Config loaded:", list(config.keys()))

    # Test logger
    logger = AgentLogger()
    logger.log("Test log message")
    print("[OK] Logger, file:", logger.log_file)

    # Test workflow listing
    wfs = list_workflows()
    print("[OK] Workflows found:", wfs)

    # Test workflow loading
    if wfs:
        wf = load_workflow(wfs[0])
        name = wf["name"]
        steps = len(wf["steps"])
        print(f"[OK] Workflow: {name} ({steps} steps)")

    # Test window manager creation
    wm = WindowManager(config, logger)
    chrome_ok, anti_ok = wm.check_windows_exist()
    print(f"[OK] WindowManager created. Chrome={chrome_ok}, Antigravity={anti_ok}")

    # List all windows
    all_wins = wm.list_all_windows()
    print(f"     Visible windows: {len(all_wins)}")

    # Test clipboard manager creation
    cm = ClipboardManager(config, logger)
    print("[OK] ClipboardManager created")

    # Test agent creation
    agent = LightAgent()
    print("[OK] LightAgent created")
    print(f"     Status: {agent.get_status()}")

    # Test prompt parser
    from prompt_parser import parse_prompt, build_workflow_from_prompt
    sample_prompt = "ChatGPT in Chrome is instructor, Antigravity is listener"
    roles = parse_prompt(sample_prompt)
    print(f"[OK] Prompt parsed: Instructor={roles['instructor']}, Listener={roles['listener']}")
    dyn_wf = build_workflow_from_prompt(sample_prompt, config)
    dyn_loaded = agent.set_dynamic_workflow(dyn_wf)
    print(f"[OK] Dynamic workflow loaded: {dyn_loaded} ({len(dyn_wf['steps'])} steps)")

    print("\n=== ALL MODULES OK ===")

if __name__ == "__main__":
    test()
