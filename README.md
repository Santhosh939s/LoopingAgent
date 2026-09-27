# LightAgent V1 — LoopingAgent

Extremely lightweight Windows desktop automation agent.

**Core loop:** COPY → SWITCH → PASTE → ENTER → WAIT → REPEAT

## What It Does

LightAgent automates copy-paste workflows between open Windows applications using only keyboard shortcuts and window switching. It **never** opens or launches any application.

## Requirements

- Python 3.7+
- Windows 10/11
- ~20 MB RAM

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent
python main.py
```

## Before Starting

1. Open **Google Chrome** with **ChatGPT** ready
2. Open **Antigravity IDE**
3. Make sure the correct content is selected/ready in the source app
4. Click **START** in the LightAgent GUI

## Controls

| Control | Action |
|---------|--------|
| **START** | Begin the workflow |
| **PAUSE** | Temporarily stop (resume from same step) |
| **STOP** | Stop the workflow |
| **ESC** | Emergency stop (global hotkey) |

## Configuration

Edit `config.json`:

```json
{
    "chatgpt_wait": 10,
    "antigravity_wait": 10,
    "paste_delay": 0.3,
    "copy_delay": 0.5,
    "chrome_title": "Google Chrome",
    "antigravity_title": "Antigravity"
}
```

## Workflows

Workflows are JSON files in the `workflows/` folder. See `antigravity_chatgpt.json` for the default workflow.

## Project Structure

```
LoopingAgent/
  main.py                 — Entry point + Tkinter GUI
  agent.py                — Agent core controller
  window_manager.py       — Window finding/switching
  clipboard_manager.py    — Clipboard operations
  workflow.py             — JSON workflow engine
  config.py               — Config loader
  logger.py               — Lightweight logger
  config.json             — Settings
  requirements.txt        — Dependencies
  workflows/              — Workflow definitions
  logs/                   — Log files (auto-created)
```

## Safety

- Never launches applications
- Never logs clipboard content (only character count)
- Stops on any error
- ESC emergency stop always available
