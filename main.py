# main.py
import time
from llm_interface import query_llm
from rag_engine import RAGEngine
from intent_firewall import intent_firewall
from state_manager import StateManager

def main():
    print("💡 Smart Home CLI with RAG + Intent Firewall (Type 'exit' to quit)")

    rag = RAGEngine(kb_path="knowledge/knowledge.txt")
    state = StateManager(context_file="data/context_summary.json")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        # Try to parse as structured device control
        commands = None
        for attempt in range(1, 4):
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
                raw_text=user_input  # NEW: pass original input for extra safety
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

            # If allowed, execute (here we just simulate)
            device = cmd.get("device", "unknown")
            location = cmd.get("location", "unknown")
            action = cmd.get("action", "unknown")

            # Simulate updating state
            state.update_state(device, location, action)
            print(f"✅ Executed: {action} {location} {device}")

if __name__ == "__main__":
    main()
