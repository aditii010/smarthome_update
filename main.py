# main.py
import time
from llm_interface import query_llm
from rag_engine import RAGEngine
from intent_firewall import intent_firewall
from state_manager import StateManager
from smart_home_api import list_devices, control_device
#from audio_interface import listen_for_command, speak_response #dont use it now, its for audio

def main():
    print("💡 Smart Home CLI with RAG + Intent Firewall (Type 'exit' to quit)")

    rag = RAGEngine(kb_path="knowledge.txt")
    state = StateManager(context_file="data/context_summary.json")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        # --- Built-in queries ---
        if user_input.lower() in ["list devices", "what can i control", "show devices", "what devices can i control", "what are the devices available to me"]:
            devices = list_devices()
            print("📋 Devices you can control:")
            for d in devices:
                print(f"- {d}")
            continue

        if user_input.lower() in ["status of all devices", "show status", "device status", "status"]:
            responses = control_device("*", "*", "get_status")
            print("📊 Current device status:")
            print(responses)
            continue
        # ------------------------

        # Try to parse as structured device control
        commands = None
        for attempt in range(1, 3):
            print(f"[LLM] Attempt {attempt} querying with input: {user_input}")
            commands = query_llm(user_input)
            print(f"[LLM] Parsed commands: {commands}")
            if commands:
                break
            else:
                print(f"[LLM] Retrying in 2 seconds...")
                time.sleep(2)

        if not commands:
            # Fallback to RAG if no commands parsed
            answer = rag.query(user_input)
            print(f"Agent: {answer}")
            continue

        # Process each structured command
        for cmd in commands:
            allowed, message, needs_confirmation = intent_firewall(
                cmd,
                system_state=state.get_state(),
                raw_text=user_input
            )

            if not allowed and needs_confirmation:
                print(f"⚠️  Confirmation required: {message}")
                confirm = input("Confirm (yes/no): ").strip().lower()
                if confirm != "yes":
                    print("❌ Action canceled.")
                    continue
                else:
                    print("✅ Confirmation received, executing command.")

            elif not allowed:
                print(f"🚫 Action blocked: {message}")
                continue

            # --- Normalize brightness/fan-related actions ---
            if cmd.get("action") in ["dim", "set_brightness", "set_temperature"]:
                cmd["action"] = "dim"  
                cmd["value"] = cmd.get("brightness") or cmd.get("level") or cmd.get("percentage") or cmd.get("value") or 40

            if cmd.get("action") in ["turn_on", "on", "turn_off", "off"] and cmd.get("device") in ["fan", "fans"]:
                cmd["device"] = "fan"

            # Execute using smart_home_api
            device = cmd.get("device")
            location = cmd.get("location")
            action = cmd.get("action")
            value = cmd.get("value")  # <-- pass the mapped value

            result = control_device(device, location, action, value)
            state.update_state(device or "unknown", location or "unknown", action or "unknown")

            # Human-readable output for status commands
            if action in ["get_status", "check_status", "status_check", ""]:
                print(f"📊 Device status:\n{result}")
            else:
                print(f"✅ Action executed:\n{result}")

if __name__ == "__main__":
    main()
