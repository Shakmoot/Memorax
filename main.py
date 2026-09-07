import os
from dotenv import load_dotenv

from core.orchestrator import AIAssistant
from ui.app import start_ui
from glasses.server import GlassesServer
from core.audio_service import AudioService

def main():
    print("[SYSTEM] Loading environment variables...")
    load_dotenv()

    print("[SYSTEM] Initializing AI Assistant...")
    assistant = AIAssistant()

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
            # NEW: Interruption Logic
            if audio.is_speaking:
                print("[SYSTEM] Interrupting AI speech...")
                audio.interrupt()
                return # Stop executing here; the existing background loop will automatically drop down to listen()!
                
            # NEW: Prevent duplicate loops if user spams the button while it's already listening
            if audio.is_listening:
                print("[SYSTEM] Already listening for your voice...")
                return

            print("[SYSTEM] Glasses button pressed! Waking up Voice Assistant...")
            audio.speak("Yes?")
            
            conversation_active = True
            
            while conversation_active:
                user_speech = audio.listen()
                
                if not user_speech:
                    print("[SYSTEM] No speech detected. Going back to sleep.")
                    audio.speak("Going to sleep.")
                    conversation_active = False
                    continue
                
                if "goodbye" in user_speech.lower() or "stop" in user_speech.lower():
                    print("[SYSTEM] User ended conversation.")
                    audio.speak("Goodbye.")
                    conversation_active = False
                    continue

                ai_response = assistant.ask_question(user_speech)
                print(f"\n>>> AI RESPONSE: {ai_response} <<<\n")
                audio.speak(ai_response)
                
        elif command == "IMAGE_RECEIVED":
            print("[SYSTEM] Image received from glasses. Sending to AI for analysis...")
            audio.speak("Analyzing image...")
            
            ai_response = assistant.ask_question(
                user_text="Describe what you see in this image in one brief sentence.", 
                image_path="latest_capture.jpg"
            )
            print(f"\n>>> AI VISION RESULT: {ai_response} <<<\n")
            audio.speak(ai_response)

        elif command == "START_MEETING":
            print("[SYSTEM] Glasses requested meeting start.")
            audio.speak("Starting meeting recording.")
            audio.start_meeting_recording()

        elif command == "STOP_MEETING":
            print("[SYSTEM] Glasses requested meeting stop.")
            audio.speak("Stopping meeting recording. Please wait while I analyze the audio.")
            audio_file_path = audio.stop_meeting_recording()
            
            if audio_file_path:
                print(f"[SYSTEM] Sending {audio_file_path} to Gemini for summarization!")
                
                # We command the AI to summarize AND use the database tool!
                prompt = (
                    "Please listen to this meeting recording and write a brief, bulleted summary of the key points. "
                    "Then, you MUST use the 'save_memory' tool to save this summary to the database."
                )
                
                ai_response = assistant.ask_question(user_text=prompt, audio_path=audio_file_path)
                print(f"\n>>> MEETING SUMMARY: {ai_response} <<<\n")
                audio.speak("Meeting summarized and saved to memory.")

    print("[SYSTEM] Starting Glasses Network Server...")
    glasses_server = GlassesServer(port=65432, on_command_callback=handle_glasses_command)
    glasses_server.start()

    print("[SYSTEM] Starting User Interface...")
    # This blocks the main thread and runs the UI window
    start_ui(on_message_callback=handle_ui_message)

if __name__ == "__main__":
    main()