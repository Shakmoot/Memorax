import os
from dotenv import load_dotenv

# Import the modules your team is building
from core.orchestrator import AIAssistant
from ui.app import start_ui

def main():
    # 1. Load environment variables (API keys)
    print("[SYSTEM] Loading environment variables...")
    load_dotenv()

    # 2. Initialize the AI Brain
    print("[SYSTEM] Initializing AI Assistant...")
    assistant = AIAssistant()

    # 3. Define the Bridge (Callback Function)
    # The UI will call this every time the user hits "Send"
    def handle_user_input(message_text: str) -> str:
        print(f"[DEBUG] User asked: {message_text}")
        
        try:
            # Send text to Member 2's AI module
            ai_response = assistant.get_response(message_text)
            print(f"[DEBUG] AI replied: {ai_response}")
            return ai_response
            
        except Exception as e:
            error_msg = f"Error communicating with AI: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg

    # 4. Start the Application
    print("[SYSTEM] Starting User Interface...")
    # Pass the bridge function to Member 3/4's UI module
    start_ui(on_message_callback=handle_user_input)

if __name__ == "__main__":
    main()