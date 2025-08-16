#llm_interface.py

import subprocess
import json
import re

def normalize_command(cmd):
    if isinstance(cmd, dict):
        device = cmd.get("device", "").lower().replace(" ", "_")
        location = cmd.get("location", "").lower().replace(" ", "_")

        # Normalize device
        if device in ["all_lights", "lights", "lightbulbs", "lamps"]:
            cmd["device"] = "light"
        else:
            cmd["device"] = device.replace("_", " ")

        # Normalize location
        if location in ["all_rooms", "entire_house", "whole_home", "all"]:
            cmd["location"] = "all"
        else:
            cmd["location"] = location.replace("_", " ")

        # ✅ Default location fallback
        if not cmd.get("location") or cmd["location"].strip() == "" or cmd["location"].lower() == "unknown":
            cmd["location"] = "all"

    return cmd

def safe_parse_multiple_json(raw_output):
    """Try parsing multiple JSON objects from LLM output."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_output.strip(), flags=re.MULTILINE)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return [normalize_command(parsed)]
        elif isinstance(parsed, list):
            return [normalize_command(p) for p in parsed]
    except json.JSONDecodeError:
        pass

    objects = []
    for match in re.finditer(r"{.*?}", cleaned, flags=re.DOTALL):
        try:
            obj = json.loads(match.group())
            objects.append(normalize_command(obj))
        except json.JSONDecodeError:
            continue

    return objects if objects else None

def query_llm(user_input):
    system_prompt = """
You are a smart home assistant. Your job is to understand the user's natural language commands and convert them into a structured JSON format.

If the user is asking a general question that is NOT a command, such as "What can I control?", "What are the safety rules?", or is simply greeting you, you MUST return an empty JSON array: [].

Only use the following actions:
- turn_on
- turn_off
- get_status
- dim
- set_temperature
- lock
- unlock
- open
- close

Output format must always be valid JSON. If there are multiple actions, return them as a single JSON array containing multiple JSON objects.

Each object must include:
- device
- location
- action

Example:
User: dim the bedroom light and turn on the kitchen light
Output:
[
  {
    "device": "light",
    "location": "bedroom",
    "action": "dim"
  },
  {
    "device": "light",
    "location": "kitchen",
    "action": "turn_on"
  }
]

Now, parse the following user input and respond ONLY with JSON objects as a single JSON array, with no additional text or explanation.
"""

    full_prompt = system_prompt.strip() + "\nUser command: " + user_input.strip()

    try:
        print(f"[LLM] Prompting Ollama with: {user_input}")
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=full_prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        if result.returncode != 0:
            print(f"[ERROR] Ollama stderr: {result.stderr.decode()}")
            return None

        raw_output = result.stdout.decode().strip()
        commands = safe_parse_multiple_json(raw_output)
        
        # The change in the prompt will cause safe_parse_multiple_json to return an empty list `[]` for non-commands
        # instead of `None`. The main script's logic will then handle this gracefully.
        return commands

    except subprocess.TimeoutExpired:
        print("[ERROR] Ollama call timed out.")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None
