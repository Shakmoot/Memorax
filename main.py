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
            # FIXED: We now use Member 2's 'ask_question' method
            return assistant.ask_question(message_text)
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    def handle_glasses_command(command: str):
        if command == "BUTTON_PRESS":
            print("[SYSTEM] Glasses button pressed! Waiting for image...")
            
        elif command == "IMAGE_RECEIVED":
            print("[SYSTEM] Image received from glasses. Sending to AI for analysis...")
            
            # FIXED: We pass the image to 'ask_question' along with a system prompt
            ai_response = assistant.ask_question(
                user_text="Describe what you see in this image in one brief sentence.", 
                image_path="latest_capture.jpg"
            )
            print(f"\n>>> AI VISION RESULT: {ai_response} <<<\n")

    print("[SYSTEM] Starting Glasses Network Server...")
    glasses_server = GlassesServer(port=65432, on_command_callback=handle_glasses_command)
    glasses_server.start()

    print("[SYSTEM] Starting User Interface...")
    start_ui(on_message_callback=handle_ui_message)

if __name__ == "__main__":
    main()