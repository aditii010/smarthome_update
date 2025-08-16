from rag_engine import RAGEngine
from llm_interface import query_llm
from scripts.smart_home_api import control_device
from intent_firewall import intent_firewall
import json
import time

# Dummy system state; replace with real sensor or occupancy data if available
def get_current_home_state():
    return {"kids_room_occupied": False}

# Identify if query is informational (uses RAG)
def is_informational(query):
    keywords = [
        "what is", "define", "describe", "how", "how does", "how do i", "how do",
        "what", "where", "when", "why", "explain", "how can", "can you tell", "meaning of"
    ]
    return any(kw in query.lower() for kw in keywords)

# Query LLM with retries and detailed debug for troubleshooting
def query_llm_with_debug(user_input, retries=3, delay=2):
    for attempt in range(retries):
        try:
            print(f"[LLM] Attempt {attempt + 1} querying with input: {user_input}")
            command = query_llm(user_input)
            print(f"[LLM] Raw output: {command}")

            if not command:
                print("[LLM] Warning: Empty or None response.")
            elif isinstance(command, str):
                try:
                    command = json.loads(command)
                    print("[LLM] Successfully parsed JSON string.")
                except Exception as e:
                    print(f"[LLM] String response not JSON parseable: {e}")
            elif isinstance(command, (dict, list)):
                print("[LLM] Response is valid dict/list.")
            else:
                print(f"[LLM] Unexpected type: {type(command)}")

            if command:
                return command

        except Exception as e:
            print(f"[LLM] Exception on attempt {attempt + 1}: {e}")

        print(f"[LLM] Retrying in {delay} seconds...")
        time.sleep(delay)

    raise Exception("LLM call failed after maximum retries")

# Normalize location names from LLM output to system known names
def normalize_location(location):
    mapping = {
        "kids room": "kids_room",
        "children's room": "kids_room",
        "kids_room": "kids_room",
        "bedroom": "bedroom",
        "kitchen": "kitchen",
        "living room": "living_room",
        "living_room": "living_room",
        "front door": "front_door",
        "front_door": "front_door",
        "bathroom": "bathroom",
        "all": "all",
        "current": "living_room",  # Default fallback for 'current'
    }
    return mapping.get(location.lower(), location.lower())

# Normalize device names similarly
def normalize_device(device):
    mapping = {
        "light": "lights",
        "lights": "lights",
        "lock": "lock",
        "locks": "lock",
        "thermostat": "thermostat",
    }
    return mapping.get(device.lower(), device.lower())

def main():
    print("💡 Smart Home CLI with RAG (Type 'exit' to quit)\n")
    engine = RAGEngine()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            print("👋 Goodbye!")
            break

        if is_informational(user_input):
            print("[RAG] Using LangChain to answer informational query...")
            response = engine.query(user_input)
            print("🤖 Assistant:", response)
            continue

        try:
            command = query_llm_with_debug(user_input)
            print("Agent:", json.dumps(command, indent=2))
        except Exception as e:
            print("[ERROR] Failed to parse command:", str(e))
            print("🤖 Assistant:", engine.query(user_input))
            continue

        valid_command_executed = False
        commands = command if isinstance(command, list) else [command]

        for c in commands:
            if not isinstance(c, dict):
                print("Agent: Sorry, I didn't understand that command.")
                continue

            device = c.get("device", "").lower()
            location = c.get("location", "").lower()
            action = c.get("action", "").lower()

            # Skip invalid/hallucinated commands
            if device in ["none", "null", "", "assistant", "user"] or action in ["none", "null", "", "get_question"]:
                continue

            normalized_device = normalize_device(device)
            normalized_location = normalize_location(location)
            if normalized_location == "current":
                normalized_location = "living_room"  # Default fallback

            # Intent firewall safety check
            allowed, message, requires_confirmation = intent_firewall(
                {"device": normalized_device, "location": normalized_location, "action": action},
                system_state=get_current_home_state()
            )
            if not allowed:
                if requires_confirmation:
                    user_confirm = input(f"{message}\nYou: ").strip().lower()
                    if user_confirm not in ["yes", "y"]:
                        print("Action cancelled for your safety.")
                        continue
                    else:
                        print("Confirmed by user. Proceeding...")
                else:
                    print(message)
                    continue

            if all([normalized_device, normalized_location, action]):
                result = control_device(normalized_device, normalized_location, action)
                print("Action:", result)
                valid_command_executed = True
            else:
                print("[ERROR] Incomplete command structure:", c)

        if not valid_command_executed:
            print("[RAG-Fallback] No valid command. Trying to answer with LangChain...")
            print("🤖 Assistant:", engine.query(user_input))


if __name__ == "__main__":
    main()
