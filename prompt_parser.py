"""
LightAgent V1 - Prompt Parser & Dynamic Workflow Generator
Parses natural language prompts to configure the automation loop between ANY two windows.
Zero heavy frameworks, 100% lightweight Python.
"""

import re


def parse_prompt(prompt_text, open_windows=None):
    """
    Parse a user prompt to determine the Instructor and Listener/Worker applications.
    
    Examples:
        - "ChatGPT in Chrome is instructor, Antigravity is listener"
        - "Instructor is WhatsApp, Worker is Antigravity"
        - "Copy from WhatsApp and execute in Antigravity"
        - "From Chrome to Notepad"
        - "Instructor: ChatGPT, Listener: Terminal"
    
    Returns:
        dict: {
            "instructor": str,
            "listener": str,
            "raw_prompt": str
        }
    """
    prompt = prompt_text.strip()
    instructor = None
    listener = None

    # Normalization
    clean_text = " " + re.sub(r'[\r\n]+', ' ', prompt) + " "

    # Pattern 1: "instructor is X", "instructor: X", "X is instructor", "X is the instructor"
    # Try "X is (the) instructor" first
    x_inst = re.search(r'([a-zA-Z0-9_\- ]+?)\s+(?:is|acts as)(?:\s+the)?\s+(?:instructor|master|source)', clean_text, re.IGNORECASE)
    if x_inst:
        cand = x_inst.group(1).strip()
        # Clean common leading words
        cand = re.sub(r'^(?:and|so|suppose|mean|for|mean for suppose|if)\s+', '', cand, flags=re.IGNORECASE)
        if cand:
            instructor = cand

    if not instructor:
        inst_match = re.search(r'\b(?:instructor|master|source|from)\s*(?:is|:)?\s*([a-zA-Z0-9_\- ]+?)(?=[,\.]|\band\b|\bto\b|\blistener\b|\bworker\b|\btarget\b|$)', clean_text, re.IGNORECASE)
        if inst_match:
            cand = inst_match.group(1).strip()
            if cand and cand.lower() not in ["the", "a", "an"]:
                instructor = cand

    # Pattern 2: "listener is Y", "Y is listener", "worker is Y", "Y is the listener"
    y_list = re.search(r'([a-zA-Z0-9_\- ]+?)\s+(?:is|acts as)(?:\s+the)?\s+(?:listener|worker|executor)', clean_text, re.IGNORECASE)
    if y_list:
        cand = y_list.group(1).strip()
        cand = re.sub(r'^(?:and|so|then|while)\s+', '', cand, flags=re.IGNORECASE)
        if cand:
            listener = cand

    if not listener:
        list_match = re.search(r'\b(?:listener|worker|executor|destination|target|to)\s*(?:is|:)?\s*([a-zA-Z0-9_\- ]+?)(?=[,\.]|\band\b|\bfrom\b|\binstructor\b|\bmaster\b|\breturn\b|\breport\b|$)', clean_text, re.IGNORECASE)
        if list_match:
            cand = list_match.group(1).strip()
            if cand and cand.lower() not in ["the", "a", "an"]:
                listener = cand

    # Pattern 3: "from X to Y"
    if not (instructor and listener):
        from_to_match = re.search(r'\bfrom\s+([a-zA-Z0-9_\- ]+?)\s+to\s+([a-zA-Z0-9_\- ]+?)(?=[,\.]|\band\b|\bthen\b|$)', clean_text, re.IGNORECASE)
        if from_to_match:
            instructor = instructor or from_to_match.group(1).strip()
            listener = listener or from_to_match.group(2).strip()

    # Pattern 4: "X ... Y" matching known open windows or common apps
    known_apps = [
        "Chrome", "ChatGPT", "Antigravity", "WhatsApp", "Code", "Visual Studio Code",
        "Notepad", "Terminal", "PowerShell", "Edge", "Firefox", "Discord", "Slack"
    ]
    if open_windows:
        # Augment with titles of active windows
        for w in open_windows:
            w_short = w.split(" - ")[-1].strip()
            if w_short and w_short not in known_apps:
                known_apps.append(w_short)

    found_apps = []
    for app in known_apps:
        idx = clean_text.lower().find(app.lower())
        if idx != -1:
            found_apps.append((idx, app))
    
    # Sort by order of appearance in the prompt
    found_apps.sort(key=lambda x: x[0])

    if not instructor and len(found_apps) >= 1:
        instructor = found_apps[0][1]
    if not listener and len(found_apps) >= 2:
        listener = found_apps[1][1]

    # Clean up names (e.g. "ChatGPT in Chrome" -> "Chrome")
    def clean_name(name):
        if not name:
            return name
        name_lower = name.lower()
        if "chrome" in name_lower or "chatgpt" in name_lower:
            return "Chrome"
        if "antigravity" in name_lower:
            return "Antigravity"
        if "whatsapp" in name_lower:
            return "WhatsApp"
        if "notepad" in name_lower:
            return "Notepad"
        if "code" in name_lower or "vs code" in name_lower:
            return "Visual Studio Code"
        return name.strip()

    instructor = clean_name(instructor) or "Chrome"
    listener = clean_name(listener) or "Antigravity"

    return {
        "instructor": instructor,
        "listener": listener,
        "raw_prompt": prompt,
    }


def build_workflow_from_prompt(prompt_text, config=None, open_windows=None):
    """
    Generate a complete executable workflow dictionary from a natural language prompt.
    """
    config = config or {}
    roles = parse_prompt(prompt_text, open_windows)
    inst = roles["instructor"]
    listener = roles["listener"]

    instructor_wait = config.get("chatgpt_wait", 10)
    listener_wait = config.get("antigravity_wait", 10)

    workflow = {
        "name": f"{inst} <-> {listener} Loop",
        "description": f"Prompt-driven loop: {inst} (Instructor) instructs {listener} (Listener/Worker).",
        "repeat": True,
        "roles": roles,
        "steps": [
            {
                "action": "switch",
                "target": inst,
                "description": f"Focus {inst} (Instructor)"
            },
            {
                "action": "drag_copy",
                "area": "instructor_area",
                "fallback_area": "chatgpt_area",
                "description": f"Copy instructions from {inst}"
            },
            {
                "action": "wait",
                "seconds": 0.5,
                "description": "Wait for clipboard"
            },
            {
                "action": "switch",
                "target": listener,
                "description": f"Focus {listener} (Worker)"
            },
            {
                "action": "paste",
                "description": f"Paste instructions into {listener}"
            },
            {
                "action": "enter",
                "description": f"Execute in {listener}"
            },
            {
                "action": "wait",
                "seconds": listener_wait,
                "description": f"Wait for {listener} to complete"
            },
            {
                "action": "drag_copy",
                "area": "listener_area",
                "fallback_area": "antigravity_area",
                "description": f"Copy result from {listener}"
            },
            {
                "action": "wait",
                "seconds": 0.5,
                "description": "Wait for clipboard"
            },
            {
                "action": "switch",
                "target": inst,
                "description": f"Focus {inst} (Instructor)"
            },
            {
                "action": "paste",
                "description": f"Paste result back to {inst}"
            },
            {
                "action": "enter",
                "description": f"Send result to {inst}"
            },
            {
                "action": "wait",
                "seconds": instructor_wait,
                "description": f"Wait for {inst} next response"
            }
        ]
    }

    return workflow
