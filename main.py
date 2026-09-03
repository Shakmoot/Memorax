import os
from dotenv import load_dotenv

from core.orchestrator import AIAssistant
from ui.app import start_ui
from glasses.server import GlassesServer

def main():
    print("[SYSTEM] Loading environment variables...")
    load_dotenv()

    print("[SYSTEM] Initializing AI Assistant...")
    assistant = AIAssistant()

    def handle_ui_message(message_text: str) -> str:
        print(f"[DEBUG] User typed: {message_text}")
        try:
            return assistant.get_response(message_text)
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    def handle_glasses_command(command: str):
        if command == "BUTTON_PRESS":
            print("[SYSTEM] Glasses button pressed! Waiting for image...")
            
        elif command == "IMAGE_RECEIVED":
            print("[SYSTEM] Image received from glasses. Sending to AI for analysis...")
            # Route the saved image to the AI Orchestrator
            ai_response = assistant.process_image("latest_capture.jpg")
            print(f"\n>>> AI VISION RESULT: {ai_response} <<<\n")

    print("[SYSTEM] Starting Glasses Network Server...")
    glasses_server = GlassesServer(port=65432, on_command_callback=handle_glasses_command)
    glasses_server.start()

    print("[SYSTEM] Starting User Interface...")
    start_ui(on_message_callback=handle_ui_message)

if __name__ == "__main__":
    main()