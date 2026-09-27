"""
LightAgent V1 - Configuration Loader
Loads settings from config.json. Extremely lightweight.
"""

import json
import os

# Path to config.json (same directory as this file)
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# Default values in case config.json is missing keys
DEFAULTS = {
    "chatgpt_wait": 10,
    "antigravity_wait": 10,
    "paste_delay": 0.3,
    "copy_delay": 0.5,
    "enter_after_paste": True,
    "chrome_title": "Google Chrome",
    "antigravity_title": "Antigravity",
    "clipboard_timeout": 5,
    "max_loops": 0,
    "loop_delay": 1.0,
}


def load_config():
    """Load configuration from config.json, falling back to defaults."""
    config = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        config.update(user_config)
    except FileNotFoundError:
        print(f"[Config] config.json not found at {CONFIG_PATH}, using defaults.")
    except json.JSONDecodeError as e:
        print(f"[Config] Error parsing config.json: {e}. Using defaults.")
    return config


def save_config(config):
    """Save configuration back to config.json."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"[Config] Error saving config.json: {e}")
