import os
from dotenv import load_dotenv

from core.orchestrator import AIAssistant
from ui.app import start_ui
from glasses.server import GlassesServer
from core.audio_service import AudioService  # NEW: Import the Audio Service

def main():
    print("[SYSTEM] Loading environment variables...")
    load_dotenv()

    print("[SYSTEM] Initializing AI Assistant...")
    assistant = AIAssistant()
    
    # NEW: Initialize the Audio Service
    print("[SYSTEM] Initializing Audio Service...")
    audio = AudioService()

    def handle_ui_message(message_text: str) -> str:
        print(f"[DEBUG] User typed: {message_text}")
        try:
            return assistant.ask_question(message_text)
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    def handle_glasses_command(command: str):
        if command == "BUTTON_PRESS":
            print("[SYSTEM] Glasses button pressed! Waking up Voice Assistant...")
            audio.speak("Yes?")
            
            # Start a continuous conversation loop
            conversation_active = True
            
            while conversation_active:
                # 1. Listen to the user
                user_speech = audio.listen()
                
                # 2. If the user said nothing, end the conversation
                if not user_speech:
                    print("[SYSTEM] No speech detected. Going back to sleep.")
                    audio.speak("Going to sleep.")
                    conversation_active = False
                    continue
                
                # 3. If the user says goodbye, end the conversation
                if "goodbye" in user_speech.lower() or "stop" in user_speech.lower():
                    print("[SYSTEM] User ended conversation.")
                    audio.speak("Goodbye.")
                    conversation_active = False
                    continue

                # 4. Otherwise, send it to the AI and speak the response
                ai_response = assistant.ask_question(user_speech)
                print(f"\n>>> AI RESPONSE: {ai_response} <<<\n")
                audio.speak(ai_response)
                
                # The loop will now immediately go back to step 1 and listen again!

    print("[SYSTEM] Starting Glasses Network Server...")
    glasses_server = GlassesServer(port=65432, on_command_callback=handle_glasses_command)
    glasses_server.start()

    print("[SYSTEM] Starting User Interface...")
    start_ui(on_message_callback=handle_ui_message)

if __name__ == "__main__":
    main()