import os
from dotenv import load_dotenv

from core.orchestrator import AIAssistant
from ui.app import start_ui
from glasses.server import GlassesServer  # NEW IMPORT

def main():
    print("[SYSTEM] Loading environment variables...")
    load_dotenv()

    print("[SYSTEM] Initializing AI Assistant...")
    assistant = AIAssistant()

    # Callback 1: Handle text typed into the UI
    def handle_ui_message(message_text: str) -> str:
        print(f"[DEBUG] User typed: {message_text}")
        try:
            return assistant.get_response(message_text)
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    # Callback 2: Handle data arriving over Wi-Fi from the glasses
    def handle_glasses_command(command: str):
        print(f"[SYSTEM] The glasses hardware sent a command: {command}")
        if command == "BUTTON_PRESS":
            print("[SYSTEM] Triggering AI Vision or Voice routine...")
            # Later, we will trigger the AI when the button is pressed.

    # Start the background Network Server
    print("[SYSTEM] Starting Glasses Network Server...")
    glasses_server = GlassesServer(port=65432, on_command_callback=handle_glasses_command)
    glasses_server.start()

    # Start the UI (This runs on the main thread and keeps the app alive)
    print("[SYSTEM] Starting User Interface...")
    start_ui(on_message_callback=handle_ui_message)

if __name__ == "__main__":
    main()